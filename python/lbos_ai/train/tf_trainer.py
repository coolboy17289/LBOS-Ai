"""
TensorFlow trainer for LBOS-AI
Alternative implementation using TensorFlow/Keras for production deployment
"""
import os
import yaml
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, losses, metrics
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import numpy as np
from tqdm import tqdm

# Configure logging
logger = logging.getLogger(__name__)

class TFTextProcessor:
    def __init__(self, vocab_size: int = 30522, max_length: int = 512):
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.tokenizer = None

    def build_tokenizer(self, texts: List[str]):
        """Build a simple word-piece tokenizer (in practice, use saved tokenizer)"""
        # For simplicity, we'll use Tokenizer from keras.preprocessing.text
        # In production, you'd load a pre-trained tokenizer
        from tensorflow.keras.preprocessing.text import Tokenizer

        self.tokenizer = Tokenizer(
            num_words=self.vocab_size,
            oov_token="<UNK>",
            filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'
        )
        self.tokenizer.fit_on_texts(texts)
        return self.tokenizer

    def texts_to_sequences(self, texts: List[str]) -> np.ndarray:
        """Convert texts to padded sequences"""
        if self.tokenizer is None:
            raise ValueError("Tokenizer not built. Call build_tokenizer first.")

        sequences = self.tokenizer.texts_to_sequences(texts)
        padded = tf.keras.preprocessing.sequence.pad_sequences(
            sequences,
            maxlen=self.max_length,
            padding='post',
            truncating='post'
        )
        return padded

class TFTransformerLayer(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super().__init__()
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = models.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, training):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

class TFTransformerLM(models.Model):
    def __init__(self, vocab_size, maxlen, embed_dim=256, num_heads=4, ff_dim=512, num_layers=4):
        super().__init__()
        self.embed_dim = embed_dim
        self.maxlen = maxlen
        self.vocab_size = vocab_size

        self.embedding_layer = layers.Embedding(vocab_size, embed_dim, input_length=maxlen)
        self.pos_embedding_layer = layers.Embedding(maxlen, embed_dim)

        self.transformer_layers = [
            TFTransformerLayer(embed_dim, num_heads, ff_dim) for _ in range(num_layers)
        ]

        self.dropout = layers.Dropout(0.1)
        self.dense = layers.Dense(vocab_size)

    def call(self, inputs, training=False):
        # Create positions
        positions = tf.range(start=0, limit=self.maxlen, delta=1)
        positions = self.pos_embedding_layer(positions)

        # Embed tokens
        x = self.embedding_layer(inputs)
        x += positions

        # Apply transformer layers
        for layer in self.transformer_layers:
            x = layer(x, training=training)

        # Final layer
        x = self.dropout(x, training=training)
        return self.dense(x)

class TFTrainer:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize trainer with configuration

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.model = None
        self.tokenizer = None
        self.history = None

        # Setup directories
        self.output_dir = Path(self.config.get('output_dir', './models'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path(self.config.get('log_dir', './logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        default_config = {
            'model': {
                'vocab_size': 30522,
                'max_length': 512,
                'embed_dim': 256,
                'num_heads': 4,
                'ff_dim': 512,
                'num_layers': 4
            },
            'training': {
                'batch_size': 32,
                'learning_rate': 0.001,
                'epochs': 10,
                'validation_split': 0.1
            },
            'output_dir': './models',
            'log_dir': './logs'
        }

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                for key in user_config:
                    if key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(user_config[key])
                    else:
                        default_config[key] = user_config[key]

        return default_config

    def prepare_data(self, texts: List[str]):
        """
        Prepare training data

        Args:
            texts: List of text samples
        """
        # Initialize and build tokenizer
        self.tokenizer = TFTextProcessor(
            vocab_size=self.config['model']['vocab_size'],
            max_length=self.config['model']['max_length']
        )
        self.tokenizer.build_tokenizer(texts)

        # Convert text to sequences
        sequences = self.tokenizer.texts_to_sequences(texts)

        # For language modeling, we need to predict next token
        # Input: all tokens except last
        # Output: all tokens except first
        X = sequences[:, :-1]
        y = sequences[:, 1:]

        # Convert to categorical
        y = tf.keras.utils.to_categorical(y, num_classes=self.config['model']['vocab_size'])

        # Split data
        split_idx = int(len(X) * (1 - self.config['training']['validation_split']))
        self.X_train, self.X_val = X[:split_idx], X[split_idx:]
        self.y_train, self.y_val = y[:split_idx], y[split_idx:]

        logger.info(f"Prepared {len(self.X_train)} training samples and {len(self.X_val)} validation samples")

    def build_model(self):
        """Build the TensorFlow/Keras model"""
        model_config = self.config['model']
        self.model = TFTransformerLM(
            vocab_size=model_config['vocab_size'],
            maxlen=model_config['max_length'],
            embed_dim=model_config['embed_dim'],
            num_heads=model_config['num_heads'],
            ff_dim=model_config['ff_dim'],
            num_layers=model_config['num_layers']
        )

        # Compile model
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config['training']['learning_rate']),
            loss=losses.CategoricalCrossentropy(from_logits=True),
            metrics=[metrics.CategoricalAccuracy()]
        )

        logger.info(f"Built TF model with {self.model.count_params()} parameters")

    def train(self):
        """Train the model"""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        if not hasattr(self, 'X_train'):
            raise ValueError("Data not prepared. Call prepare_data() first.")

        # Callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=3,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ModelCheckpoint(
                filepath=str(self.output_dir / 'tf_model_{epoch:02d}-{val_loss:.2f}.h5'),
                save_best_only=True,
                monitor='val_loss'
            ),
            tf.keras.callbacks.TensorBoard(
                log_dir=str(self.log_dir),
                histogram_freq=1
            )
        ]

        # Train
        self.history = self.model.fit(
            self.x_train, self.y_train,
            batch_size=self.config['training']['batch_size'],
            epochs=self.config['training']['epochs'],
            validation_data=(self.x_val, self.y_val),
            callbacks=callbacks
        )

        logger.info("Training completed!")
        return self.history

    def save_model(self, model_name: str = "tf_model"):
        """Save the trained model"""
        if self.model is None:
            raise ValueError("No model to save.")

        model_path = self.output_dir / model_name
        model_path.mkdir(parents=True, exist_ok=True)

        # Save TensorFlow model
        self.model.save(model_path / "model.h5")

        # Save tokenizer (simplified)
        import pickle
        with open(model_path / "tokenizer.pkl", "wb") as f:
            pickle.dump(self.tokenizer.tokenizer, f)

        # Save config
        import yaml
        with open(model_path / "config.yaml", "w") as f:
            yaml.dump(self.config, f)

        logger.info(f"Model saved to {model_path}")

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tf_trainer.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Dummy data for testing
    texts = [
        "This is a sample text for testing the trainer.",
        "Another example sentence to demonstrate functionality.",
        "Machine learning is fascinating and complex.",
        "Natural language processing enables computers to understand human language."
    ] * 100  # Repeat to have enough data

    # Initialize trainer
    trainer = TFTrainer(config_file)

    # Prepare data
    trainer.prepare_data(texts)

    # Build model
    trainer.build_model()

    # Train
    trainer.train()

    # Save model
    trainer.save_model()