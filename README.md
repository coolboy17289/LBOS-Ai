# LBOS-AI

LBOS-AI is an end-to-end pipeline for ingesting multimedia content (YouTube videos and web articles), processing it into a structured dataset, training a custom lightweight language model, and evaluating the model's performance using R and MATLAB-based analytics.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [License](#license)

## Features
- URL ingestion from YouTube and web articles
- Automated transcription and text extraction
- Custom dataset generation with cleaning, summarization, and Q&A pair generation
- Custom transformer model training from scratch (no runtime LLM dependency)
- Evaluation with perplexity, QA metrics, and optional R/MATLAB analysis
- React TypeScript control panel for monitoring and control
- Microservice architecture with Node.js API gateway, Java orchestrator, and Python workers
- Docker support for easy deployment

## Architecture
See [design.md](design.md) for detailed system architecture.

## Installation
See [INSTALL.md](INSTALL.md) for detailed installation instructions.

Quick start with Docker:
```bash
docker compose up --build
```

Manual installation:
1. Install prerequisites (Python 3.9+, Node.js 18+, Java 17, FFmpeg)
2. Clone repository
3. Set up Python virtual environment and install requirements
4. Install Node.js dependencies
5. Build Java project with Maven
6. Configure environment variables
7. Start services

## Project Structure
```
lbos-ai/
├── cpp/                 # C++ components (Whisper.cpp bindings)
├── frontend/            # React TypeScript control panel
├── node/                # Node.js API gateway and WebSocket server
├── java/                # Java orchestration service (Spring Boot)
├── python/              # Python data processing and training
├── matlab/              # Optional MATLAB scripts
├── r/                   # Optional R scripts
├── data/                # Data storage (raw, processed, test)
├── models/              # Trained model checkpoints
├── eval/                # Evaluation reports
├── logs/                # Service logs
├── design.md            # System architecture design
├── README.md            # This file
├── LICENSE              # MIT License
├── install.sh           # Linux/macOS installer
├── install.bat          # Windows installer
└── docker-compose.yml   # Optional: multi-service deployment
```

## License
MIT License - see [LICENSE](LICENSE) file for details.

## Contact
Lihan Badenhorst - lihan@example.com

Project Link: https://github.com/yourorg/lbos-ai