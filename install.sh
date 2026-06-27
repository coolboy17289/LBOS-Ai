#!/bin/bash
# LBOS-AI Installer and Launcher for Unix-like systems (Linux/macOS)
# Installs dependencies and starts the production system

set -e  # Exit on any error

echo "=============================="
echo "LBOS-AI Installation"
echo "=============================="

# Check for required commands
command -v node >/dev/null 2>&1 || { echo >&2 "Node.js is required but not installed. Aborting."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo >&2 "npm is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python3 is required but not installed. Aborting."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo >&2 "pip3 is required but not installed. Aborting."; exit 1; }

echo "Installing Python dependencies..."
cd python
pip3 install -r requirements.txt
cd ..

echo "Installing Node.js backend dependencies..."
cd node
npm install
cd ..

echo "Installing Node.js frontend dependencies..."
cd frontend
npm install
cd ..

echo "Building frontend for production..."
cd frontend
npm run build
cd ..

echo
echo "Installation complete."
echo "Starting LBOS-AI system..."
echo "Backend API will be available at http://localhost:5000"
echo "Frontend UI will be served at http://localhost:5000 (same port)"
echo

# Start the backend server which will serve the static frontend files
cd node
npm start