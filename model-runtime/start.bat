@echo off
REM Model Runtime Startup Script for Windows
REM Starts the Gemma 4B inference server using llama.cpp

echo Starting LBOS-AI Model Runtime - Gemma 4B Integration

REM Check if model exists
if not exist models\gemma-4b-it-q4_k_m.gguf (
    echo Error: Model file not found at models\gemma-4b-it-q4_k_m.gguf
    echo Please download the Gemma 4B GGUF model and place it in the models directory
    echo Example: Use a browser to download from Hugging Face
    exit /b 1
)

REM Check CPU features (basic)
wmic cpu get DataWidth > nul
if %errorlevel% neq 0 (
    echo Warning: Could not check CPU features
)

REM Create necessary directories
if not exist models mkdir models
if not exist logs mkdir logs

REM Set environment variables for optimal performance
set OMP_NUM_THREADS=8
set MKL_NUM_THREADS=8

echo.
echo Starting model server...
echo Model: models\gemma-4b-it-q4_k_m.gguf
echo Server will be available at http://localhost:8080
echo.
echo API Endpoints:
echo - POST /v1/completions
echo - POST /v1/chat/completions
echo - GET /v1/models
echo - WS /ws/completions
echo.
echo To test:
echo curl -X POST http://localhost:8080/v1/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"gemma-4b-it\", \"prompt\": \"Hello, how are you?\", \"max_tokens\": 50}"
echo.
echo NOTE: This is a demonstration version.
echo In production, replace with actual llama.cpp server:
echo .\server.exe -m models\gemma-4b-it-q4_k_m.gguf -c 8192 -b 512 -t 8 --host 0.0.0.0 --port 8080
echo.

REM Keep the window open
echo Model runtime ready. Press any key to stop...
pause > nul