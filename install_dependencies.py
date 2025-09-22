#!/usr/bin/env python3
"""
Install required dependencies for the AI Bot Management System
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🚀 Installing AI Bot Management System Dependencies...")
    print("=" * 60)
    
    # Required packages
    packages = [
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
    ]
    
    print(f"Installing {len(packages)} packages...")
    print()
    
    failed_packages = []
    
    for package in packages:
        print(f"Installing {package}...")
        if not install_package(package):
            failed_packages.append(package)
    
    print()
    print("=" * 60)
    
    if failed_packages:
        print("❌ Installation completed with errors:")
        for package in failed_packages:
            print(f"  - {package}")
        print("\nPlease install failed packages manually:")
        for package in failed_packages:
            print(f"  pip install {package}")
        return False
    else:
        print("✅ All dependencies installed successfully!")
        print("\n🎉 You can now run the bot:")
        print("  python bot_launcher.py --health-check")
        print("  python api_server.py")
        print("  python websocket_server.py")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)