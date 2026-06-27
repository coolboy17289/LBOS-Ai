@echo off
REM LBOS-AI Installer and Launcher for Windows
REM Installs dependencies and starts the production system

@echo off
echo ==============================
echo LBOS-AI Installation
echo ==============================

REM Check for required commands
where node >nul 2>&1
if errorlevel 1 (
    echo Node.js is required but not installed. Aborting.
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo npm is required but not installed. Aborting.
    exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed. Aborting.
    exit /b 1
)
where pip >nul 2>&1
if errorlevel 1 (
    echo pip is required but not installed. Aborting.
    exit /b 1
)

echo Installing Python dependencies...
cd python
pip install -r requirements.txt
cd ..

echo Installing Node.js backend dependencies...
cd node
npm install
cd ..

echo Installing Node.js frontend dependencies...
cd frontend
npm install
cd ..

echo Building frontend for production...
cd frontend
npm run build
cd ..

echo.
echo Installation complete.
echo Starting LBOS-AI system...
echo Backend API will be available at http://localhost:5000
echo Frontend UI will be served at http://localhost:5000 (same port)
echo.

REM Start the backend server which will serve the static frontend files
cd node
npm start