"""
Dataset builder module for LBOS-AI
Combines cleaned text into structured datasets for training
"""
import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

class DatasetBuilder:
    def __init__(self, raw_data_dir: str = "./data/raw",
                 processed_data_dir: str = "./data/processed"):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def _generate_id(self, prefix: str, content: str) -> str:
        """
        Generate a unique ID based on content hash

        Args:
            prefix: ID prefix (e.g., 'yt', 'web')
            content: Content to hash

        Returns:
            Unique identifier string
        """
        hash_object = hashlib.md5(content.encode())
        hex_dig = hash_object.hexdigest()[:8]
        return f"{prefix}_{hex_dig}"

    def _clean_and_chunk_text(self, text: str, max_chunk_size: int = 512) -> List[str]:
        """
        Clean text and split into chunks for processing

        Args:
            text: Input text
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Clean text
        cleaner = TextCleaner()
        cleaned = cleaner.clean_text(text)

        # Split into sentences (simplified)
        sentences = re.split(r'[.!?]+', cleaned)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Group sentences into chunks
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 < max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def generate_qa_pairs(self, text: str, num_pairs: int = 5) -> List[Dict[str, str]]:
        """
        Generate question-answer pairs from text (simplified approach)
        In production, use more sophisticated QA generation models

        Args:
            text: Source text
            num_pairs: Number of QA pairs to generate

        Returns:
            List of question-answer dictionaries
        """
        if not text or len(text.strip()) < 50:
            return []

        # Simple approach: extract sentences and create cloze questions
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if len(sentences) < 2:
            return []

        qa_pairs = []
        # Use first few sentences as context, generate questions about them
        for i in range(min(num_pairs, len(sentences) - 1)):
            context = sentences[i]
            # Simple question: "What is [subject]?" - very basic
            # In production, use a proper QA generation model
            words = context.split()
            if len(words) > 3:
                # Create a simple fill-in-the-blank question
                blank_index = len(words) // 2
                answer = words[blank_index]
                question_words = words.copy()
                question_words[blank_index] = "_____"
                question = " ".join(question_words)

                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'context': context
                })

        return qa_pairs

    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text (simplified TF-IDF approach)
        In production, use proper NLP libraries like spaCy or KeyBERT

        Args:
            text: Source text
            num_keywords: Number of keywords to extract

        Returns:
            List of keywords
        """
        if not text:
            return []

        # Simple approach: extract nouns and proper nouns
        # In production, use POS tagging or TF-IDF
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        words = [w for w in words if w not in stop_words]

        # Count frequency
        from collections import Counter
        word_counts = Counter(words)
        # Get most common words
        keywords = [word for word, count in word_counts.most_common(num_keywords)]

        return keywords

    def process_raw_item(self, raw_item: Dict) -> Optional[Dict]:
        """
        Process a single raw item from ingestion

        Args:
            raw_item: Raw item from ingestion (YouTube or web)

        Returns:
            Processed item ready for training, or None if invalid
        """
        try:
            # Extract required fields
            item_id = raw_item.get('id')
            source_url = raw_item.get('source_url')
            title = raw_item.get('title', '')
            transcript = raw_item.get('transcript', '')
            metadata = raw_item.get('metadata', {})

            if not transcript or len(transcript.strip()) < 50:
                logger.warning(f"Skipping item {item_id}: transcript too short")
                return None

            # Clean transcript
            cleaner = TextCleaner()
            cleaned_transcript = cleaner.clean_text(transcript)

            if not cleaned_transcript or len(cleaned_transcript.strip()) < 50:
                logger.warning(f"Skipping item {item_id}: cleaned transcript too short")
                return None

            # Generate QA pairs
            qa_pairs = self.generate_qa_pairs(cleaned_transcript)

            # Extract keywords/topics
            keywords = self.extract_keywords(cleaned_transcript)

            # Create processed item
            processed_item = {
                'id': item_id,
                'source_url': source_url,
                'title': title,
                'transcript': cleaned_transcript,
                'summary': self._generate_summary(cleaned_transcript),
                'qa_pairs': qa_pairs,
                'keywords': keywords,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'metadata': {
                    **metadata,
                    'processed_length': len(cleaned_transcript),
                    'qa_pairs_count': len(qa_pairs),
                    'keywords_count': len(keywords)
                }
            }

            return processed_item

        except Exception as e:
            logger.error(f"Error processing raw item {raw_item.get('id', 'unknown')}: {e}")
            return None

    def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a simple summary by extracting first few sentences
        In production, use proper summarization models

        Args:
            text: Source text
            max_sentences: Maximum number of sentences for summary

        Returns:
            Summary text
        """
        if not text:
            return ""

        # Simple approach: take first few sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return ""

        summary = ' '.join(sentences[:max_sentences])
        return summary.strip()

    def save_processed_item(self, item: Dict, output_dir: Optional[Path] = None) -> Path:
        """
        Save processed item to JSONL file

        Args:
            item: Processed item dictionary
            output_dir: Optional custom output directory

        Returns:
            Path to saved file
        """
        if output_dir is None:
            output_dir = self.processed_data_dir

        # Create daily directory
        today = datetime.utcnow().strftime('%Y-%m-%d')
        daily_dir = output_dir / today
        daily_dir.mkdir(parents=True, exist_ok=True)

        # Create filename based on hour
        hour = datetime.utcnow().strftime('%H')
        filename = f"dataset_{hour}.jsonl"
        filepath = daily_dir / filename

        # Write as JSONL
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

        logger.info(f"Saved processed item {item['id']} to {filepath}")
        return filepath

    def process_batch(self, raw_items: List[Dict]) -> List[Dict]:
        """
        Process a batch of raw items

        Args:
            raw_items: List of raw items from ingestion

        Returns:
            List of processed items
        """
        processed_items = []
        for item in raw_items:
            processed = self.process_raw_item(item)
            if processed:
                processed_items.append(processed)

        logger.info(f"Processed {len(processed_items)} out of {len(raw_items)} raw items")
        return processed_items

    def get_training_dataset(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Load processed dataset for training

        Args:
            limit: Maximum number of items to return

        Returns:
            List of processed items from storage
        """
        dataset = []

        # Walk through processed data directory
        for root, dirs, files in os.walk(self.processed_data_dir):
            for file in files:
                if file.endswith('.jsonl'):
                    filepath = Path(root) / file
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    item = json.loads(line)
                                    dataset.append(item)
                                    if limit and len(dataset) >= limit:
                                        return dataset
                    except Exception as e:
                        logger.error(f"Error reading {filepath}: {e}")

        return dataset

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python dataset_builder.py '<json_file>'")
        sys.exit(1)

    json_file = sys.argv[1]

    with open(json_file, 'r') as f:
        raw_items = json.load(f)

    builder = DatasetBuilder()
    processed = builder.process_batch(raw_items)

    for item in processed:
        builder.save_processed_item(item)

    print(f"Processed {len(processed)} items")