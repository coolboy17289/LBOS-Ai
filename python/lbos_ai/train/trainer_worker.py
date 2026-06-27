"""
Training worker for LBOS-AI
Called by Node.js job processor to train models
"""
import sys
import json
import logging
import os
from pathlib import Path
from .trainer import Trainer
from .model import TransformerLM
from transformers import PreTrainedTokenizerFast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 4:
        print("Usage: python trainer_worker.py <DATASET_ID> <CONFIG_JSON> <JOB_ID>")
        sys.exit(1)

    dataset_id = sys.argv[1]
    config_json = sys.argv[2]
    job_id = sys.argv[3]

    try:
        # Parse config
        config = json.loads(config_json)

        # Load dataset
        data_dir = Path("./data/processed")
        texts = []

        # Load all processed data (in production, you would filter by dataset_id)
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.jsonl'):
                    file_path = Path(root) / file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                item = json.loads(line)
                                if 'transcript' in item:
                                    texts.append(item['transcript'])

        if not texts:
            raise ValueError("No training data found")

        # Limit dataset size for demo (in production, use proper sampling)
        if len(texts) > 10000:
            texts = texts[:10000]

        logger.info(f"Loaded {len(texts)} training samples for job {job_id}")

        # Initialize tokenizer (in production, load from saved tokenizer)
        tokenizer = None
        tokenizer_path = Path("./models/tokenizer")
        if tokenizer_path.exists():
            tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_path)
        else:
            # For demo, create a simple tokenizer
            from transformers import BertTokenizer
            tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            # Save it for future use
            tokenizer_path.mkdir(parents=True, exist_ok=True)
            tokenizer.save_pretrained(tokenizer_path)

        # Initialize trainer
        trainer = Trainer()
        trainer.config.update(config)  # Override with job-specific config

        # Prepare data
        trainer.prepare_data(texts, tokenizer)

        # Initialize model
        trainer.initialize_model()

        # Setup optimizer and scheduler
        trainer.setup_optimizer_and_scheduler()

        # Train
        trainer.train()

        # Get the latest checkpoint
        latest_checkpoint = max(
            [d for d in os.listdir(trainer.output_dir) if os.path.isdir(os.path.join(trainer.output_dir, d))],
            key=lambda x: os.path.getctime(os.path.join(trainer.output_dir, x))
        )
        model_path = os.path.join(trainer.output_dir, latest_checkpoint, "model.pt")

        # Return success
        result = {
            "status": "success",
            "job_id": job_id,
            "model_path": model_path,
            "message": "Training completed successfully"
        }
        print(json.dumps(result))

    except Exception as e:
        logger.error(f"Error in training worker for job {job_id}: {e}")
        print(json.dumps({
            "status": "error",
            "job_id": job_id,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()