# AI Bot Management System - Windows Installation Script

param(
    [switch]$SkipPython,
    [switch]$Production,
    [string]$InstallPath = "C:\AIBotProject"
)

Write-Host "🚀 AI Bot Management System - Windows Installer" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if running as Administrator (optional for system-wide install)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if ($Production -and -not $isAdmin) {
    Write-Host "⚠️  Production mode requires Administrator privileges" -ForegroundColor Yellow
    Write-Host "Please run as Administrator or remove -Production flag" -ForegroundColor Yellow
    exit 1
}

# Step 1: Check/Install Python 3.11
if (-not $SkipPython) {
    Write-Host "🔍 Checking Python 3.11..." -ForegroundColor Blue
    
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.11") {
            Write-Host "✅ Python 3.11 found: $pythonVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ Python 3.11 not found. Current: $pythonVersion" -ForegroundColor Red
            Write-Host "Please install Python 3.11 from https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
    } catch {
        Write-Host "❌ Python not found in PATH" -ForegroundColor Red
        Write-Host "Please install Python 3.11 from https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

# Step 2: Create Installation Directory
Write-Host "📁 Setting up installation directory..." -ForegroundColor Blue

if ($InstallPath -ne (Get-Location).Path) {
    if (Test-Path $InstallPath) {
        $response = Read-Host "Directory $InstallPath already exists. Continue? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "Installation cancelled." -ForegroundColor Yellow
            exit 0
        }
    } else {
        New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
    }
    
    Set-Location $InstallPath
}

# Step 3: Create Virtual Environment
Write-Host "🐍 Creating Python virtual environment..." -ForegroundColor Blue

if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Removing old one..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

python -m venv venv

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& ".\venv\Scripts\Activate.ps1"

# Step 4: Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Blue
python -m pip install --upgrade pip

# Step 5: Install Dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Blue

$requirements = @(
    "psutil>=5.9.0",
    "transformers>=4.21.0", 
    "torch>=1.12.0",
    "sentencepiece>=0.1.97",
    "sacremoses>=0.0.53",
    "protobuf>=3.20.0",
    "flask>=2.3.0",
    "flask-cors>=4.0.0",
    "websockets>=11.0.2",
    "numpy>=1.21.0"
)

foreach ($package in $requirements) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    pip install $package --no-cache-dir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install $package" -ForegroundColor Red
        exit 1
    }
}

# Step 6: Create Directory Structure
Write-Host "📂 Creating directory structure..." -ForegroundColor Blue

$directories = @("logs", "uploads", "temp", "config", "data")
foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
}

# Step 7: Create Configuration Files
Write-Host "⚙️  Creating configuration files..." -ForegroundColor Blue

# Create bot_config.json if it doesn't exist
if (!(Test-Path "bot_config.json")) {
    $config = @{
        bot_name = "Self-Aware Assistant Bot"
        version = "1.0.0"
        modules = @{
            self_aware = @{ enabled = $true }
            self_healing = @{ enabled = $true }
            self_coding = @{ enabled = $true }
            text_humanizer = @{ enabled = $true; model = "Ateeqq/Text-Rewriter-Paraphraser" }
            ai_detector = @{ enabled = $true; model = "AICodexLab/answerdotai-ModernBERT-base-ai-detector" }
        }
        interface = @{
            startup_message = $true
            command_history = $true
            auto_save_logs = $true
        }
    }
    
    $config | ConvertTo-Json -Depth 3 | Out-File -FilePath "bot_config.json" -Encoding utf8
    Write-Host "  ✓ Created bot_config.json" -ForegroundColor Gray
}

# Step 8: Test Installation
Write-Host "🧪 Testing installation..." -ForegroundColor Blue

try {
    $testResult = python bot_launcher.py --health-check 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Bot modules test: PASSED" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Bot modules test: WARNING (some modules may not be available)" -ForegroundColor Yellow
        Write-Host "This is normal if AI models haven't been downloaded yet." -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Bot modules test: FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

# Step 9: Create Shortcuts and Scripts
Write-Host "🔗 Creating shortcuts and scripts..." -ForegroundColor Blue

# Create Windows batch files for easy startup
@"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python api_server.py
pause
"@ | Out-File -FilePath "start-api.bat" -Encoding ascii

@"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python websocket_server.py
pause
"@ | Out-File -FilePath "start-websocket.bat" -Encoding ascii

@"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python bot_launcher.py
pause
"@ | Out-File -FilePath "start-interactive.bat" -Encoding ascii

Write-Host "  ✓ Created start-api.bat" -ForegroundColor Gray
Write-Host "  ✓ Created start-websocket.bat" -ForegroundColor Gray  
Write-Host "  ✓ Created start-interactive.bat" -ForegroundColor Gray

# Step 10: Configure Firewall (if Administrator)
if ($isAdmin) {
    Write-Host "🔒 Configuring Windows Firewall..." -ForegroundColor Blue
    
    try {
        New-NetFirewallRule -DisplayName "AI Bot API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
        New-NetFirewallRule -DisplayName "AI Bot WebSocket" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
        Write-Host "  ✓ Firewall rules created" -ForegroundColor Gray
    } catch {
        Write-Host "  ⚠️  Could not create firewall rules" -ForegroundColor Yellow
    }
}

# Step 11: Installation Complete
Write-Host ""
Write-Host "🎉 Installation Complete!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Installation Location: $InstallPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Quick Start Options:" -ForegroundColor Cyan
Write-Host "  1. Interactive Mode:  .\start-interactive.bat" -ForegroundColor White
Write-Host "  2. API Server:        .\start-api.bat" -ForegroundColor White
Write-Host "  3. WebSocket Server:  .\start-websocket.bat" -ForegroundColor White
Write-Host "  4. PowerShell:        .\startup.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test Commands:" -ForegroundColor Cyan
Write-Host "  Health Check:   python bot_launcher.py --health-check" -ForegroundColor White
Write-Host "  Test API:       Invoke-RestMethod -Uri 'http://localhost:5000/api/health'" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "  README.md - General information" -ForegroundColor White
Write-Host "  WINDOWS_DEPLOYMENT.md - Detailed Windows guide" -ForegroundColor White
Write-Host "  DEPLOYMENT_GUIDE.md - Commercial deployment" -ForegroundColor White
Write-Host ""

if (-not $Production) {
    Write-Host "💡 For production deployment, run with -Production flag" -ForegroundColor Yellow
    Write-Host "   .\install.ps1 -Production" -ForegroundColor Gray
}

Write-Host "Happy bot managing! 🤖" -ForegroundColor Green