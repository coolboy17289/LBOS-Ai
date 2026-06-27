"""
Feedback Loop Training System for LBOS-AI
Implements continuous learning from user interactions and corrections
"""
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import hashlib
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class FeedbackItem:
    """Represents a single piece of feedback for training"""
    def __init__(self,
                 input_text: str,
                 model_output: str,
                 expected_output: str,
                 feedback_type: str,  # 'correction', 'rating', 'ranking'
                 score: float = None,  # For rating feedback (0-1)
                 metadata: Dict = None):
        self.input_text = input_text
        self.model_output = model_output
        self.expected_output = expected_output
        self.feedback_type = feedback_type
        self.score = score
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for this feedback item"""
        data = f"{self.input_text}_{self.model_output}_{self.expected_output}_{self.timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'input_text': self.input_text,
            'model_output': self.model_output,
            'expected_output': self.expected_output,
            'feedback_type': self.feedback_type,
            'score': self.score,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FeedbackItem':
        """Create from dictionary"""
        item = cls(
            input_text=data['input_text'],
            model_output=data['model_output'],
            expected_output=data['expected_output'],
            feedback_type=data['feedback_type'],
            score=data.get('score'),
            metadata=data.get('metadata', {})
        )
        item.id = data['id']
        item.timestamp = datetime.fromisoformat(data['timestamp'])
        return item

class FeedbackDataset(Dataset):
    """PyTorch Dataset for feedback data"""
    def __init__(self, feedback_items: List[FeedbackItem], tokenizer, max_length: int = 512):
        self.feedback_items = feedback_items
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = self._prepare_examples()

    def _prepare_examples(self) -> List[Dict]:
        """Convert feedback items to training examples"""
        examples = []
        for item in self.feedback_items:
            # For correction feedback, create training pairs
            if item.feedback_type == 'correction':
                # Input: original prompt + model output
                # Expected: corrected output
                input_text = f"Correct the following: {item.input_text}\nModel output: {item.model_output}\nCorrection:"
                target_text = item.expected_output

                # Tokenize
                input_encoding = self.tokenizer(
                    input_text,
                    truncation=True,
                    max_length=self.max_length,
                    padding='max_length',
                    return_tensors='pt'
                )

                target_encoding = self.tokenizer(
                    target_text,
                    truncation=True,
                    max_length=self.max_length,
                    padding='max_length',
                    return_tensors='pt'
                )

                examples.append({
                    'input_ids': input_encoding['input_ids'].squeeze(),
                    'attention_mask': input_encoding['attention_mask'].squeeze(),
                    'labels': target_encoding['input_ids'].squeeze(),
                    'feedback_weight': 1.0  # Could be adjusted based on feedback score
                })

            # For rating feedback, we could use reinforcement learning approaches
            elif item.feedback_type == 'rating' and item.score is not None:
                # Higher score = better output, use for reinforcement learning
                pass

        return examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

class FeedbackTrainer:
    """Handles training from feedback data"""
    def __init__(self, base_model, tokenizer, feedback_dir: str = "./feedback"):
        """
        Initialize feedback trainer

        Args:
            base_model: The base model to fine-tune
            tokenizer: Tokenizer for the model
            feedback_dir: Directory to store feedback data
        """
        self.model = base_model
        self.tokenizer = tokenizer
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

        # Storage for feedback
        self.feedback_buffer: List[FeedbackItem] = []
        self.min_feedback_for_training = 10  # Minimum feedback before triggering training
        self.training_threshold_hours = 24   # Max time between training sessions

        # Training configuration
        self.learning_rate = 1e-5
        self.batch_size = 4
        self.epochs = 3
        self.warmup_steps = 100

        # Optimizer and scheduler will be initialized when needed
        self.optimizer = None
        self.scheduler = None

        logger.info(f"Feedback trainer initialized with directory: {self.feedback_dir}")

    def add_feedback(self, feedback: FeedbackItem):
        """
        Add feedback to the training buffer

        Args:
            feedback: Feedback item to add
        """
        self.feedback_buffer.append(feedback)
        logger.info(f"Added feedback item {feedback.id}. Buffer size: {len(self.feedback_buffer)}")

        # Persist to disk
        self._save_feedback_to_disk(feedback)

        # Check if we should trigger training
        if self._should_trigger_training():
            self.schedule_training()

    def _save_feedback_to_disk(self, feedback: FeedbackItem):
        """Save feedback item to disk for persistence"""
        feedback_file = self.feedback_dir / f"feedback_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(feedback_file, 'a') as f:
            f.write(json.dumps(feedback.to_dict()) + '\n')

    def load_feedback_from_disk(self, days: int = 7) -> List[FeedbackItem]:
        """
        Load feedback from disk

        Args:
            days: Number of days of feedback to load

        Returns:
            List of feedback items
        """
        feedback_items = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for feedback_file in self.feedback_dir.glob("feedback_*.jsonl"):
            # Extract date from filename
            try:
                date_str = feedback_file.stem.split('_')[1]
                file_date = datetime.strptime(date_str, '%Y%m%d')
                if file_date < cutoff_date:
                    continue
            except:
                # If we can't parse date, include it anyway
                pass

            try:
                with open(feedback_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line.strip())
                            feedback_items.append(FeedbackItem.from_dict(data))
            except Exception as e:
                logger.error(f"Error loading feedback from {feedback_file}: {e}")

        logger.info(f"Loaded {len(feedback_items)} feedback items from disk")
        return feedback_items

    def _should_trigger_training(self) -> bool:
        """Determine if training should be triggered based on feedback volume and time"""
        # Check if we have enough feedback
        if len(self.feedback_buffer) < self.min_feedback_for_training:
            return False

        # Check time since last training (would need to track this)
        # For simplicity, we'll train when we reach certain thresholds
        return len(self.feedback_buffer) >= self.min_feedback_for_training * 2

    def schedule_training(self):
        """Schedule a training session (in production, this would use a job queue)"""
        logger.info("Scheduling feedback training session...")
        # In a real system, this would message a queue or trigger a training pipeline
        # For now, we'll just run it synchronously
        self.train_from_feedback()

    def train_from_feedback(self) -> Dict[str, Any]:
        """
        Train the model using accumulated feedback

        Returns:
            Dictionary with training results
        """
        if len(self.feedback_buffer) < self.min_feedback_for_training:
            return {
                'status': 'skipped',
                'reason': f'Insufficient feedback ({len(self.feedback_buffer)} < {self.min_feedback_for_training})'
            }

        logger.info(f"Starting feedback training with {len(self.feedback_buffer)} items")

        try:
            # Prepare dataset
            dataset = FeedbackDataset(self.feedback_buffer, self.tokenizer)
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

            # Initialize optimizer and scheduler
            self.optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate)
            total_steps = len(dataloader) * self.epochs
            self.scheduler = optim.lr_scheduler.LinearLR(
                self.optimizer,
                start_factor=0.1,
                total_iters=self.warmup_steps
            )

            # Training loop
            self.model.train()
            total_loss = 0.0
            steps = 0

            for epoch in range(self.epochs):
                epoch_loss = 0.0
                for batch in dataloader:
                    self.optimizer.zero_grad()

                    # Forward pass
                    outputs = self.model(
                        input_ids=batch['input_ids'],
                        attention_mask=batch['attention_mask'],
                        labels=batch['labels']
                    )

                    loss = outputs.loss
                    # Weight by feedback importance if available
                    if 'feedback_weight' in batch:
                        loss = loss * batch['feedback_weight']

                    # Backward pass
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    self.optimizer.step()
                    self.scheduler.step()

                    epoch_loss += loss.item()
                    steps += 1

                avg_epoch_loss = epoch_loss / len(dataloader)
                logger.info(f"Epoch {epoch+1}/{self.epochs} - Loss: {avg_epoch_loss:.4f}")
                total_loss += epoch_loss

            # Calculate final metrics
            avg_loss = total_loss / steps
            perplexity = np.exp(avg_loss)

            # Save the updated model
            self._save_model()

            # Clear the feedback buffer (optional - could keep for review)
            self.feedback_buffer.clear()

            result = {
                'status': 'completed',
                'epochs': self.epochs,
                'steps': steps,
                'average_loss': round(avg_loss, 4),
                'perplexity': round(perplexity, 2),
                'feedback_samples': len(dataset),
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Feedback training completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error during feedback training: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _save_model(self):
        """Save the updated model"""
        save_dir = self.feedback_dir / f"model_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        save_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.model.save_pretrained(save_dir)
            self.tokenizer.save_pretrained(save_dir)
            logger.info(f"Model saved to {save_dir}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected feedback"""
        if not self.feedback_buffer:
            return {
                'total_feedback': 0,
                'by_type': {},
                'recent_activity': None
            }

        # Count by type
        type_counts = defaultdict(int)
        for item in self.feedback_buffer:
            type_counts[item.feedback_type] += 1

        # Find most recent
        most_recent = max(self.feedback_buffer, key=lambda x: x.timestamp) if self.feedback_buffer else None

        return {
            'total_feedback': len(self.feedback_buffer),
            'by_type': dict(type_counts),
            'recent_activity': {
                'timestamp': most_recent.timestamp.isoformat() if most_recent else None,
                'type': most_recent.feedback_type if most_recent else None
            }
        }

class FeedbackAPI:
    """API endpoint handlers for feedback collection"""
    def __init__(self, feedback_trainer: FeedbackTrainer):
        self.trainer = feedback_trainer

    def collect_correction_feedback(self, request_data: Dict) -> Dict:
        """
        Collect correction feedback from user

        Expected request format:
        {
            "input_text": "Original user input",
            "model_output": "What the model generated",
            "expected_output": "What the user expected/corrected to",
            "context": {...}  # Optional additional context
        }
        """
        try:
            feedback = FeedbackItem(
                input_text=request_data['input_text'],
                model_output=request_data['model_output'],
                expected_output=request_data['expected_output'],
                feedback_type='correction',
                metadata=request_data.get('context', {})
            )

            self.trainer.add_feedback(feedback)

            return {
                'status': 'success',
                'feedback_id': feedback.id,
                'message': 'Feedback recorded successfully',
                'should_retrain': self.trainer._should_trigger_training()
            }

        except Exception as e:
            logger.error(f"Error collecting correction feedback: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def collect_rating_feedback(self, request_data: Dict) -> Dict:
        """
        Collect rating feedback from user

        Expected request format:
        {
            "input_text": "Original user input",
            "model_output": "What the model generated",
            "rating": 0.8,  # 0.0 to 1.0 scale
            "dimensions": {  # Optional: specific aspects rated
                "helpfulness": 0.9,
                "accuracy": 0.7,
                "relevance": 0.8
            }
        }
        """
        try:
            feedback = FeedbackItem(
                input_text=request_data['input_text'],
                model_output=request_data['model_output'],
                expected_output=request_data['model_output'],  # For rating, expected is same as actual
                feedback_type='rating',
                score=request_data['rating'],
                metadata={
                    'dimensions': request_data.get('dimensions', {}),
                    'original_request': request_data
                }
            )

            self.trainer.add_feedback(feedback)

            return {
                'status': 'success',
                'feedback_id': feedback.id,
                'message': 'Rating feedback recorded',
                'should_retrain': self.trainer._should_trigger_training()
            }

        except Exception as e:
            logger.error(f"Error collecting rating feedback: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

# Global feedback trainer instance
feedback_trainer = None

def get_feedback_trainer(model=None, tokenizer=None) -> FeedbackTrainer:
    """Get or create the global feedback trainer instance"""
    global feedback_trainer
    if feedback_trainer is None:
        if model is None or tokenizer is None:
            raise ValueError("Model and tokenizer must be provided for initial creation")
        feedback_trainer = FeedbackTrainer(model, tokenizer)
    return feedback_trainer

def init_feedback_trainer(model, tokenizer, feedback_dir: str = "./feedback") -> FeedbackTrainer:
    """Initialize the feedback trainer with required components"""
    global feedback_trainer
    feedback_trainer = FeedbackTrainer(model, tokenizer, feedback_dir)
    return feedback_trainer

# Example usage
if __name__ == "__main__":
    # This would normally be called with actual model and tokenizer
    # For demonstration, we'll show the structure

    print("Feedback Loop Training System for LBOS-AI")
    print("==========================================")

    # Example feedback items
    feedback1 = FeedbackItem(
        input_text="What is the capital of France?",
        model_output="The capital of France is London.",
        expected_output="The capital of France is Paris.",
        feedback_type='correction'
    )

    feedback2 = FeedbackItem(
        input_text="Explain quantum computing simply",
        model_output="Quantum computing uses quantum bits that can be 0 and 1 at the same time.",
        expected_output="Quantum computing uses qubits that can exist in superposition states, enabling parallel computation.",
        feedback_type='correction'
    )

    feedback3 = FeedbackItem(
        input_text="Write a haiku about autumn",
        model_output="Leaves falling down\nCool breeze whispers through the trees\nAutumn paints the ground",
        expected_output="Red leaves softly fall\nCrisp air carries winter's breath\nEarth prepares to rest",
        feedback_type='rating',
        score=0.8
    )

    print(f"Created {len([feedback1, feedback2, feedback3])} example feedback items")
    print("In a real implementation, these would be used to fine-tune the model")