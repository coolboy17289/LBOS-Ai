"""
Model training module for LBOS-AI
Handles training of custom transformer models from scratch
"""
import os
import yaml
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import PreTrainedTokenizerFast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import math
from tqdm import tqdm

# Import our model
from .model import TransformerLM

# Configure logging
logger = logging.getLogger(__name__)

class TextDataset(Dataset):
    def __init__(self, texts: List[str], tokenizer: PreTrainedTokenizerFast, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []

        # Tokenize texts
        for text in texts:
            if not text or len(text.strip()) < 10:
                continue

            # Add special tokens and truncate
            encoding = tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                padding='max_length',
                return_tensors='pt'
            )

            self.examples.append({
                'input_ids': encoding['input_ids'].squeeze(),
                'attention_mask': encoding['attention_mask'].squeeze(),
                'labels': encoding['input_ids'].squeeze().clone()  # For language modeling
            })

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

class Trainer:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize trainer with configuration

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.device = self._get_device()
        self.model = None
        self.tokenizer = None
        self.optimizer = None
        self.scheduler = None
        self.train_loader = None
        self.val_loader = None

        # Training state
        self.epoch = 0
        self.global_step = 0
        self.best_loss = float('inf')

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
                'hidden_size': 768,
                'num_hidden_layers': 6,
                'num_attention_heads': 12,
                'intermediate_size': 3072,
                'hidden_act': 'gelu',
                'hidden_dropout_prob': 0.1,
                'attention_probs_dropout_prob': 0.1,
                'max_position_embeddings': 512,
                'type_vocab_size': 2,
                'initializer_range': 0.02
            },
            'training': {
                'batch_size': 16,
                'learning_rate': 5e-5,
                'weight_decay': 0.01,
                'adam_epsilon': 1e-8,
                'max_grad_norm': 1.0,
                'num_train_epochs': 3,
                'warmup_steps': 500,
                'logging_steps': 50,
                'save_steps': 1000,
                'eval_steps': 500,
                'fp16': False,
                'gradient_accumulation_steps': 1
            },
            'data': {
                'max_seq_length': 512,
                'train_split': 0.9
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

    def _get_device(self) -> torch.device:
        """Get appropriate device for training"""
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for training")
        return device

    def prepare_data(self, texts: List[str], tokenizer: PreTrainedTokenizerFast):
        """
        Prepare training and validation data

        Args:
            texts: List of text samples
            tokenizer: Tokenizer to use
        """
        self.tokenizer = tokenizer

        # Split data
        split_idx = int(len(texts) * self.config['data']['train_split'])
        train_texts = texts[:split_idx]
        val_texts = texts[split_idx:] if len(texts) > split_idx else []

        # Create datasets
        train_dataset = TextDataset(
            train_texts,
            tokenizer,
            self.config['data']['max_seq_length']
        )
        val_dataset = TextDataset(
            val_texts,
            tokenizer,
            self.config['data']['max_seq_length']
        ) if val_texts else None

        # Create data loaders
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=True,
            num_workers=2,
            pin_memory=True
        )

        if val_dataset:
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=self.config['training']['batch_size'],
                shuffle=False,
                num_workers=2,
                pin_memory=True
            )

        logger.info(f"Prepared {len(train_dataset)} training samples and {len(val_dataset) if val_dataset else 0} validation samples")

    def initialize_model(self):
        """Initialize the model with configuration"""
        model_config = self.config['model']
        self.model = TransformerLM(
            vocab_size=model_config['vocab_size'],
            hidden_size=model_config['hidden_size'],
            num_hidden_layers=model_config['num_hidden_layers'],
            num_attention_heads=model_config['num_attention_heads'],
            intermediate_size=model_config['intermediate_size'],
            hidden_act=model_config['hidden_act'],
            hidden_dropout_prob=model_config['hidden_dropout_prob'],
            attention_probs_dropout_prob=model_config['attention_probs_dropout_prob'],
            max_position_embeddings=model_config['max_position_embeddings'],
            type_vocab_size=model_config['type_vocab_size'],
            initializer_range=model_config['initializer_range']
        )

        self.model.to(self.device)
        logger.info(f"Initialized model with {sum(p.numel() for p in self.model.parameters())} parameters")

    def setup_optimizer_and_scheduler(self):
        """Setup optimizer and learning rate scheduler"""
        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config['training']['learning_rate'],
            weight_decay=self.config['training']['weight_decay'],
            eps=self.config['training']['adam_epsilon']
        )

        # Calculate total steps
        total_steps = len(self.train_loader) * self.config['training']['num_train_epochs']
        warmup_steps = self.config['training']['warmup_steps']

        # Scheduler
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

        logger.info(f"Optimizer and scheduler configured. Total steps: {total_steps}, Warmup: {warmup_steps}")

    def train(self):
        """Main training loop"""
        if not self.model:
            raise ValueError("Model not initialized. Call initialize_model() first.")

        if not self.train_loader:
            raise ValueError("Training data not prepared. Call prepare_data() first.")

        self.model.train()
        total_loss = 0.0
        best_val_loss = float('inf')

        for epoch in range(self.config['training']['num_train_epochs']):
            self.epoch = epoch
            epoch_loss = 0.0
            num_batches = 0

            progress_bar = tqdm(self.train_loader, desc=f"Epoch {epoch+1}/{self.config['training']['num_train_epochs']}")

            for batch in progress_bar:
                # Move batch to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                loss = outputs['loss']

                # Backward pass
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config['training']['max_grad_norm']
                )

                # Optimizer step
                self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad()

                # Update metrics
                total_loss += loss.item()
                epoch_loss += loss.item()
                num_batches += 1
                self.global_step += 1

                # Update progress bar
                progress_bar.set_postfix({
                    'loss': loss.item(),
                    'avg_loss': epoch_loss / num_batches,
                    'lr': self.scheduler.get_last_lr()[0]
                })

                # Log and save checkpoints
                if self.global_step % self.config['training']['logging_steps'] == 0:
                    avg_loss = total_loss / self.global_step
                    self._log_metrics({
                        'train_loss': loss.item(),
                        'avg_train_loss': avg_loss,
                        'learning_rate': self.scheduler.get_last_lr()[0],
                        'epoch': epoch,
                        'step': self.global_step
                    })

                if self.global_step % self.config['training']['save_steps'] == 0:
                    self._save_checkpoint(f"step-{self.global_step}")

                # Validation
                if self.val_loader and self.global_step % self.config['training']['eval_steps'] == 0:
                    val_loss = self.evaluate()
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        self._save_checkpoint("best_model")
                        logger.info(f"New best validation loss: {val_loss:.4f}")

            # End of epoch
            avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else 0
            logger.info(f"Epoch {epoch+1} completed. Average loss: {avg_epoch_loss:.4f}")

            # Save checkpoint at end of epoch
            self._save_checkpoint(f"epoch-{epoch+1}")

        # Final evaluation
        if self.val_loader:
            final_val_loss = self.evaluate()
            logger.info(f"Final validation loss: {final_val_loss:.4f}")

        # Save final model
        self._save_checkpoint("final")
        logger.info("Training completed!")

    def evaluate(self) -> float:
        """
        Evaluate model on validation set

        Returns:
            Average validation loss
        """
        if not self.val_loader:
            return 0.0

        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in self.val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                loss = outputs['loss']
                total_loss += loss.item()
                num_batches += 1

        self.model.train()
        return total_loss / num_batches if num_batches > 0 else 0.0

    def _save_checkpoint(self, checkpoint_name: str):
        """Save model checkpoint"""
        checkpoint_dir = self.output_dir / checkpoint_name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Save model
        model_path = checkpoint_dir / "model.pt"
        torch.save(self.model.state_dict(), model_path)

        # Save tokenizer
        if self.tokenizer:
            tokenizer_path = checkpoint_dir / "tokenizer"
            self.tokenizer.save_pretrained(tokenizer_path)

        # Save config
        config_path = checkpoint_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f)

        # Save training state
        state_path = checkpoint_dir / "training_state.json"
        state = {
            'epoch': self.epoch,
            'global_step': self.global_step,
            'best_loss': self.best_loss,
            'config': self.config
        }
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Checkpoint saved: {checkpoint_name}")

    def _log_metrics(self, metrics: dict):
        """Log training metrics"""
        log_file = self.log_dir / f"training_log_{self.epoch}.jsonl"
        with open(log_file, 'a') as f:
            log_entry = {
                'timestamp': torch.datetime.now().isoformat(),
                'step': self.global_step,
                **metrics
            }
            f.write(json.dumps(log_entry) + '\n')

        # Also print to console
        logger.info(f"Step {self.global_step}: {metrics}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load model from checkpoint"""
        checkpoint_path = Path(checkpoint_path)

        # Load model
        model_path = checkpoint_path / "model.pt"
        if model_path.exists():
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info(f"Loaded model from {model_path}")

        # Load tokenizer
        tokenizer_path = checkpoint_path / "tokenizer"
        if tokenizer_path.exists():
            self.tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_path)
            logger.info(f"Loaded tokenizer from {tokenizer_path}")

        # Load config
        config_path = checkpoint_path / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded config from {config_path}")

        # Load training state
        state_path = checkpoint_path / "training_state.json"
        if state_path.exists():
            with open(state_path, 'r') as f:
                state = json.load(f)
                self.epoch = state.get('epoch', 0)
                self.global_step = state.get('global_step', 0)
                self.best_loss = state.get('best_loss', float('inf'))
            logger.info(f"Loaded training state from {state_path}")

# Helper function for learning rate scheduler
def get_linear_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps):
    """
    Create a schedule with a learning rate that decreases linearly after
    linearly increasing during a warmup period.
    """
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        return max(
            0.0, float(num_training_steps - current_step) / float(max(1, num_training_steps - num_warmup_steps))
        )

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python trainer.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Create dummy data for testing
    texts = [
        "This is a sample text for testing the trainer.",
        "Another example sentence to demonstrate functionality.",
        "Machine learning is fascinating and complex.",
        "Natural language processing enables computers to understand human language."
    ] * 100  # Repeat to have enough data

    # Initialize trainer
    trainer = Trainer(config_file)

    # For testing, we'll create a simple tokenizer
    # In practice, you would load or train a proper tokenizer
    from transformers import BertTokenizer
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    # Prepare data
    trainer.prepare_data(texts, tokenizer)

    # Initialize model
    trainer.initialize_model()

    # Setup optimizer and scheduler
    trainer.setup_optimizer_and_scheduler()

    # Train
    trainer.train()