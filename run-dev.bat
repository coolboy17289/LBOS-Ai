@echo off
REM LBOS-AI Development Starter
REM Starts both backend and frontend for development

echo.
echo ==============================
echo LBOS-AI Development Server
echo ==============================
echo.

REM Check if we're in the right directory
if not exist "package.json" (
    echo [WARNING] Please run this script from the project root directory.
)

echo [INFO] Starting backend (Node.js) API server...
cd /d %~dp0node
REM Install dependencies if needed
npm install > nul
START "LBOS-AI Backend" cmd /k "node index.js"
cd ..

echo [INFO] Waiting for backend to start...
timeout /t 5 > nul

echo [INFO] Starting frontend (React) development server...
cd /d %~dp0frontend
REM Install dependencies if needed
npm install > nul
START "LBOS-AI Frontend" cmd /k "npm start"
cd ..

echo.
echo [SUCCESS] Both servers are starting.
echo [INFO] Backend API: http://localhost:5000
echo [INFO] Frontend UI: http://localhost:3000 (proxying to backend)
echo.
echo [INFO] To stop, close the console windows or press Ctrl+C in each.
echo.
pause