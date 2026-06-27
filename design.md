# LBOS-AI System Architecture Design

## High-Level Goal Summary
LBOS-AI is an end-to-end pipeline for ingesting multimedia content (YouTube videos and web articles), processing it into a structured dataset, training a custom lightweight language model, and evaluating the model's performance using R and MATLAB-based analytics. The system is designed to be modular, language-agnostic where possible, and deployable as a self-contained package without runtime dependencies on large language models (LLMs). The primary goal is to enable autonomous knowledge acquisition and reasoning from web-scale multimedia content for domain-specific AI applications.

## Language Selection Justification
- **Python (3.9+)**: Primary language for data processing, dataset generation, and model training due to its rich ecosystem (PyTorch, HuggingFace, pandas, scikit-learn, NLTK, spaCy, pytube, newspaper3k, etc.).
- **Node.js (18.x)**: Backend API gateway and WebSocket server for real-time communication with the frontend, chosen for its non-blocking I/O and extensive npm ecosystem.
- **React (18.x) with TypeScript**: Frontend control panel for its reactivity, component reusability, and strong typing for complex UI state management.
- **Java (17+)**: Orchestration layer (orchestrator service) for workflow coordination, service orchestration, and process management due to its maturity, concurrency model, and enterprise-grade reliability.
- **C++ (17)**: Performance-critical components in the data preprocessing pipeline (e.g., video frame extraction, audio processing via FFmpeg bindings) where low-level control is beneficial.
- **R (4.2+)**: Statistical analysis and visualization in the evaluation pipeline (optional, for statistical reporting).
- **MATLAB (R2023a)**: Advanced signal processing and model evaluation (optional, for domains requiring specialized toolboxes).

**Languages Removed/Justification**:
- **Python 2**: Deprecated, security risks, lack of modern library support.
- **Ruby/Perl**: Lack of ML/NLP ecosystem maturity compared to Python.
- **.NET**: Cross-platform improvements noted but ecosystem mismatch with primary ML stack.
- **Go**: Excellent for microservices but less mature for rapid ML prototyping compared to Python.

## Full Pipeline Flow
1. **URL Ingestion**: 
   - Input: YouTube URLs or web article URLs via frontend or API.
   - Process: 
     - YouTube: Audio/video download via `pytube`/`yt-dlp`, audio extraction via `ffmpeg` (C++ bindings), speech-to-text via Whisper.cpp (C++).
     - Web Articles: HTML fetch via `axios` (Node.js) or `requests` (Python), text extraction via `newspaper3k` or `boilerpy3`.
   - Output: Raw text transcripts and metadata stored as JSONL in `/data/raw/`.

2. **Dataset Generation**:
   - Input: Raw transcripts/metadata from ingestion.
   - Process:
     - Text cleaning (boilerplate removal, deduplication) with `newspaper3k`/`boilerpy3`.
     - Sentence segmentation via `spaCy` or `nltk`.
     - Topic modeling (LDA/BERTopic) for categorization.
     - Summary generation via extractive (TextRank) or abstractive (PEGASUS) methods.
     - Q&A pair generation via rule-based or lightweight seq2seq models.
   - Output: Structured dataset (JSONL) in `/data/processed/` with fields: `id`, `source_url`, `title`, `transcript`, `summary`, `qa_pairs`, `topics`, `timestamp`.

3. **Training**:
   - Input: Processed dataset from `/data/processed/`.
   - Process:
     - Tokenization with HuggingFace tokenizers (fast tokenizers in Rust via Python bindings).
     - Model: Custom transformer architecture (encoder-only or encoder-decoder) trained from scratch using PyTorch, sized for efficiency (e.g., DistilBERT-scale).
     - Objective: Masked language modeling (MLM) or sequence-to-sequence loss.
     - Optimization: AdamW with learning rate scheduler.
     - Hardware: GPU-accelerated (CUDA) if available, else CPU fallback.
   - Output: Model checkpoints in `/models/` and training logs.

4. **Evaluation**:
   - Input: Trained model and held-out test set.
   - Process:
     - Perplexity calculation via PyTorch.
     - Downstream task evaluation (e.g., question answering accuracy) using custom scripts.
     - Statistical analysis (R) for significance testing.
     - Signal processing analysis (MATLAB optional) for audio-derived features.
   - Output: Evaluation reports (JSON/HTML) in `/eval/reports/`.

## Data Movement Between Services
- **Ingestion → Dataset Generation**: JSONL files written to shared volume (`/data/raw/` → `/data/processed/`) via shared filesystem (NFS or host-mounted volume in Docker/K8s).
- **Dataset Generation → Training**: Processed dataset consumed directly from `/data/processed/` by Python training script.
- **Training → Evaluation**: Model checkpoints copied to `/models/`; evaluation script reads from there and test set from `/data/processed/test/`.
- **Evaluation → Frontend**: Evaluation reports served via Node.js API gateway as static files or via WebSocket for real-time updates.
- **Orchestration**: Java orchestrator service coordinates via lightweight HTTP gateway (Node.js) or direct JDBC/JDBC-like calls to services (if containerized, uses Docker SDK or Kubernetes API).

## Communication Method Chosen
**Lightweight HTTP Gateway (Node.js) + WebSocket for Real-Time Updates**
- **Why not pure IPC**: Services may be containerized or distributed; IPC (e.g., Unix sockets) lacks network transparency.
- **Why not pure HTTP**: WebSocket provides low-latency duplex streaming for frontend updates (e.g., training progress, log streaming).
- **Implementation**:
  - Node.js API gateway exposes REST endpoints for job submission, status, and result retrieval.
  - WebSocket endpoint (`/ws/progress`) streams logs and metrics from Python/Java services via the gateway.
  - Internal service communication uses HTTP/JSON for simplicity and observability.
  - File-based JSONL used for bulk data transfer (datasets, model checkpoints) due to efficiency with large binary/blob data.

## URL Ingestion Pipeline Details
### YouTube Ingestion
1. **Input**: YouTube URL via frontend/API.
2. **Download**: `yt-dlp` (Python wrapper) or `youtube-dl` downloads best audio/video format.
3. **Audio Extraction**: `ffmpeg` (via `ffmpeg-python` or direct subprocess) extracts mono-channel audio at 16kHz.
4. **Speech-to-Text**: 
   - Primary: Whisper.cpp (C++ inference engine) for fast, offline transcription.
   - Fallback: Whisper (Python) or Vosk for lower latency.
5. **Metadata Extraction**: Video title, description, duration, upload date via YouTube Data API (cached).
6. **Output**: JSONL line: `{"id": "yt_<hash>", "source_url": "...", "title": "...", "transcript": "...", "metadata": {...}}`

### Web Article Ingestion
1. **Input**: Article URL.
2. **Fetch**: `axios` (Node.js) or `requests` (Python) with retry and timeout.
3. **HTML Parsing**: `newspaper3k` (Python) or `boilerpy3` extracts main article text, title, publish date, authors.
4. **Fallback**: `readability-lxml` or `jusText` if primary fails.
5. **Output**: JSONL line: `{"id": "web_<hash>", "source_url": "...", "title": "...", "transcript": "<article_text>", "metadata": {...}}`

## Training Pipeline Details
- **Custom Model Architecture**: 
  - Based on DistilBERT-base architecture (6 layers, 768 hidden, 12 heads) for efficiency.
  - Customizable via config (layers, hidden size, attention heads).
  - Trained from scratch (no pretrained weights) to avoid LLM dependency and ensure data provenance.
- **Training Process**:
  - Data Loader: PyTorch `DataLoader` with dynamic batching.
  - Loss: Masked Language Modeling (MLM) with 15% token masking.
  - Optimizer: AdamW (lr=5e-5, weight_decay=0.01).
  - Scheduler: Linear warmup + cosine decay.
  - Early Stopping: Based on validation loss.
  - Checkpointing: Best model saved by validation loss.
- **No Runtime LLM Dependency**: Model is self-contained; inference uses only PyTorch and the model weights.
- **Hardware Utilization**: 
  - Automatic GPU detection (CUDA). Falls back to CPU.
  - Mixed precision training (AMP) if GPU supports.
  - Multi-GPU via `torch.distributed` if available.

## Evaluation System Details
### Core Evaluation (Python/PyTorch)
- **Perplexity**: Standard metric on held-out test set.
- **Accuracy**: For QA tasks, exact match and F1 score.
- **Loss Curves**: Plotted via `matplotlib` (saved to `/eval/reports/loss_curve.png`).

### Optional R Module
- **Statistical Analysis**: 
  - Load evaluation metrics (CSV/JSON) via `readr`.
  - Perform t-tests/ANOVA comparing model variants.
  - Generate plots (`ggplot2`) for loss distribution, attention visualization.
- **Reporting**: Knit R Markdown to HTML/PDF.

### Optional MATLAB Module
- **Signal Processing**: If audio features are extracted (e.g., MFCCs, prosody), MATLAB toolboxes analyze:
  - Correlation between audio properties and model performance.
  - Spectral analysis of transcription errors.
- **Toolboxes Used**: Signal Processing Toolbox, Statistics and Machine Learning Toolbox.

### Evaluation Output
- JSON report: `{ "model_id": "...", "perplexity": 20.5, "qa_exact_match": 0.45, "qa_f1": 0.52, ... }`
- HTML report: Interactive plots via `plotly` (Python) or `ggplot2` (R).
- Stored in `/eval/reports/<timestamp>/`.

## Frontend (React TSX) Control Panel Components
- **Dashboard**: Overview of system health, recent jobs, model performance.
- **Ingestion Panel**: 
  - Input field for YouTube/article URLs (single or batch).
  - Progress bars for download/transcription/extraction.
  - Metadata preview (title, duration, etc.).
- **Training Panel**:
  - Dataset selector (from processed datasets).
  - Hyperparameter configurator (layers, lr, batch size, epochs).
  - Start/stop/pause training buttons.
  - Real-time loss/accuracy chart (using `react-chartjs-2` or `recharts`).
  - Log streaming pane (via WebSocket).
- **Evaluation Panel**:
  - Select model checkpoint and test dataset.
  - Run evaluation button.
  - Display metrics table and downloadable reports (JSON/HTML/PDF).
- **Settings Panel**:
  - API keys (YouTube, optional MATLAB/R paths).
  - Resource limits (GPU memory, CPU threads).
  - Storage paths (data, models, outputs).
- **Technology Stack**:
  - React 18.2.0, TypeScript 5.0+, Vite 4.0+ for fast HMR.
  - State Management: Zustand (lightweight) or React Query for server state.
  - UI Library: MUI v5 or Ant Design for professional components.
  - WebSocket: `socket.io-client` for real-time updates.
  - Charts: Recharts or Chart.js via react wrappers.

## Backend (Node.js) API Gateway and WebSocket Streaming
- **Framework**: Express.js 4.18+.
- **API Endpoints**:
  - `POST /ingest`: Accept URL(s), enqueue ingestion job, return job ID.
  - `GET /jobs/:id`: Get job status (queued, processing, completed, failed).
  - `GET /models`: List available model checkpoints.
  - `POST /train`: Start training job with config.
  - `POST /evaluate`: Start evaluation job.
  - `GET /eval/reports/:id`: Retrieve evaluation report.
  - `GET /logs/:job_id`: Stream logs via WebSocket (upgrade endpoint).
- **WebSocket Server**: 
  - `/ws/progress`: Bidirectional channel for real-time updates.
  - Services publish progress messages to Redis pub/sub (or in-memory if single instance); Node.js WebSocket server relays to connected clients.
- **Job Queue**: 
  - BullMQ (Redis-backed) for reliable job queuing and retries.
  - Job types: `ingest`, `train`, `evaluate`.
- **Security**: 
  - Rate limiting, input validation (URL sanitization).
  - JWT-based auth for future multi-user extension (currently assumed single-user/local).
- **File Serving**: 
  - Static serving of evaluation reports (`/eval/reports/` → `/public/reports/`).
  - Model checkpoints served via signed URLs (if needed for download).

## Java Orchestration Layer Responsibilities
- **Workflow Orchestration**: 
  - Define and manage DAGs (Directed Acyclic Graphs) of pipeline stages (ingest → process → train → evaluate).
  - Use Camunda BPM or custom lightweight orchestrator (Spring Boot + Activiti).
- **Service Coordination**:
  - Start/stop/monitor Python (data processing/training), Node.js (API), and optional R/MATLAB services.
  - Health checks and restart policies.
- **Resource Management**:
  - Allocate GPU/CPU resources to jobs (via nvidia-smi or OS-level cgroups).
  - Prevent over-subscription (e.g., only one training job per GPU).
- **Persistence**:
  - Job metadata stored in PostgreSQL (or SQLite for simplicity) via JDBC.
  - Track job inputs/outputs, status, logs, timestamps.
- **Error Handling**:
  - Retry policies with exponential backoff.
  - Dead-letter queue for failed jobs.
  - Alerting via email/webhook on repeated failures.
- **Technology Stack**:
  - Spring Boot 3.2+ (Java 17) for REST/gRPC services if needed.
  - Embedded Tomcat/Jetty.
  - Lombok for boilerplate reduction.
  - JPA/Hibernate for ORM.
  - Docker Java SDK or Kubernetes Java client for container orchestration.

## Python Training and Data Processing Specifics
### Data Processing (`lbos_ai/data/`):
- **Transcription**: `speech_to_text.py` wraps Whisper.cpp via `subprocess` or `ctranslate2` binding.
- **Text Cleaning**: `text_cleaner.py` uses `regex`, `ftfy`, `unicodedata`, and `boilerpipe3`.
- **Sentence Splitting**: `nltk.sent_tokenize` or `spacy` language model.
- **Q&A Generation**: 
  - Rule-based: Regex patterns for interrogative sentences.
  - Neural: Tiny T5 model (if accuracy required) but default is rule-based for speed.
- **Dataset Builder**: `dataset_builder.py` reads raw JSONL, applies pipeline, writes processed JSONL.

### Training (`lbos_ai/train/`):
- **Trainer**: `trainer.py` encapsulates PyTorch training loop.
- **Model**: `model.py` defines custom Transformer(nn.Module).
- **Tokenizer**: `tokenizer.py` loads/saves HuggingFace tokenizer (fast tokenizers from `tokenizers` library).
- **Data Loader**: `data_loader.py` creates `Dataset` and `DataLoader` with dynamic padding.
- **Utilities**: 
  - `utils.py`: seed setting, mixed precision, gradient clipping.
  - `metrics.py`: perplexity, accuracy calculation.
- **Configuration**: `config.yaml` for hyperparameters (loaded via `OmegaConf` or `yaml`).

### Dependencies (Key):
- `torch>=2.0.0`
- `transformers>=4.30.0` (for tokenizers only)
- `sentencepiece` (if using BPE)
- `accelerate>=0.20.0` (for multi-GPU)
- `yt-dlp>=2023.08.0`
- `whispercpp-python>=0.1.0` (or `git+https://github.com/ggerganov/whisper.cpp`)
- `newspaper3k>=0.2.8`
- `spacy>=3.5.0`
- `nltk>=3.8`
- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `pyyaml>=6.0`
- `tqdm>=4.65.0`
- `redis>=4.5.0` (for job queue)
- `python-dotenv>=1.0.0` (for env vars)

## C++ Role (If Any)
- **Whisper.cpp Integration**: 
  - Used for efficient, offline speech-to-text via C++ bindings.
  - Compiled as a shared library (`libwhisper.so`/`.dll`) and called via `ctypes` or `cffi` in Python.
  - Enables CPU-friendly transcription without GPU dependency.
- **FFmpeg Bindings**: 
  - Used via `ffmpeg-python` or direct subprocess calls for audio/video extraction.
  - No custom C++ code unless specific optimizations needed (e.g., custom filters).
- **Potential Future Use**: 
  - High-performance tokenization (e.g., `tokenizers` library is Rust-based, but C++ could be used for custom ops).
  - Accelerated inference via TensorRT or ONNX Runtime (C++ backend) — *optional, not in MVP*.

## R and MATLAB Specifics
### R (Optional)
- **Purpose**: Statistical validation and reporting.
- **Scripts**: 
  - `eval/r/analyze_results.R`: Reads evaluation JSON, computes confidence intervals, generates plots.
  - `eval/r/report.Rmd`: R Markdown template for dynamic reports.
- **Packages**: 
  - `tidyverse` (dplyr, ggplot2, readr, etc.)
  - `knitr`, `rmarkdown` for report generation.
  - `jsonlite` for JSON input.
  - `ggpubr` for publication-ready plots.
- **Execution**: Called via `Rscript` from Python/Java orchestrator.

### MATLAB (Optional)
- **Purpose**: Signal processing on audio features (if extracted).
- **Scripts**:
  - `eval/matlab/analyze_audio_features.m`: Processes MFCC, pitch, energy features from audio.
  - `eval/matlab/correlate_with_performance.m`: Links audio features to model error metrics.
- **Toolboxes Required**: 
  - Signal Processing Toolbox
  - Statistics and Machine Learning Toolbox
  - Curve Fitting Toolbox (optional)
- **Execution**: Called via `matlab -batch` from Python/Java; requires MATLAB Runtime (MCR) for deployment if no full MATLAB license.

## Repository Structure Confirmation
```
lbos-ai/
├── .claude/ Claude Code settings
├── .git/ Git metadata
├── design.md ← This file
├── main.md Miscellaneous notes
├── notescli/ Possibly legacy notes
├── README.md Project overview and setup
├── docker-compose.yml Optional: multi-service deployment
├── Dockerfile.base Base image for Python/services
├── Dockerfile.trainer GPU-enabled training image
├── Dockerfile.api Node.js API gateway
├── docker/
│   └── ... Docker-related configs
├── src/
│   ├── api/ Node.js API gateway and WebSocket server
│   │   ├── src/
│   │   │   ├── index.js Entry point
│   │   │   ├── routes/ API route handlers
│   │   │   ├── ws/ WebSocket logic
│   │   │   ├── jobs/ BullMQ job definitions
│   │   │   ├── middleware/ Auth, validation, etc.
│   │   │   └── utils/
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── orchestrator/ Java orchestration service (Spring Boot)
│   │   ├── src/
│   │   │   ├── main/java/com/lbos/orchestrator/
│   │   │   │   ├── OrchestratorApplication.java
│   │   │   │   ├── service/ JobService, ServiceManager
│   │   │   │   ├── repository/ JPA repositories
│   │   │   │   └── controller/ REST endpoints
│   │   │   └── resources/ application.properties, schema.sql
│   │   └── pom.xml
│   ├── python/ Core Python data processing and training
│   │   ├── lbos_ai/
│   │   │   ├── __init__.py
│   │   │   ├── data/ Ingestion and preprocessing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── youtube.py
        │   │   │   ├── web.py
        │   │   │   ├── text_cleaner.py
        │   │   │   └── dataset_builder.py
        │   │   ├── train/ Training loop, model, tokenizer
        │   │   │   ├── __init__.py
        │   │   │   ├── trainer.py
        │   │   │   ├── model.py
        │   │   │   ├── tokenizer.py
        │   │   │   ├── data_loader.py
        │   │   │   └── config.yaml
        │   │   ├── eval/ Evaluation scripts (Python core)
        │   │   │   ├── __init__.py
        │   │   │   ├── perplexity.py
        │   │   │   ├── qa_metrics.py
        │   │   │   └── report_generator.py
        │   │   └── utils/ Logging, config, hardware detection
        │   │       ├── __init__.py
        │   │       ├── logger.py
        │   │       ├── config.py
        │   │       └── hardware.py
        │   ├── requirements.txt
        │   └── setup.py
│   ├── cpp/ Optional C++ bindings (e.g., whisper.cpp wrapper)
│   │   ├── CMakeLists.txt
│   │   ├── src/
│   │   │   └── whisper_wrapper.cpp
        │   │   └── ...
        │   └── include/
        │       └── whisper_wrapper.h
│   ├── r/ Optional R scripts
│   │   ├── analyze_results.R
        │   └── report.Rmd
│   └── matlab/ Optional MATLAB scripts
        │   ├── analyze_audio_features.m
        │   └── correlate_with_performance.m
├── data/
│   ├── raw/ Ingestion output (JSONL)
│   ├── processed/ Cleaned, structured dataset (JSONL)
│   └── test/ Held-out test set (JSONL)
├── models/
│   └── <timestamp>/ Model checkpoints and config
├── eval/
│   └── reports/ Evaluation outputs (JSON, HTML, PDF)
├── logs/ Service logs (ingest, train, api, etc.)
├── configs/ Default configuration files (yaml, json, properties)
└── scripts/ Helper scripts (setup, download models, etc.)
```

## Installer Requirements
### Prerequisites
- **OS**: Ubuntu 22.04 LTS, Windows 10/11 (WSL2 recommended), or macOS 12+ (Intel/Apple Silicon; GPU support varies).
- **Hardware**: 
  - Minimum: 4 CPU cores, 8GB RAM, 20GB disk.
  - Recommended for training: 8+ CPU cores, 16GB+ RAM, NVIDIA GPU with 6GB+ VRAM (CUDA 11.8+), 50GB SSD.
- **Software**:
  - Docker Engine 24.0+ (for containerized deployment) **OR**
  - Direct installation dependencies:
    - Python 3.9-3.11
    - Node.js 18.x LTS
    - Java 17 OpenJDK or Oracle JDK
    - FFmpeg 5.0+ (with libx264, libfdk-aac, libmp3lame)
    - Optional: R 4.2+, MATLAB R2023a+ (with toolboxes)
    - Optional: NVIDIA Driver 525+ and CUDA Toolkit 11.8 (for GPU acceleration)

### Installation Methods
#### 1. Docker Compose (Recommended)
```bash
# Clone repo
git clone https://github.com/yourorg/lbos-ai.git
cd lbos-ai

# Copy example env and adjust
cp .env.example .env
# Edit .env for API keys, paths, etc.

# Build and start services
docker compose up --build
```
Services:
- `api`: Node.js gateway (port 3000)
- `orchestrator`: Java service (port 8080)
- `trainer`: Python training service (GPU if available)
- `worker`: Python data processing worker
- `redis`: Job queue and cache
- `postgres`: Job metadata storage
- `volumes`: Persistent `data/`, `models/`, `logs/`

#### 2. Manual Installation
```bash
# 1. Clone repo
git clone https://github.com/yourorg/lbos-ai.git
cd lbos-ai

# 2. Set up Python virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r src/python/requirements.txt

# 3. Set up Node.js
cd src/api
npm install
cd ../..

# 4. Set up Java (Maven)
cd src/orchestrator
mvn clean install
cd ../..

# 5. Install system dependencies
# Ubuntu example:
sudo apt-get update
sudo apt-get install -y ffmpeg git wget
# For GPU: Install NVIDIA driver and CUDA toolkit from https://developer.nvidia.com/cuda-downloads

# 6. Configure environment
cp .env.example .env
# Edit .env with paths, API keys, etc.

# 7. Start services (separate terminals or use tmux/screen)
# Terminal 1: API
cd src/api && npm start
# Terminal 2: Orchestrator
cd src/orchestrator && mvn spring-boot:run
# Terminal 3: Worker (data processing)
cd src/python && python -m lbos_ai.data.worker
# Terminal 4: Trainer (optional, start on demand)
#   python -m lbos_ai.train.trainer --config configs/train.yaml
```

### Post-Installation
- Access frontend at `http://localhost:3000` (if using dev server) or via API gateway serving static files.
- Default API gateway at `http://localhost:5000`.
- Monitor logs in `logs/` directory or via Docker logs.

## Design Philosophy Adherence
1. **Modularity**: 
   - Loosely coupled services communicate via well-defined APIs (HTTP/JSON) and message queues.
   - Each service (ingest, process, train, eval) can be developed, scaled, and replaced independently.
2. **Transparency & Control**: 
   - No hidden LLM APIs; all models trained from scratch on user-provided data.
   - Full audit trail: inputs → processed data → model weights → outputs.
3. **Efficiency**: 
   - Custom model architecture sized for task (avoids overparameterization).
   - Hardware-aware scheduling (GPU/CPU affinity).
   - Efficient data formats (JSONL, binary model checkpoints).
4. **Extensibility**: 
   - Plugin-like architecture for ingestion sources (add new `youtube.py`, `web.py`).
   - Swappable evaluation backends (Python/R/MATLAB).
   - Configurable model architecture via YAML.
5. **Robustness**: 
   - Retry mechanisms, dead-letter queues, health checks.
   - Input validation and sanitization (URLs, file paths).
   - Graceful degradation (CPU fallback, optional R/MATLAB).
6. **Usability**: 
   - Unified control panel (React SPA) for end-to-end workflow.
   - Real-time feedback via WebSocket (logs, metrics).
   - Clear documentation and one-click deployment (Docker Compose).
7. **Ethical & Legal**: 
   - URL ingestion respects `robots.txt` and rate limits (via `yt-dlp`/`newspaper3k` configurations).
   - Data provenance tracked; users responsible for content rights.
   - No user data telemetry; all processing is local/on-prem.

---
*Design Version: 1.0*
*Last Updated: 2026-06-27*