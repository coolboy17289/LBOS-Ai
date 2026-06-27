#!/bin/bash
# Model Runtime Startup Script
# Starts the Gemma 4B inference server using llama.cpp

set -e  # Exit on any error

echo "Starting LBOS-AI Model Runtime - Gemma 4B Integration"

# Check if model exists
MODEL_PATH="./models/gemma-4b-it-q4_k_m.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH"
    echo "Please download the Gemma 4B GGUF model and place it in the models directory"
    echo "Example: wget https://huggingface.co/TheBloke/gemma-4B-it-GGUF/resolve/main/gemma-4b-it.q4_k_m.gguf"
    exit 1
fi

# Check CPU features for optimization
echo "Checking CPU capabilities..."
if grep -q avx2 /proc/cpuinfo; then
    echo "AVX2 supported - good performance expected"
else
    echo "Warning: AVX2 not found - performance may be reduced"
fi

if grep -q avx512f /proc/cpuinfo; then
    echo "AVX-512 supported - excellent performance expected"
fi

# Create necessary directories
mkdir -p models logs

# Set environment variables
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

# Start the server
echo "Starting model server..."
echo "Model: $MODEL_PATH"
echo "Server will be available at http://localhost:8080"

# In a real implementation, this would launch the llama.cpp server
# For this demo, we'll create a placeholder that simulates the service
cat > server_info.txt << EOF
LLAMA CPP SERVER SIMULATION
Model: $(basename "$MODEL_PATH")
Context Size: 8192
Batch Size: 512
Threads: 8
GPU Layers: 0 (CPU Only)
Listening on: 0.0.0.0:8080

API Endpoints:
- POST /v1/completions
- POST /v1/chat/completions
- GET /v1/models
- WS /ws/completions

To test:
curl -X POST http://localhost:8080/v1/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model": "gemma-4b-it", "prompt": "Hello, how are you?", "max_tokens": 50}'

NOTE: This is a demonstration version.
In production, replace with actual llama.cpp server:
./server -m models/gemma-4b-it-q4_k_m.gguf -c 8192 -b 512 -t 8 --host 0.0.0.0 --port 8080
EOF

cat server_info.txt

# Keep the container running
echo "Model runtime ready. Press Ctrl+C to stop."
tail -f /dev/null