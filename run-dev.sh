#!/bin/bash
# LBOS-AI Development Starter
# Starts both backend and frontend for development

echo "Starting backend (Node.js) API server..."
cd node
npm install &
npm_pid=$!
# Wait for npm install to finish
wait $npm_pid
node index.js &
backend_pid=$!
cd ..

echo "Waiting for backend to start..."
sleep 5

echo "Starting frontend (React) development server..."
cd frontend
npm install &
npm_pid=$!
wait $npm_pid
npm start &
frontend_pid=$!
cd ..

echo
echo "Both servers are starting."
echo "Backend API: http://localhost:5000"
echo "Frontend UI: http://localhost:3000 (proxying to backend)"
echo
echo "To stop, press Ctrl+C in this terminal (will kill both processes)."

# Wait for user to press Ctrl+C, then kill children
trap "kill $backend_pid $frontend_pid; exit" SIGINT
wait