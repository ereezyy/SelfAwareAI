# 🚀 Windows PowerShell Deployment Guide

## 📋 Prerequisites

### 1. Install Python 3.11
```powershell
# Download and install Python 3.11 from https://www.python.org/downloads/
# Or use Chocolatey
choco install python311

# Verify installation
python --version
# Should show: Python 3.11.x
```

### 2. Install Git (if not already installed)
```powershell
# Using Chocolatey
choco install git

# Or download from https://git-scm.com/download/win
```

## 🔧 Environment Setup

### 1. Create Project Directory
```powershell
# Navigate to your desired location
cd C:\
mkdir AIBotProject
cd AIBotProject

# Or clone if you have a repository
# git clone <your-repo-url> .
```

### 2. Create Python Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If execution policy error occurs, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify activation (should show (venv) in prompt)
```

### 3. Install Dependencies
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# If you get errors, install individually:
pip install psutil>=5.9.0
pip install transformers>=4.21.0
pip install torch>=1.12.0
pip install sentencepiece>=0.1.97
pip install sacremoses>=0.0.53
pip install protobuf>=3.20.0
pip install flask>=2.3.0
pip install flask-cors>=4.0.0
pip install websockets>=11.0.2
pip install numpy>=1.21.0
```

## ⚙️ Configuration Setup

### 1. Create Required Directories
```powershell
# Create log directories
New-Item -ItemType Directory -Force -Path "logs"
New-Item -ItemType Directory -Force -Path "uploads"
New-Item -ItemType Directory -Force -Path "temp"
```

### 2. Configure Bot Settings
```powershell
# Copy default config if it doesn't exist
if (!(Test-Path "bot_config.json")) {
    Write-Host "Creating default bot configuration..."
    # The bot will create default config on first run
}
```

### 3. Set Environment Variables (Optional)
```powershell
# Set temporary environment variables for this session
$env:FLASK_ENV = "production"
$env:FLASK_DEBUG = "0"
$env:BOT_LOG_LEVEL = "INFO"

# To make permanent, add to your PowerShell profile:
# notepad $PROFILE
# Add the $env lines above
```

## 🚀 Deployment Steps

### 1. Test Bot Components
```powershell
# Test core bot functionality
python bot_launcher.py --health-check

# Expected output should show module initialization success
```

### 2. Start the API Server
```powershell
# Start the main API server
python api_server.py

# You should see:
# 🚀 Starting AI Bot API Server...
# ✅ Core bot modules initialized successfully
# 🌐 Server starting on http://0.0.0.0:5000
```

### 3. Start WebSocket Server (Separate Terminal)
```powershell
# Open new PowerShell window/tab
cd C:\AIBotProject
.\venv\Scripts\Activate.ps1

# Start WebSocket server
python websocket_server.py

# You should see:
# 🚀 Starting WebSocket server on ws://localhost:8765
```

## 🧪 Testing Deployment

### 1. Test API Endpoints
```powershell
# Test health endpoint
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET

# Test bot status
Invoke-RestMethod -Uri "http://localhost:5000/api/bot/status" -Method GET

# Test text humanization
$body = @{
    text = "This is a test sentence to humanize"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/humanize" -Method POST -Body $body -ContentType "application/json"
```

### 2. Test WebSocket Connection
```powershell
# Install WebSocket test tool
npm install -g wscat

# Test WebSocket connection
wscat -c ws://localhost:8765
```

### 3. Test File Upload
```powershell
# Create test file
"print('Hello World')" | Out-File -FilePath "test.py" -Encoding utf8

# Test file upload (using curl if available)
curl -X POST -F "file=@test.py" http://localhost:5000/api/upload

# Or use PowerShell
$form = @{
    file = Get-Item -Path "test.py"
}
Invoke-RestMethod -Uri "http://localhost:5000/api/upload" -Method POST -Form $form
```

## 🔒 Production Deployment

### 1. Windows Service Setup (Optional)
```powershell
# Install python-windows-service
pip install pywin32

# Create service wrapper script (service.py)
@"
import win32serviceutil
import win32service
import win32event
import subprocess
import sys
import os

class AIBotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AIBotService"
    _svc_display_name_ = "AI Bot Management Service"
    _svc_description_ = "AI Bot with management and WebSocket functionality"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        
    def SvcDoRun(self):
        # Change to your project directory
        os.chdir(r"C:\AIBotProject")
        
        # Start the API server
        subprocess.Popen([sys.executable, "api_server.py"])
        
        # Wait for stop signal
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AIBotService)
"@ | Out-File -FilePath "service.py" -Encoding utf8

# Install the service
python service.py install

# Start the service
python service.py start
```

### 2. IIS Integration (Advanced)
```powershell
# Install IIS with CGI support
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-CGI

# Install wfastcgi
pip install wfastcgi

# Configure wfastcgi
wfastcgi-enable

# Create web.config for IIS
@"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" 
           scriptProcessor="C:\AIBotProject\venv\Scripts\python.exe|C:\AIBotProject\venv\Lib\site-packages\wfastcgi.py" 
           resourceType="Unspecified" requireAccess="Script" />
    </handlers>
  </system.webServer>
  <appSettings>
    <add key="WSGI_HANDLER" value="api_server.app" />
    <add key="PYTHONPATH" value="C:\AIBotProject" />
  </appSettings>
</configuration>
"@ | Out-File -FilePath "web.config" -Encoding utf8
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Python Path Issues
```powershell
# If python command not found
$env:PATH += ";C:\Python311;C:\Python311\Scripts"

# Or use full path
C:\Python311\python.exe api_server.py
```

#### 2. Module Import Errors
```powershell
# Check if modules are installed
pip list | Select-String "transformers|torch|flask"

# Reinstall problematic modules
pip uninstall torch transformers
pip install torch transformers --no-cache-dir
```

#### 3. Port Already in Use
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
$env:FLASK_PORT = "5001"
python api_server.py
```

#### 4. WebSocket Connection Issues
```powershell
# Check Windows Firewall
New-NetFirewallRule -DisplayName "AI Bot API" -Direction Inbound -Port 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "AI Bot WebSocket" -Direction Inbound -Port 8765 -Protocol TCP -Action Allow
```

#### 5. Memory Issues with AI Models
```powershell
# Monitor memory usage
Get-Process python | Select-Object ProcessName, WorkingSet, PagedMemorySize

# If insufficient memory, disable heavy modules in bot_config.json
```

## 📊 Monitoring and Maintenance

### 1. Log Monitoring
```powershell
# Monitor logs in real-time
Get-Content -Path "logs\bot_main.log" -Wait -Tail 10

# Check for errors
Select-String -Path "logs\*.log" -Pattern "ERROR|CRITICAL"
```

### 2. Performance Monitoring
```powershell
# Create monitoring script
@"
while (`$true) {
    `$process = Get-Process python -ErrorAction SilentlyContinue
    if (`$process) {
        Write-Host "CPU: `$(`$process.CPU)% Memory: `$([math]::Round(`$process.WorkingSet/1MB,2))MB"
    }
    Start-Sleep 60
}
"@ | Out-File -FilePath "monitor.ps1" -Encoding utf8

# Run monitoring
.\monitor.ps1
```

### 3. Automated Startup
```powershell
# Create startup script
@"
cd C:\AIBotProject
.\venv\Scripts\Activate.ps1
Start-Process python -ArgumentList "api_server.py" -NoNewWindow
Start-Sleep 5
Start-Process python -ArgumentList "websocket_server.py" -NoNewWindow
"@ | Out-File -FilePath "startup.ps1" -Encoding utf8

# Add to Windows startup (optional)
# Copy startup.ps1 to shell:startup folder
```

## 🎯 Quick Commands Summary

```powershell
# Complete deployment in one go:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python bot_launcher.py --health-check
python api_server.py

# In separate terminal:
python websocket_server.py

# Test deployment:
Invoke-RestMethod -Uri "http://localhost:5000/api/health"
```

## 🚨 Security Considerations

### 1. Firewall Configuration
```powershell
# Allow only necessary ports
New-NetFirewallRule -DisplayName "AI Bot API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "AI Bot WebSocket" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
```

### 2. User Permissions
```powershell
# Run with limited user account (not Administrator)
# Create dedicated service account for production
```

### 3. HTTPS Setup (Production)
```powershell
# Generate self-signed certificate for testing
New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "cert:\LocalMachine\My"
```

🎉 **Your AI Bot Management System is now deployed and ready for use on Windows!**