"""
Web article ingestion module for LBOS-AI
Handles fetching and extracting text from web articles
"""
import os
import json
import uuid
import logging
import requests
from pathlib import Path
from typing import Dict, Optional
from newspaper import Article
from readability import Document
import bs4

# Configure logging
logger = logging.getLogger(__name__)

class WebIngestor:
    def __init__(self, output_dir: str = "./data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configure requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_article(self, url: str) -> str:
        """
        Fetch HTML content from URL

        Args:
            url: Article URL

        Returns:
            HTML content as string
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

    def extract_article_text(self, html: str, url: str) -> dict:
        """
        Extract article text and metadata from HTML

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Dictionary with title, text, and metadata
        """
        try:
            # Try newspaper3k first (most robust)
            article = Article(url)
            article.set_html(html)
            article.parse()

            if article.text and len(article.text.strip()) > 100:
                return {
                    'title': article.title or 'Untitled',
                    'text': article.text.strip(),
                    'authors': article.authors,
                    'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                    'top_image': article.top_image,
                    'images': article.images,
                    'movies': article.movies,
                    'keywords': article.keywords
                }
        except Exception as e:
            logger.warning(f"newspaper3k failed for {url}: {e}")

        try:
            # Fallback to readability-lxml
            doc = Document(html)
            title = doc.short_title()
            summary = doc.summary()

            # Parse summary with BeautifulSoup to get clean text
            soup = bs4.BeautifulSoup(summary, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)

            if len(text) > 100:
                return {
                    'title': title or 'Untitled',
                    'text': text,
                    'authors': [],
                    'publish_date': None,
                    'top_image': None,
                    'images': [],
                    'movies': [],
                    'keywords': []
                }
        except Exception as e:
            logger.warning(f"readability-lxml failed for {url}: {e}")

        # Last resort: extract all text from body
        try:
            soup = bs4.BeautifulSoup(html, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator=' ', strip=True)

            # Try to get title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else 'Untitled'

            if len(text) > 100:
                return {
                    'title': title,
                    'text': text,
                    'authors': [],
                    'publish_date': None,
                    'top_image': None,
                    'images': [],
                    'movies': [],
                    'keywords': []
                }
        except Exception as e:
            logger.error(f"All extraction methods failed for {url}: {e}")

        # If all else fails, return minimal data
        return {
            'title': 'Extraction Failed',
            'text': 'Could not extract content from the provided URL.',
            'authors': [],
            'publish_date': None,
            'top_image': None,
            'images': [],
            'movies': [],
            'keywords': []
        }

    def process_url(self, url: str, job_id: str) -> dict:
        """
        Process a web article URL: fetch, extract text, and prepare for storage

        Args:
            url: Article URL
            job_id: Unique job identifier

        Returns:
            Dictionary with processed data
        """
        try:
            logger.info(f"Processing web URL: {url} (job: {job_id})")

            # Fetch HTML content
            html = self.fetch_article(url)

            # Extract article text and metadata
            article_data = self.extract_article_text(html, url)

            # Create result
            result = {
                'id': f'web_{job_id}',
                'source_url': url,
                'title': article_data['title'],
                'transcript': article_data['text'],  # Using same field name as YouTube for consistency
                'metadata': {
                    'authors': article_data['authors'],
                    'publish_date': article_data['publish_date'],
                    'top_image': article_data['top_image'],
                    'image_count': len(article_data['images']),
                    'movie_count': len(article_data['movies']),
                    'keywords': article_data['keywords'],
                    'content_length': len(article_data['text'])
                }
            }

            logger.info(f"Web processing completed for job {job_id}")
            return result

        except Exception as e:
            logger.error(f"Web processing failed for job {job_id}: {e}")
            raise

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python web.py <URL> <JOB_ID>")
        sys.exit(1)

    url = sys.argv[1]
    job_id = sys.argv[2]

    ingestor = WebIngestor()
    result = ingestor.process_url(url, job_id)
    print(json.dumps(result, indent=2))