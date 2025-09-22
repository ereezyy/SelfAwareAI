# AI Bot Management System - Windows Startup Script

Write-Host "🚀 Starting AI Bot Management System..." -ForegroundColor Green

# Set location to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# Check if virtual environment exists
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found. Please run deployment setup first." -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& ".\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Blue
$packages = @("flask", "transformers", "torch", "websockets")
foreach ($package in $packages) {
    $installed = pip list | Select-String $package
    if (!$installed) {
        Write-Host "⚠️  Package $package not found. Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
        break
    }
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "temp" | Out-Null

# Start API Server
Write-Host "🌐 Starting API Server..." -ForegroundColor Green
Start-Process python -ArgumentList "api_server.py" -NoNewWindow

# Wait for API server to initialize
Start-Sleep 5

# Start WebSocket Server
Write-Host "🔌 Starting WebSocket Server..." -ForegroundColor Green
Start-Process python -ArgumentList "websocket_server.py" -NoNewWindow

# Wait for services to start
Start-Sleep 3

# Test endpoints
Write-Host "🧪 Testing endpoints..." -ForegroundColor Blue
try {
    $health = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET -TimeoutSec 10
    Write-Host "✅ API Server: " -ForegroundColor Green -NoNewline
    Write-Host $health.status -ForegroundColor White
} catch {
    Write-Host "❌ API Server: Not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 AI Bot Management System Started!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   • API Server: http://localhost:5000" -ForegroundColor White
Write-Host "   • WebSocket: ws://localhost:8765" -ForegroundColor White
Write-Host "   • Health Check: http://localhost:5000/api/health" -ForegroundColor White
Write-Host ""
Write-Host "📋 Available Commands:" -ForegroundColor Cyan
Write-Host "   • Test: Invoke-RestMethod -Uri 'http://localhost:5000/api/health'" -ForegroundColor White
Write-Host "   • Stop: Get-Process python | Stop-Process" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitor logs at: .\logs\" -ForegroundColor Yellow

# Keep script running to monitor
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow
try {
    while ($true) {
        Start-Sleep 60
        # Check if processes are still running
        $apiProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*api_server.py*"}
        $wsProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*websocket_server.py*"}
        
        if (!$apiProcess) {
            Write-Host "⚠️  API Server process not found. Restarting..." -ForegroundColor Yellow
            Start-Process python -ArgumentList "api_server.py" -NoNewWindow
        }
        
        if (!$wsProcess) {
            Write-Host "⚠️  WebSocket Server process not found. Restarting..." -ForegroundColor Yellow
            Start-Process python -ArgumentList "websocket_server.py" -NoNewWindow
        }
    }
} catch {
    Write-Host "🛑 Shutting down services..." -ForegroundColor Red
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*api_server.py*" -or $_.CommandLine -like "*websocket_server.py*"} | Stop-Process -Force
    Write-Host "👋 Services stopped." -ForegroundColor Green
}