"""
Model evaluation module for LBOS-AI
Handles evaluation of trained models on test datasets
"""
import os
import json
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from tqdm import tqdm

# Import our model and tokenizer
from ..train.model import TransformerLM
from transformers import PreTrainedTokenizerFast

# Configure logging
logger = logging.getLogger(__name__)

def perplexity(model: torch.nn.Module, dataloader: torch.utils.data.DataLoader, device: torch.device) -> float:
    """
    Calculate perplexity of model on dataset

    Args:
        model: Trained model
        dataloader: DataLoader for evaluation data
        device: Device to run evaluation on

    Returns:
        Perplexity score
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Calculating perplexity"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs['loss']
            # Get number of non-padded tokens
            num_tokens = attention_mask.sum().item()

            total_loss += loss.item() * num_tokens
            total_tokens += num_tokens

    # Calculate perplexity: exp(average loss)
    avg_loss = total_loss / max(total_tokens, 1)
    ppl = math.exp(min(avg_loss, 20))  # Cap to avoid overflow
    return ppl

def evaluate_qa(model: torch.nn.Module,
                tokenizer: PreTrainedTokenizerFast,
                qa_pairs: List[Dict],
                device: torch.device,
                max_length: int = 512) -> Dict[str, float]:
    """
    Evaluate model on question-answering task

    Args:
        model: Trained model
        tokenizer: Tokenizer
        qa_pairs: List of dictionaries with 'question' and 'answer' keys
        device: Device to run evaluation on
        max_length: Maximum sequence length

    Returns:
        Dictionary with EM (Exact Match) and F1 scores
    """
    model.eval()
    exact_match = 0
    f1_score = 0.0
    total = len(qa_pairs)

    if total == 0:
        return {"exact_match": 0.0, "f1": 0.0}

    with torch.no_grad():
        for qa in tqdm(qa_pairs, desc="Evaluating QA"):
            question = qa['question']
            true_answer = qa['answer'].lower().strip()

            # Prepare input
            input_text = f"Question: {question} Answer:"
            encoding = tokenizer(
                input_text,
                truncation=True,
                max_length=max_length,
                padding='max_length',
                return_tensors='pt'
            )

            input_ids = encoding['input_ids'].to(device)
            attention_mask = attention_mask.to(device)

            # Generate answer
            generated_ids = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=min(50, max_length),
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

            # Decode generated text
            generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
            # Extract answer (everything after "Answer:")
            if "Answer:" in generated_text:
                pred_answer = generated_text.split("Answer:")[1].strip().lower()
            else:
                pred_answer = generated_text.strip().lower()

            # Calculate exact match
            if pred_answer == true_answer:
                exact_match += 1

            # Calculate F1 score
            pred_tokens = set(pred_answer.split())
            true_tokens = set(true_answer.split())

            if len(pred_tokens) == 0 and len(true_tokens) == 0:
                f1 = 1.0
            elif len(pred_tokens) == 0 or len(true_tokens) == 0:
                f1 = 0.0
            else:
                common = len(pred_tokens & true_tokens)
                precision = common / len(pred_tokens) if len(pred_tokens) > 0 else 0
                recall = common / len(true_tokens) if len(true_tokens) > 0 else 0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            f1_score += f1

    return {
        "exact_match": exact_match / total,
        "f1": f1_score / total
    }

def evaluate_model(model_path: str,
                  tokenizer_path: str,
                  test_data_path: str,
                  batch_size: int = 16,
                  max_length: int = 512) -> Dict:
    """
    Main evaluation function

    Args:
        model_path: Path to model checkpoint
        tokenizer_path: Path to tokenizer
        test_data_path: Path to test data (JSONL format)
        batch_size: Batch size for evaluation
        max_length: Maximum sequence length

    Returns:
        Dictionary with evaluation metrics
    """
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load model
    model = TorchTransformerLM.load_from_checkpoint(model_path)
    model.to(device)
    model.eval()
    logger.info(f"Model loaded from {model_path}")

    # Load tokenizer
    tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_path)
    logger.info(f"Tokenizer loaded from {tokenizer_path}")

    # Load test data
    test_texts = []
    test_qa_pairs = []

    with open(test_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                text = item.get('transcript', '')
                if text:
                    test_texts.append(text)

                # Extract QA pairs if available
                if 'qa_pairs' in item and isinstance(item['qa_pairs'], list):
                    for qa in item['qa_pairs']:
                        if isinstance(qa, dict) and 'question' in qa and 'answer' in qa:
                            test_qa_pairs.append({
                                'question': qa['question'],
                                'answer': qa['answer']
                            })

    # Create dataset and dataloader
    test_dataset = TextDataset(test_texts, tokenizer, max_length)
    test_dataloader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2
    )

    # Calculate perplexity
    ppl = perplexity(model, test_dataloader, device)
    logger.info(f"Perplexity: {ppl:.2f}")

    # Evaluate QA if we have QA pairs
    qa_results = {"exact_match": 0.0, "f1": 0.0}
    if test_qa_pairs:
        qa_results = evaluate_qa(model, tokenizer, test_qa_pairs, device, max_length)
        logger.info(f"QA Results - EM: {qa_results['exact_match']:.4f}, F1: {qa_results['f1']:.4f}")

    # Compile results
    results = {
        "perplexity": ppl,
        "exact_match": qa_results["exact_match"],
        "f1": qa_results["f1"],
        "eval_samples": len(test_texts),
        "qa_samples": len(test_qa_pairs),
        "model_path": model_path,
        "tokenizer_path": tokenizer_path,
        "timestamp": torch.datetime.now().isoformat()
    }

    # Save results
    output_dir = Path(model_path).parent / "evaluation_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / f"eval_{int(time.time())}.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Evaluation results saved to {result_file}")
    return results

# For testing
if __name__ == "__main__":
    import sys
    import time
    import math
    from torch.utils.data import DataLoader

    if len(sys.argv) < 4:
        print("Usage: python evaluator.py <model_path> <tokenizer_path> <test_data_path>")
        sys.exit(1)

    model_path = sys.argv[1]
    tokenizer_path = sys.argv[2]
    test_data_path = sys.argv[3]

    results = evaluate_model(model_path, tokenizer_path, test_data_path)
    print(json.dumps(results, indent=2))