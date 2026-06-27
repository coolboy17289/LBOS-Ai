"""
Text cleaning module for LBOS-AI
Handles cleaning and preprocessing of text data
"""
import re
import logging
from typing import List, Optional
import unicodedata
import ftfy
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self):
        # Compile regex patterns for efficiency
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.multiple_spaces = re.compile(r'\s+')
        self.multiple_newlines = re.compile(r'\n\s*\n')
        self.special_chars = re.compile(r'[^\w\s\.,!?\-:;\"\'()]')
        self.html_tags = re.compile(r'<[^>]+>')

    def clean_text(self, text: str,
                   fix_encoding: bool = True,
                   remove_html: bool = True,
                   remove_urls: bool = True,
                   remove_emails: bool = True,
                   remove_phones: bool = True,
                   normalize_whitespace: bool = True,
                   remove_special_chars: bool = False) -> str:
        """
        Clean and normalize text

        Args:
            text: Input text to clean
            fix_encoding: Fix text encoding issues
            remove_html: Remove HTML tags
            remove_urls: Remove URLs
            remove_emails: Remove email addresses
            remove_phones: Remove phone numbers
            normalize_whitespace: Normalize whitespace
            remove_special_chars: Remove special characters (keep only alphanumeric and basic punctuation)

        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""

        try:
            # Fix encoding issues
            if fix_encoding:
                text = ftfy.fix_text(text)

            # Remove HTML tags
            if remove_html:
                text = self.html_tags.sub('', text)

            # Remove URLs
            if remove_urls:
                text = self.url_pattern.sub('', text)

            # Remove email addresses
            if remove_emails:
                text = self.email_pattern.sub('', text)

            # Remove phone numbers
            if remove_phones:
                text = self.phone_pattern.sub('', text)

            # Remove special characters (optional)
            if remove_special_chars:
                text = self.special_chars.sub('', text)

            # Normalize whitespace
            if normalize_whitespace:
                # Replace multiple spaces with single space
                text = self.multiple_spaces.sub(' ', text)
                # Replace multiple newlines with double newline
                text = self.multiple_newlines.sub('\n\n', text)
                # Strip leading/trailing whitespace
                text = text.strip()

            return text

        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            # Return original text on error to avoid data loss
            return text

    def clean_batch(self, texts: list, **kwargs) -> list:
        """
        Clean a batch of texts

        Args:
            texts: List of text strings
            **kwargs: Arguments to pass to clean_text

        Returns:
            List of cleaned text strings
        """
        return [self.clean_text(text, **kwargs) for text in texts]

    def detect_language(self, text: str) -> str:
        """
        Simple language detection (English vs non-English)
        For production, consider using langdetect or fastText

        Args:
            text: Input text

        Returns:
            Language code ('en' for English, 'unknown' otherwise)
        """
        # Simple heuristic: check if most common words are English
        common_english = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i'}
        words = set(re.findall(r'\b\w+\b', text.lower()))
        if not words:
            return 'unknown'

        match_ratio = len(words & common_english) / len(words)
        return 'en' if match_ratio > 0.3 else 'unknown'

    def is_boilerplate(self, text: str, threshold: float = 0.3) -> bool:
        """
        Detect if text is likely boilerplate (navigation, footer, etc.)

        Args:
            text: Text to analyze
            threshold: Threshold for boilerplate score

        Returns:
            True if likely boilerplate
        """
        if not text or len(text.strip()) < 20:
            return True

        # Check for common boilerplate patterns
        boilerplate_indicators = [
            r'copyright',
            r'all rights reserved',
            r'terms of service',
            r'privacy policy',
            r'contact us',
            r'about us',
            r'follow us',
            r'subscribe',
            rss feed',
            r'javascript must be enabled',
            r'cookie policy'
        ]

        text_lower = text.lower()
        matches = sum(1 for pattern in boilerplate_indicators if re.search(pattern, text_lower))
        score = min(matches / len(boilerplate_indicators), 1.0)

        return score > threshold

    def remove_boilerplate(self, text: str) -> str:
        """
        Remove boilerplate text from content

        Args:
            text: Input text

        Returns:
            Text with boilerplate removed
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and not self.is_boilerplate(line):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python text_cleaner.py '<text>'")
        sys.exit(1)

    text = sys.argv[1]
    cleaner = TextCleaner()
    cleaned = cleaner.clean_text(text)
    print("Original:", text)
    print("Cleaned:", cleaned)