@echo off
REM LBOS-AI Installer and Launcher for Windows
REM Installs dependencies and starts the production system

echo.
echo ==============================
echo LBOS-AI Installation
echo ==============================
echo.

REM Check for required commands
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is required but not installed. Aborting.
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is required but not installed. Aborting.
    exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is required but not installed. Aborting.
    exit /b 1
)
where pip >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is required but not installed. Aborting.
    exit /b 1
)

echo [INFO] Installing Python dependencies...
cd /d %~dp0python
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    exit /b 1
)
cd ..

echo [INFO] Installing Node.js backend dependencies...
cd /d %~dp0node
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js backend dependencies.
    exit /b 1
)
cd ..

echo [INFO] Installing Node.js frontend dependencies...
cd /d %~dp0frontend
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js frontend dependencies.
    exit /b 1
)
cd ..

echo [INFO] Building frontend for production...
cd /d %~dp0frontend
npm run build
if errorlevel 1 (
    echo [ERROR] Failed to build frontend.
    exit /b 1
)
cd ..

echo.
echo [SUCCESS] Installation complete.
echo [INFO] Starting LBOS-AI system...
echo [INFO] Backend API will be available at http://localhost:5000
echo [INFO] Frontend UI will be served at http://localhost:5000 (same port)
echo.

REM Start the backend server which will serve the static frontend files
cd /d %~dp0node
npm start