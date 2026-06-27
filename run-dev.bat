@echo off
REM LBOS-AI Development Starter
REM Starts both backend and frontend for development

echo Starting backend (Node.js) API server...
cd node
call npm install > nul
start "" cmd /k "node index.js"
cd ..

echo Waiting for backend to start...
timeout /t 5 > nul

echo Starting frontend (React) development server...
cd frontend
call npm install > nul
start "" cmd /k "npm start"
cd ..

echo.
echo Both servers are starting.
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:3000 (proxying to backend)
echo.
echo To stop, close the console windows or press Ctrl+C in each.
pause