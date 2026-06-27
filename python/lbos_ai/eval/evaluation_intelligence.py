"""
Evaluation Intelligence Layer for LBOS-AI
Advanced evaluation metrics and analysis beyond basic perplexity
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import *
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class EvaluationIntelligence:
    """
    Advanced evaluation system for language models
    Goes beyond perplexity to provide comprehensive insights
    """
    def __init__(self, output_dir: str = "./eval/reports"):
        """
        Initialize evaluation intelligence system

        Args:
            output_dir: Directory to save evaluation reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_history = []

        # Initialize semantic similarity model for advanced metrics
        try:
            from sentence_transformers import SentenceTransformer
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.semantic_available = True
        except ImportError:
            logger.warning("sentence-transformers not available, semantic metrics disabled")
            self.semantic_model = None
            self.semantic_available = False

    def evaluate_model_comprehensive(self,
                                   model,
                                   tokenizer,
                                   test_data: List[Dict],
                                   task_type: str = "general") -> Dict[str, Any]:
        """
        Perform comprehensive evaluation of a model

        Args:
            model: The model to evaluate
            tokenizer: Tokenizer for the model
            test_data: List of test examples with inputs and expected outputs
            task_type: Type of task (e.g., 'qa', 'summarization', 'classification', 'general')

        Returns:
            Dictionary with comprehensive evaluation results
        """
        logger.info(f"Starting comprehensive evaluation for {task_type} task with {len(test_data)} samples")

        results = {
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type,
            'sample_count': len(test_data),
            'metrics': {},
            'detailed_analysis': {},
            'error_analysis': {},
            'trends': {}
        }

        # Generate predictions
        predictions = self._generate_predictions(model, tokenizer, test_data)
        references = [item.get('expected_output', '') for item in test_data]
        inputs = [item.get('input_text', '') for item in test_data]

        # Basic metrics
        results['metrics'].update(self._calculate_basic_metrics(predictions, references))

        # Task-specific metrics
        if task_type == 'qa':
            results['metrics'].update(self._calculate_qa_metrics(predictions, references, test_data))
        elif task_type == 'summarization':
            results['metrics'].update(self._calculate_summarization_metrics(predictions, references, inputs))
        elif task_type == 'classification':
            results['metrics'].update(self._calculate_classification_metrics(predictions, references, test_data))
        elif task_type == 'translation':
            results['metrics'].update(self._calculate_translation_metrics(predictions, references))

        # Advanced linguistic metrics
        results['metrics'].update(self._calculate_linguistic_metrics(predictions, references))

        # Semantic similarity (if available)
        if self.semantic_available:
            results['metrics'].update(self._calculate_semantic_metrics(predictions, references))

        # Fairness and bias analysis
        results['detailed_analysis']['fairness'] = self._analyze_fairness(predictions, references, test_data)

        # Error analysis
        results['error_analysis'] = self._perform_error_analysis(predictions, references, test_data, inputs)

        # Stability and consistency
        results['detailed_analysis']['stability'] = self._analyze_stability(model, tokenizer, test_data[:min(10, len(test_data))])

        # Uncertainty quantification (if model supports it)
        results['detailed_analysis']['uncertainty'] = self._estimate_uncertainty(model, tokenizer, test_data[:min(5, len(test_data))])

        # Save detailed report
        self._save_evaluation_report(results)

        # Add to history for trend analysis
        self.evaluation_history.append({
            'timestamp': results['timestamp'],
            'task_type': task_type,
            'metrics': results['metrics'].copy()
        })

        # Update trends if we have enough history
        if len(self.evaluation_history) >= 3:
            results['trends'] = self._calculate_trends()

        logger.info(f"Evaluation completed. Main metrics: {results['metrics']}")
        return results

    def _generate_predictions(self, model, tokenizer, test_data: List[Dict]) -> List[str]:
        """Generate predictions from the model"""
        predictions = []
        model.eval()

        with torch.no_grad():
            for item in test_data:
                input_text = item.get('input_text', '')
                if not input_text:
                    predictions.append("")
                    continue

                # Tokenize input
                inputs = tokenizer(
                    input_text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True
                )

                # Generate
                try:
                    outputs = model.generate(
                        **inputs,
                        max_length=min(512, inputs['input_ids'].shape[1] + 50),
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )

                    # Decode only the generated part
                    input_length = inputs['input_ids'].shape[1]
                    generated_tokens = outputs[0][input_length:]
                    prediction = tokenizer.decode(generated_tokens, skip_special_tokens=True)
                    predictions.append(prediction.strip())
                except Exception as e:
                    logger.warning(f"Error generating prediction for '{input_text[:50]}...': {e}")
                    predictions.append("")

        return predictions

    def _calculate_basic_metrics(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Calculate basic accuracy-like metrics"""
        if not predictions or not references:
            return {}

        # Exact match
        exact_matches = sum(1 for p, r in zip(predictions, references) if p.strip().lower() == r.strip().lower())
        exact_match_ratio = exact_matches / len(predictions) if predictions else 0

        # Token-level accuracy (simple)
        token_matches = 0
        total_tokens = 0
        for p, r in zip(predictions, references):
            p_tokens = p.lower().split()
            r_tokens = r.lower().split()
            if len(p_tokens) == 0 and len(r_tokens) == 0:
                continue
            if len(p_tokens) == 0 or len(r_tokens) == 0:
                continue
            matches = sum(1 for i in range(min(len(p_tokens), len(r_tokens))) if p_tokens[i] == r_tokens[i])
            token_matches += matches
            total_tokens += max(len(p_tokens), len(r_tokens))

        token_accuracy = token_matches / total_tokens if total_tokens > 0 else 0

        # Length ratio statistics
        pred_lengths = [len(p.split()) for p in predictions]
        ref_lengths = [len(r.split()) for r in references]
        length_ratio = np.mean([p/r if r > 0 else 0 for p, r in zip(pred_lengths, ref_lengths)]) if ref_lengths and any(r > 0 for r in ref_lengths) else 0

        return {
            'exact_match_ratio': round(exact_match_ratio, 4),
            'token_accuracy': round(token_accuracy, 4),
            'average_prediction_length': round(np.mean(pred_lengths), 2) if pred_lengths else 0,
            'average_reference_length': round(np.mean(ref_lengths), 2) if ref_lengths else 0,
            'length_ratio': round(length_ratio, 4)
        }

    def _calculate_qa_metrics(self, predictions: List[str], references: List[str], test_data: List[Dict]) -> Dict[str, float]:
        """Calculate Question-Answering specific metrics"""
        if not predictions or not references:
            return {}

        # Exact Match (EM)
        em = self._compute_exact_match(predictions, references)

        # F1 Score (token-level)
        f1 = self._compute_f1_score(predictions, references)

        # Handle unanswerable questions if present
        has_unanswerable = any('is_impossible' in item and item['is_impossible'] for item in test_data)
        if has_unanswerable:
            # For SQuAD-like format with unanswerable questions
            pass  # Would implement specific logic here

        return {
            'qa_exact_match': round(em, 4),
            'qa_f1_score': round(f1, 4)
        }

    def _calculate_summarization_metrics(self, predictions: List[str], references: List[str], inputs: List[str]) -> Dict[str, float]:
        """Calculate summarization specific metrics"""
        if not predictions or not references:
            return {}

        # ROUGE scores (simplified implementation)
        rouge_scores = self._compute_rouge_scores(predictions, references)

        # Compression ratio
        compression_ratios = []
        for pred, inp in zip(predictions, inputs):
            if len(inp.split()) > 0:
                ratio = len(pred.split()) / len(inp.split())
                compression_ratios.append(min(ratio, 1.0))  # Cap at 1.0 (no expansion)

        avg_compression = np.mean(compression_ratios) if compression_ratios else 0

        # Length appropriateness (penalize too short or too long)
        target_ratios = [0.2, 0.3]  # Ideal summary is 20-30% of original
        length_scores = []
        for ratio in compression_ratios:
            # Score based on closeness to target range
            if 0.2 <= ratio <= 0.3:
                score = 1.0
            elif ratio < 0.2:
                score = ratio / 0.2  # Linear penalty for too short
            else:
                score = 0.3 / ratio  # Penalty for too long
            length_scores.append(score)

        avg_length_score = np.mean(length_scores) if length_scores else 0

        return {
            'rouge_1': round(rouge_scores.get('rouge_1', 0), 4),
            'rouge_2': round(rouge_scores.get('rouge_2', 0), 4),
            'rouge_l': round(rouge_scores.get('rouge_l', 0), 4),
            'compression_ratio': round(np.mean(compression_ratios), 4) if compression_ratios else 0,
            'length_appropriateness': round(avg_length_score, 4)
        }

    def _calculate_classification_metrics(self, predictions: List[str], references: List[str], test_data: List[Dict]) -> Dict[str, float]:
        """Calculate classification metrics"""
        if not predictions or not references:
            return {}

        # For simplicity, treat as binary/multi-class classification
        # In practice, you'd need label mapping
        try:
            # Convert to numeric labels if possible
            unique_labels = list(set(references))
            label_to_id = {label: i for i, label in enumerate(unique_labels)}

            y_true = [label_toid.get(r, -1) for r in references]
            y_pred = [label_toid.get(p, -1) for p in predictions]

            # Filter out unknown labels
            valid_indices = [i for i in range(len(y_true)) if y_true[i] != -1 and y_pred[i] != -1]
            if not valid_indices:
                return {'classification_accuracy': 0.0}

            y_true_valid = [y_true[i] for i in valid_indices]
            y_pred_valid = [y_pred[i] for i in valid_indices]

            accuracy = accuracy_score(y_true_valid, y_pred_valid)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_true_valid, y_pred_valid, average='weighted', zero_division=0
            )

            return {
                'classification_accuracy': round(accuracy, 4),
                'classification_precision': round(precision, 4),
                'classification_recall': round(recall, 4),
                'classification_f1': round(f1, 4)
            }
        except Exception as e:
            logger.warning(f"Could not compute classification metrics: {e}")
            return {'classification_accuracy': 0.0}

    def _calculate_translation_metrics(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Calculate translation specific metrics"""
        if not predictions or not references:
            return {}

        # BLEU score (simplified)
        bleu_score = self._compute_bleu_score(predictions, references)

        return {
            'bleu_score': round(bleu_score, 4)
        }

    def _calculate_linguistic_metrics(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Calculate linguistic quality metrics"""
        if not predictions:
            return {}

        metrics = {}

        # Perplexity approximation (would need model access for true perplexity)
        # Instead, we use language modeling heuristics

        # Repetition rate
        repetition_scores = []
        for pred in predictions:
            words = pred.lower().split()
            if len(words) > 1:
                unique_words = len(set(words))
                repetition_score = 1 - (unique_words / len(words))
                repetition_scores.append(repetition_score)
            else:
                repetition_scores.append(0.0)

        metrics['repetition_rate'] = round(np.mean(repetition_scores), 4) if repetition_scores else 0

        # Length variance (consistency)
        lengths = [len(p.split()) for p in predictions if p.strip()]
        if len(lengths) > 1:
            metrics['length_std'] = round(np.std(lengths), 2)
            metrics['length_cv'] = round(np.std(lengths) / np.mean(lengths), 4) if np.mean(lengths) > 0 else 0
        else:
            metrics['length_std'] = 0
            metrics['length_cv'] = 0

        # Special character ratio
        special_char_ratios = []
        for pred in predictions:
            if len(pred) > 0:
                special_count = sum(1 for c in pred if not c.isalnum() and not c.isspace())
                ratio = special_char_count / len(pred)
                special_char_ratios.append(ratio)
            else:
                special_char_ratios.append(0)

        metrics['special_character_ratio'] = round(np.mean(special_char_ratios), 4) if special_char_ratios else 0

        # Sentence count
        sentence_counts = []
        for pred in predictions:
            # Simple sentence counting
            sentences = re.split(r'[.!?]+', pred)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_counts.append(len(sentences))

        metrics['average_sentences'] = round(np.mean(sentence_counts), 2) if sentence_counts else 0
        metrics['average_words_per_sentence'] = round(
            np.mean([len(p.split()) for p in predictions if p.split()]) if any(p.split() for p in predictions) else 0, 2
        )

        return metrics

    def _calculate_semantic_metrics(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Calculate semantic similarity metrics"""
        if not self.semantic_available or not predictions or not references:
            return {}

        try:
            # Get embeddings
            pred_embeddings = self.semantic_model.encode(predictions)
            ref_embeddings = self.semantic_model.encode(references)

            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = []
            for i in range(len(pred_embeddings)):
                sim = cosine_similarity([pred_embeddings[i]], [ref_embeddings[i]])[0][0]
                similarities.append(sim)

            return {
                'semantic_similarity_mean': round(np.mean(similarities), 4),
                'semantic_similarity_std': round(np.std(similarities), 4),
                'semantic_similarity_min': round(np.min(similarities), 4),
                'semantic_similarity_max': round(np.max(similarities), 4)
            }
        except Exception as e:
            logger.warning(f"Could not compute semantic metrics: {e}")
            return {}

    def _compute_exact_match(self, predictions: List[str], references: List[str]) -> float:
        """Compute exact match score"""
        if not predictions or not references:
            return 0.0
        matches = sum(1 for p, r in zip(predictions, references) if p.strip().lower() == r.strip().lower())
        return matches / len(predictions)

    def _compute_f1_score(self, predictions: List[str], references: List[str]) -> float:
        """Compute token-level F1 score"""
        if not predictions or not references:
            return 0.0

        f1_scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = pred.lower().split()
            ref_tokens = ref.lower().split()

            if len(pred_tokens) == 0 and len(ref_tokens) == 0:
                f1_scores.append(1.0)
                continue
            if len(pred_tokens) == 0 or len(ref_tokens) == 0:
                f1_scores.append(0.0)
                continue

            common = set(pot) & set(ref_tokens)
            if len(common) == 0:
                f1_scores.append(0.0)
                continue

            precision = len(common) / len(pred_tokens)
            recall = len(common) / len(ref_tokens)
            if precision + recall == 0:
                f1 = 0.0
            else:
                f1 = 2 * (precision * recall) / (precision + recall)
            f1_scores.append(f1)

        return np.mean(f1_scores) if f1_scores else 0.0

    def _compute_rouge_scores(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Compute ROUGE scores (simplified)"""
        # This is a simplified version - in practice use rouge_score library
        rougem_l_scores = []
        for pred, ref in zip(predictions, references):
            if not pred and not ref:
                rougem_l_scores.append(1.0)
                continue
            if not pred or not ref:
                rougem_l_scores.append(0.0)
                continue

            # Simple LCS-based ROUGE-L
            lcs_length = self._longest_common_subsequence_length(
                pred.split(), ref.split()
            )
            precision = lcs_length / len(pred.split()) if len(pred.split()) > 0 else 0
            recall = lcs_length / len(ref.split()) if len(ref.split()) > 0 else 0
            if precision + recall == 0:
                f1 = 0.0
            else:
                f1 = 2 * (precision * recall) / (precision + recall)
            rougem_l_scores.append(f1)

        return {
            'rouge_l': np.mean(rougem_l_scores) if rougem_l_scores else 0.0
            # Simplified - real ROUGE has R-1, R-2, R-L
        }

    def _longest_common_subsequence_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Compute LCS length using dynamic programming"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        return dp[m][n]

    def _compute_bleu_score(self, predictions: List[str], references: List[str]) -> float:
        """Compute BLEU score (simplified)"""
        # Very simplified BLEU-1 implementation
        if not predictions or not references:
            return 0.0

        precisions = []
        for pred, ref in zip(predictions, references):
            pred_tokens = pred.lower().split()
            ref_tokens = ref.lower().split()

            if len(pred_tokens) == 0:
                precisions.append(0.0)
                continue

            # Count matches
            matches = sum(1 for token in pred_tokens if token in ref_tokens)
            precision = matches / len(pred_tokens) if len(pred_tokens) > 0 else 0
            precisions.append(precision)

        # Brevity penalty
        pred_lengths = [len(p.split()) for p in predictions]
        ref_lengths = [len(r.split()) for r in references]
        bp = 1.0
        if np.mean(pred_lengths) < np.mean(ref_lengths) and np.mean(ref_lengths) > 0:
            bp = np.exp(1 - np.mean(ref_lengths) / np.mean(pred_lengths))

        return bp * np.mean(precisions) if precisions else 0.0

    def _analyze_fairness(self, predictions: List[str], references: List[str], test_data: List[Dict]) -> Dict[str, Any]:
        """Analyze fairness and bias in predictions"""
        # This would require demographic information in test_data
        # For now, return placeholder structure
        return {
            'demographic_parity': 'Not implemented - requires demographic data',
            'equal_opportunity': 'Not implemented - requires demographic data',
            'disparate_impact': 'Not implemented - requires demographic data',
            'note': 'Fairness analysis requires protected attribute data in test set'
        }

    def _perform_error_analysis(self, predictions: List[str], references: List[str], test_data: List[Dict], inputs: List[str]) -> Dict[str, Any]:
        """Perform detailed error analysis"""
        errors = []
        for i, (pred, ref, inp) in enumerate(zip(predictions, references, inputs)):
            if pred.strip().lower() != ref.strip().lower():
                error_info = {
                    'index': i,
                    'input': inp[:100] + '...' if len(inp) > 100 else inp,
                    'expected': ref[:100] + '...' if len(ref) > 100 else ref,
                    'got': pred[:100] + '...' if len(pred) > 100 else pred,
                    'error_type': self._classify_error_type(pred, ref, inp),
                    'length_diff': len(pred.split()) - len(ref.split()) if ref.split() else len(pred.split())
                }
                errors.append(error_info)

        # Categorize errors
        error_types = Counter([e['error_type'] for e in errors])
        length_errors = [e for e in errors if abs(e['length_diff']) > 3]

        return {
            'total_errors': len(errors),
            'error_rate': len(errors) / len(predictions) if predictions else 0,
            'error_types': dict(error_types),
            'length_error_count': len(length_errors),
            'sample_errors': errors[:5]  # First 5 errors as examples
        }

    def _classify_error_type(self, prediction: str, reference: str, input_text: str) -> str:
        """Classify the type of error"""
        pred_lower = prediction.lower().strip()
        ref_lower = reference.lower().strip()

        if len(pred_split := prediction.split()) == 0:
            return 'empty_response'
        if len(pred_split) > len(ref_split := reference.split()) * 3:
            return 'overly_verbose'
        if len(pred_split) < len(ref_split) * 0.3:
            return 'too_brief'
        if any(word in pred_lower for word in ['i don\\'t know', 'unknown', 'not sure']) and \
           len(ref_split) > 2:
            return 'unhelpful_response'
        if len(set(pred_split)) / max(len(pred_split), 1) < 0.3:
            return 'repetitive'
        # Add more classifications as needed
        return 'other'

    def _analyze_stability(self, model, tokenizer, test_sample: List[Dict]) -> Dict[str, float]:
        """Analyze model stability under small perturbations"""
        if not test_sample:
            return {}

        # Test with slight variations in input
        variations = []
        for item in test_sample:
            original = item.get('input_text', '')
            if not original:
                continue

            # Create variations
            variants = [
                original + " ",  # Extra space
                " " + original,  # Leading space
                original.replace(".", "."),  # No change (control)
                original.replace(" ", "  ") if " " in original else original,  # Double spaces
            ]

            # Get predictions for each
            try:
                orig_pred = self._get_single_prediction(model, tokenizer, original)
                var_preds = [self._get_single_prediction(model, tokenizer, v) for v in variants if v != original]

                # Calculate similarity between original and variations
                if self.semantic_available and orig_pred:
                    from sklearn.metrics.pairwise import cosine_similarity
                    orig_emb = self.semantic_model.encode([orig_pred])
                    similarities = []
                    for var_pred in var_preds:
                        if var_pred:
                            var_emb = self.semantic_model.encode([var_pred])
                            sim = cosine_similarity(orig_emb, var_emb)[0][0]
                            similarities.append(sim)
                    avg_similarity = np.mean(similarities) if similarities else 0
                    variations.append(1 - avg_similarity)  # Dissimilarity as instability measure
            except Exception as e:
                logger.warning(f"Error in stability analysis: {e}")
                continue

        avg_instability = np.mean(variations) if variations else 0
        return {
            'stability_score': 1 - min(avg_instability, 1.0),  # Higher is more stable
            'average_variation_effect': round(avg_instability, 4)
        }

    def _estimate_uncertainty(self, model, tokenizer, test_sample: List[Dict]) -> Dict[str, float]:
        """Estimate model uncertainty using entropy or ensemble methods"""
        if not test_sample:
            return {}

        entropies = []
        for item in test_sample[:5]:  # Limit to avoid excessive computation
            text = item.get('input_text', '')
            if not text:
                continue

            try:
                inputs = tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                )

                with torch.no_grad():
                    outputs = model(**inputs, output_hidden_states=True)
                    # Get logits for last token
                    logits = outputs.logits[0, -1, :]
                    probs = torch.softmax(logits, dim=-1)
                    # Calculate entropy
                    entropy = -torch.sum(probs * torch.log(probs + 1e-10)).item()
                    entropies.append(entropy)
            except Exception as e:
                logger.warning(f"Error estimating uncertainty: {e}")
                continue

        avg_entropy = np.mean(entropies) if entropies else 0
        # Normalize entropy (max entropy for vocab size)
        vocab_size = getattr(model.config, 'vocab_size', 50000) if hasattr(model, 'config') else 50000
        max_entropy = np.log(vocab_size)
        normalized_entropy = avg_entropy / max_entropy if max_entropy > 0 else 0

        return {
            'average_entropy': round(avg_entropy, 4),
            'normalized_uncertainty': round(normalized_entropy, 4),
            'confidence_score': round(1 - normalized_entropy, 4)
        }

    def _get_single_prediction(self, model, tokenizer, text: str) -> str:
        """Get a single prediction from the model"""
        try:
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=min(512, inputs['input_ids'].shape[1] + 20),
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )

                input_length = inputs['input_ids'].shape[1]
                generated_tokens = outputs[0][input_length:]
                return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        except Exception as e:
            logger.warning(f"Error getting prediction: {e}")
            return ""

    def _save_evaluation_report(self, results: Dict[str, Any]):
        """Save evaluation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"evaluation_{results['task_type']}_{timestamp}.json"

        # Convert numpy types to native Python for JSON serialization
        def convert_for_json(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(i) for i in obj]
            else:
                return obj

        serializable_results = convert_for_json(results)

        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)

        logger.info(f"Evaluation report saved to {filename}")

    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate trends from evaluation history"""
        if len(self.evaluation_history) < 2:
            return {}

        # Extract metrics over time
        metrics_over_time = defaultdict(list)
        timestamps = []

        for entry in self.evaluation_history:
            timestamps.append(datetime.fromisoformat(entry['timestamp']))
            for metric_name, value in entry['metrics'].items():
                if isinstance(value, (int, float)):
                    metrics_over_time[metric_name].append(value)

        # Calculate trends (simple linear regression slope)
        trends = {}
        for metric_name, values in metrics_over_time.items():
            if len(values) >= 2:
                x = np.arange(len(values))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                trends[metric_name] = {
                    'slope': round(slope, 6),
                    'r_squared': round(r_value**2, 4),
                    'p_value': round(p_value, 4),
                    'direction': 'improving' if slope > 0 else 'declining' if slope < 0 else 'stable',
                    'significance': 'significant' if p_value < 0.05 else 'not_significant'
                }

        return {
            'trends': trends,
            'evaluation_count': len(self.evaluation_history),
            'time_span_hours': (timestamps[-1] - timestamps[0]).total_seconds() / 3600 if len(timestamps) >= 2 else 0
        }

# Global evaluation instance
evaluator = None

def get_evaluator() -> EvaluationIntelligence:
    """Get or create the global evaluator instance"""
    global evaluator
    if evaluator is None:
        evaluator = EvaluationIntelligence()
    return evaluator

def init_evaluator(output_dir: str = "./eval/reports") -> EvaluationIntelligence:
    """Initialize the evaluator with custom output directory"""
    global evaluator
    evaluator = EvaluationIntelligence(output_dir)
    return evaluator

# Convenience functions
def quick_evaluate(model, tokenizer, test_data: List[Dict], task_type: str = "general") -> Dict[str, Any]:
    """Quick evaluation function"""
    evaluator = get_evaluator()
    return evaluator.evaluate_model_comprehensive(model, tokenizer, test_data, task_type)

# Example usage
if __name__ == "__main__":
    print("Evaluation Intelligence System for LBOS-AI")
    print("==========================================")

    # This would normally be called with actual model, tokenizer, and data
    print("Ready to evaluate models with comprehensive metrics including:")
    print("- Basic accuracy metrics")
    print("- Task-specific metrics (QA, summarization, translation)")
    print("- Linguistic quality metrics")
    print("- Semantic similarity (when sentence-transformers available)")
    print("- Error analysis")
    print("- Stability analysis")
    print("- Uncertainty estimation")
    print("- Fairness analysis")
    print("- Trend tracking over time")