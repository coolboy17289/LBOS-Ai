"""
Hugging Face integration for LBOS-AI
Shows how to use Hugging Face tokenizers while maintaining our own model
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

class HuggingFaceIntegration:
    """
    Demonstrates integration with Hugging Face ecosystem
    while keeping our model independent (no runtime LLM dependency)
    """

    def __init__(self, model_name: str = "bert-base-uncased"):
        """
        Initialize HF integration

        Args:
            model_name: Name of HF model to use for tokenization only
        """
        self.model_name = model_name
        self.tokenizer = None
        self._load_tokenizer()

    def _load_tokenizer(self):
        """Load tokenizer from Hugging Face"""
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info(f"Loaded HF tokenizer: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load HF tokenizer {self.model_name}: {e}")
            # Fallback to basic tokenizer
            self.tokenizer = None

    def tokenize_texts(self, texts: List[str], max_length: int = 512) -> dict:
        """
        Tokenize texts using HF tokenizer

        Args:
            texts: List of text strings
            max_length: Maximum sequence length

        Returns:
            Dictionary with input_ids and attention_mask
        """
        if self.tokenizer is None:
            # Fallback to simple whitespace tokenization
            return self._basic_tokenize(texts, max_length)

        try:
            encoding = self.tokenizer(
                texts,
                add_special_tokens=True,
                max_length=max_length,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_tensors='np'
            )

            return {
                'input_ids': encoding['input_ids'],
                'attention_mask': encoding['attention_mask']
            }
        except Exception as e:
            logger.error(f"Error in HF tokenization: {e}")
            return self._basic_tokenize(texts, max_length)

    def _basic_tokenize(self, texts: List[str], max_length: int = 512) -> dict:
        """Basic whitespace tokenization as fallback"""
        # Simple implementation for demonstration
        tokenized = []
        attention_masks = []

        # Build a simple vocab from the texts
        vocab = {"<PAD>": 0, "<UNK>": 1, "<CLS>": 2, "<SEP>": 3}
        word_counts = {}

        for text in texts:
            for word in text.lower().split():
                word_counts[word] = word_counts.get(word, 0) + 1

        # Add most common words to vocab
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (word, _) in enumerate(sorted_words):
            if len(vocab) >= 10000:  # Limit vocab size
                break
            if word not in vocab:
                vocab[word] = len(vocab)

        for text in texts:
            tokens = ["<CLS>"] + text.lower().split()[:max_length-2] + ["<SEP>"]
            if len(tokens) < max_length:
                tokens += ["<PAD>"] * (max_length - len(tokens))

            ids = [vocab.get(token, vocab["<UNK>"]) for token in tokens]
            mask = [1 if token != "<PAD>" else 0 for token in tokens]

            # Truncate or pad
            ids = ids[:max_length] + [0] * max(0, max_length - len(ids))
            mask = mask[:max_length] + [0] * max(0, max_length - len(mask))

            tokenized.append(ids)
            attention_masks.append(mask)

        return {
            'input_ids': np.array(tokenized),
            'attention_mask': np.array(attention_masks)
        }

    def decode_tokens(self, token_ids) -> str:
        """
        Decode token IDs back to text

        Args:
            token_ids: Array of token IDs

        Returns:
            Decoded string
        """
        if self.tokenizer is not None:
            try:
                return self.tokenizer.decode(token_ids, skip_special_tokens=True)
            except Exception as e:
                logger.error(f"Error decoding with HF tokenizer: {e}")

        # Fallback decoding
        if hasattr(self, 'inv_vocab'):
            tokens = [self.inv_vocab.get(id, "<UNK>") for id in token_ids]
            return " ".join(tokens).replace("<PAD>", "").strip()
        else:
            return f"[Token IDs: {token_ids}]"

    def get_vocab_size(self) -> int:
        """Get vocabulary size"""
        if self.tokenizer is not None and hasattr(self.tokenizer, 'vocab_size'):
            return self.tokenizer.vocab_size
        elif hasattr(self, 'vocab'):
            return len(self.vocab)
        else:
            return 30522  # Default

# Example usage showing how we might use HF for data processing but not for model
def example_usage():
    """
    Example showing proper usage of HF components in LBOS-AI:
    - Use HF tokenizers for text processing
    - Use HF datasets for loading data
    - BUT train our own model from scratch (no HF model weights)
    """
    # This is just for demonstration - in practice, you'd use this in your data pipeline
    hf_integration = HuggingFaceIntegration()

    # Example texts
    texts = [
        "Hello world, this is a test.",
        "Another example for tokenization."
    ]

    # Tokenize using HF tokenizer
    encoded = hf_integration.tokenize_texts(texts)
    print(f"Input IDs shape: {encoded['input_ids'].shape}")
    print(f"Attention mask shape: {encoded['attention_mask'].shape}")

    # Decode back
    decoded = [hf_integration.decode_tokens(ids) for ids in encoded['input_ids']]
    print(f"Decoded texts: {decoded}")

    # Note: We would NOT use HF models for actual prediction/training
    # We would only use them for preprocessing/tokenization if beneficial
    # Our core model remains independent and trained from scratch

if __name__ == "__main__":
    example_usage()