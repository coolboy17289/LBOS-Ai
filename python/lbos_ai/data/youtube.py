"""
YouTube ingestion module for LBOS-AI
Handles downloading YouTube videos, extracting audio, and transcribing speech
"""
import os
import json
import uuid
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import yt_dlp
import whisper

# Configure logging
logger = logging.getLogger(__name__)

class YouTubeIngestor:
    def __init__(self, output_dir: str = "./data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Whisper model (small for balance of speed/accuracy)
        # In production, this could be configurable or use Whisper.cpp via subprocess
        self.whisper_model = None
        self._init_whisper()

    def _init_whisper(self):
        """Initialize Whisper model for transcription"""
        try:
            # Use tiny model for faster loading in demo
            # In production, use base or small, or use Whisper.cpp for better performance
            self.whisper_model = whisper.load_model("tiny")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model: {e}. Will use fallback.")
            self.whisper_model = None

    def download_audio(self, url: str, job_id: str) -> str:
        """
        Download audio from YouTube video

        Args:
            url: YouTube URL
            job_id: Unique job identifier

        Returns:
            Path to downloaded audio file
        """
        try:
            output_template = str(self.output_dir / f"{job_id}_%(title)s.%(ext)s")

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Find the downloaded file
                filename = ydl.prepare_filename(info)
                # Change extension to wav due to postprocessing
                audio_file = os.path.splitext(filename)[0] + '.wav'

                if not os.path.exists(audio_file):
                    # Try to find the file with different extensions
                    for ext in ['.wav', '.mp3', '.m4a']:
                        test_file = os.path.splitext(filename)[0] + ext
                        if os.path.exists(test_file):
                            audio_file = test_file
                            break

                logger.info(f"Audio downloaded to: {audio_file}")
                return audio_file

        except Exception as e:
            logger.error(f"Failed to download audio from {url}: {e}")
            raise

    def transcribe_audio(self, audio_file: str) -> str:
        """
        Transcribe audio file to text using Whisper

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        try:
            if self.whisper_model:
                result = self.whisper_model.transcribe(audio_file)
                return result["text"].strip()
            else:
                # Fallback: use Whisper.cpp via subprocess if available
                return self._transcribe_with_whisper_cpp(audio_file)

        except Exception as e:
            logger.error(f"Transcription failed for {audio_file}: {e}")
            raise

    def _transcribe_with_whisper_cpp(self, audio_file: str) -> str:
        """
        Transcribe using Whisper.cpp (if available)
        """
        try:
            # This would call the Whisper.cpp binary
            # For now, we'll simulate or raise NotImplementedError
            raise NotImplementedError("Whisper.cpp integration not implemented in this demo")
        except Exception as e:
            logger.error(f"Whisper.cpp transcription failed: {e}")
            raise

    def get_video_info(self, url: str) -> dict:
        """
        Extract video metadata without downloading

        Args:
            url: YouTube URL

        Returns:
            Dictionary with video metadata
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'uploader': info.get('uploader', ''),
                    'tags': info.get('tags', []),
                    'categories': info.get('categories', []),
                    'thumbnail': info.get('thumbnail', '')
                }
        except Exception as e:
            logger.error(f"Failed to extract info from {url}: {e}")
            return {}

    def process_url(self, url: str, job_id: str) -> dict:
        """
        Process a YouTube URL: download audio, transcribe, extract metadata

        Args:
            url: YouTube URL
            job_id: Unique job identifier

        Returns:
            Dictionary with processed data
        """
        try:
            logger.info(f"Processing YouTube URL: {url} (job: {job_id})")

            # Get video metadata
            video_info = self.get_video_info(url)

            # Download audio
            audio_file = self.download_audio(url, job_id)

            # Transcribe audio
            transcript = self.transcribe_audio(audio_file)

            # Clean up audio file (optional)
            # os.remove(audio_file)

            # Create result
            result = {
                'id': f'yt_{job_id}',
                'source_url': url,
                'title': video_info.get('title', 'Unknown Title'),
                'transcript': transcript,
                'metadata': {
                    'duration': video_info.get('duration', 0),
                    'view_count': video_info.get('view_count', 0),
                    'upload_date': video_info.get('upload_date', ''),
                    'uploader': video_info.get('uploader', ''),
                    'tags': video_info.get('tags', []),
                    'categories': video_info.get('categories', []),
                    'thumbnail': video_info.get('thumbnail', '')
                }
            }

            logger.info(f"YouTube processing completed for job {job_id}")
            return result

        except Exception as e:
            logger.error(f"YouTube processing failed for job {job_id}: {e}")
            raise

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python youtube.py <URL> <JOB_ID>")
        sys.exit(1)

    url = sys.argv[1]
    job_id = sys.argv[2]

    ingestor = YouTubeIngestor()
    result = ingestor.process_url(url, job_id)
    print(json.dumps(result, indent=2))