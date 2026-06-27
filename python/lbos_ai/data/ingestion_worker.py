"""
Ingestion worker for LBOS-AI
Called by Node.js job processor to ingest YouTube and web content
"""
import sys
import json
import logging
import os
from pathlib import Path
from .youtube import YouTubeIngestor
from .web import WebIngestor
from .dataset_builder import DatasetBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 4:
        print("Usage: python ingestion_worker.py <URL> <JOB_ID> <TYPE>")
        sys.exit(1)

    url = sys.argv[1]
    job_id = sys.argv[2]
    content_type = sys.argv[3]  # 'youtube', 'web', or 'auto'

    try:
        # Initialize ingestors
        youtube_ingestor = YouTubeIngestor()
        web_ingestor = WebIngestor()
        builder = DatasetBuilder()

        # Determine content type
        if content_type == 'auto':
            # Simple URL-based detection
            if 'youtube.com' in url or 'youtu.be' in url:
                content_type = 'youtube'
            else:
                content_type = 'web'

        # Process based on type
        if content_type == 'youtube':
            result = youtube_ingestor.process_url(url, job_id)
        elif content_type == 'web':
            result = web_ingestor.process_url(url, job_id)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        # Save raw result
        raw_dir = Path("./data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / f"{job_id}.json"
        with open(raw_file, 'w') as f:
            json.dump(result, f, indent=2)

        # Process into dataset
        processed_item = builder.process_raw_item(result)
        if processed_item:
            builder.save_processed_item(processed_item)
            logger.info(f"Successfully processed and saved item for job {job_id}")
            print(json.dumps({"status": "success", "job_id": job_id}))
        else:
            logger.warning(f"Content processed but no valid data extracted for job {job_id}")
            print(json.dumps({"status": "warning", "job_id": job_id, "message": "No extractable content"}))

    except Exception as e:
        logger.error(f"Error in ingestion worker for job {job_id}: {e}")
        print(json.dumps({"status": "error", "job_id": job_id, "message": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()