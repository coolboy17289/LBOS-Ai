"""
Evaluation worker for LBOS-AI
Called by Node.js job processor to evaluate models
"""
import sys
import json
import logging
import os
from pathlib import Path
from .evaluator import evaluate_model
from transformers import PreTrainedTokenizerFast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 4:
        print("Usage: python evaluation_worker.py <MODEL_ID> <TEST_SET_ID> <JOB_ID>")
        sys.exit(1)

    model_id = sys.argv[1]
    test_set_id = sys.argv[2]
    job_id = sys.argv[3]

    try:
        # In a real implementation, you would load the model and test set from storage
        # For now, we'll simulate or use placeholder paths

        model_path = f"./models/{model_id}/model.pt"
        tokenizer_path = f"./models/{model_id}/tokenizer"
        test_data_path = f"./data/processed/test_{test_set_id}.jsonl"

        # Check if files exist
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError(f"Tokenizer not found: {tokenizer_path}")

        if not os.path.exists(test_data_path):
            # For demo, use general processed data
            test_data_path = "./data/processed"
            if not os.path.exists(test_data_path):
                raise FileNotFoundError(f"Test data not found: {test_data_path}")

        # Run evaluation
        results = evaluate_model(model_path, tokenizer_path, test_data_path)

        # Save results
        results_dir = Path("./eval/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        results_file = results_dir / f"eval_{job_id}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Return success
        result = {
            "status": "success",
            "job_id": job_id,
            "results_path": str(results_file),
            "metrics": results.get("metrics", {}),
            "message": "Evaluation completed successfully"
        }
        print(json.dumps(result))

    except Exception as e:
        logger.error(f"Error in evaluation worker for job {job_id}: {e}")
        print(json.dumps({
            "status": "error",
            "job_id": job_id,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()