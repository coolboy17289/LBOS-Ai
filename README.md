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

### Option 1: Using Installer Scripts (Recommended for quick start)

#### Windows
```bat
install.bat
```

#### Linux/macOS
```bash
chmod +x install.sh   # Make script executable (if needed)
./install.sh
```

The installer will:
1. Install Python dependencies from `python/requirements.txt`
2. Install Node.js dependencies for both backend and frontend
3. Build the React frontend for production
4. Start the backend server (Node.js) which serves the API and the built frontend UI

After installation, access the system at:
- **API**: http://localhost:5000
- **UI**: http://localhost:5000 (same port, serving the React app)

### Option 2: Development Mode (for contributors)

If you want to develop with hot-reloading:

1. **Backend API** (Node.js
npm install
npm start
# Runs on http://localhost:5000

2. **Frontend UI**
cd frontend
npm install
npm start
# Runs on http://localhost:3000 (proxies API requests to backend)

### Option 3: Docker (if Docker Compose is added later)
Refer to docker-compose.yml (if present).

## Usage
After starting the system:
1. Open your browser to the UI URL.
2. Use the navigation menu to access different panels:
   - **Dashboard**: System overview and statistics
   - **Ingestion**: Submit YouTube URLs or web articles for processing
   - **Training**: Configure and start model training jobs
   - **Evaluation**: Run evaluations on trained models
   - **Settings**: Configure system parameters

## Project Structure
```
lbos-ai/
├── cpp/                 # C++ performance utilities (e.g., string processing)
├── frontend/            # React TypeScript control panel
├── node/                # Node.js API gateway and WebSocket server
├── java/                # Java orchestration service (Spring Boot)
├── python/              # Python data processing and training
├── matlab/              # Optional MATLAB scripts for analysis
├── r/                   # Optional R scripts for statistical analysis
├── design.md            # System architecture design
├── README.md            # This file
├── LICENSE              # MIT License
├── install.bat          # Windows installer and launcher
├── install.sh           # Unix installer and launcher
└── main.md              # Original notes
```

## License
MIT License - see [LICENSE](LICENSE) file for details.

## Contact
Lihan Badenhorst - lihan@example.com

Project Link: https://github.com/yourorg/lbos-ai