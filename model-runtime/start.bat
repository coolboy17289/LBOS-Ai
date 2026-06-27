@echo off
REM Model Runtime Startup Script for Windows
REM Starts both Gemma 4B and Gemma 5B inference servers using llama.cpp

echo.
echo ==============================
echo LBOS-AI Model Runtime
echo ==============================
echo.

REM Check if llama.cpp is available
if not exist "llama-server.exe" (
    echo [ERROR] llama-server.exe not found. Please build llama.cpp first.
    echo [INFO] You can build it with: mkdir build && cd build && cmake .. && cmake --build . --config Release
    pause
    exit /b 1
)

REM Check for Gemma 4B model
if not exist "models\gemma-4b-it-q4_k_m.gguf" (
    echo [WARNING] Gemma 4B model not found at models\gemma-4b-it-q4_k_m.gguf
    echo [INFO] Please download the model and place it in the models directory
    echo [INFO] You can still continue with Gemma 5B if available
) else (
    echo [INFO] Gemma 4B model found: models\gemma-4b-it-q4_k_m.gguf
)

REM Check for Gemma 5B model
if not exist "models\gemma-5b-it-q4_k_m.gguf" (
    echo [WARNING] Gemma 5B model not found at models\gemma-5b-it-q4_k_m.gguf
    echo [INFO] Please download the model and place it in the models directory
    echo [INFO] You can still continue with just Gemma 4B if available
) else (
    echo [INFO] Gemma 5B model found: models\gemma-5b-it-q4_k_m.gguf
)

REM Check if at least one model exists
if not exist "models\gemma-4b-it-q4_k_m.gguf" (
    if not exist "models\gemma-5b-it-q4_k_m.gguf" (
        echo [ERROR] No Gemma models found. Please download at least one model.
        pause
        exit /b 1
    )
)

REM Create necessary directories
if not exist models mkdir models
if not exist logs mkdir logs

REM Set environment variables for optimal performance
set OMP_NUM_THREADS=8
set MKL_NUM_THREADS=8

echo.
echo [INFO] Starting model servers...
echo.

REM Start Gemma 4B server if model exists
if exist "models\gemma-4b-it-q4_k_m.gguf" (
    echo [INFO] Starting Gemma 4B model server on port 8080...
    START "Gemma 4B Server" cmd /k "llama-server.exe -m models\gemma-4b-it-q4_k_m.gguf --host 0.0.0.0 --port 8080 --ctx-size 8192 --batch-size 512 --threads 8 --ngl 0"
    echo [INFO] Gemma 4B server starting on http://localhost:8080
) else (
    echo [WARNING] Skipping Gemma 4B server (model not found)
)

REM Start Gemma 5B server if model exists
if exist "models\gemma-5b-it-q4_k_m.gguf" (
    echo [INFO] Starting Gemma 5B model server on port 8081...
    START "Gemma 5B Server" cmd /k "llama-server.exe -m models\gemma-5b-it-q4_k_m.gguf --host 0.0.0.0 --port 8081 --ctx-size 8192 --batch-size 512 --threads 8 --ngl 0"
    echo [INFO] Gemma 5B server starting on http://localhost:8081
) else (
    echo [WARNING] Skipping Gemma 5B server (model not found)
)

echo.
echo [SUCCESS] Model server startup initiated.
echo [INFO] Check the console windows for server logs.
echo [INFO] To stop servers, close the console windows.
echo.
pause