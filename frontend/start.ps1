# Frontend Startup Script
# This script installs dependencies and starts the development server

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Resume Screening System - Frontend" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js is not installed!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Node.js version: " -NoNewline
node --version

Write-Host "npm version: " -NoNewline
npm --version
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

# Start development server
Write-Host "Starting development server..." -ForegroundColor Green
Write-Host "The app will be available at http://localhost:3000" -ForegroundColor Cyan
Write-Host "Make sure the backend is running on http://localhost:8000" -ForegroundColor Yellow
Write-Host ""

npm run dev
