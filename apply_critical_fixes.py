#!/usr/bin/env python3
"""
Apply Critical Fixes to Existing Code Files
This script patches the most critical issues in the existing codebase.
"""

import os
import shutil
import re

def backup_file(filepath):
    """Create backup of original file"""
    backup_path = f"{filepath}.backup"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup: {backup_path}")

def fix_self_aware_module():
    """Fix cross-platform issues in self_aware_module.py"""
    filepath = "self_aware_module.py"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix hard-coded disk path
    old_disk_usage = 'disk_usage = psutil.disk_usage("/")'
    new_disk_usage = '''# Cross-platform disk usage
            if os.name == 'nt':  # Windows
                disk_usage = psutil.disk_usage("C:\\\\")
            else:  # Unix-like systems
                disk_usage = psutil.disk_usage("/")'''
    
    content = content.replace(old_disk_usage, new_disk_usage)
    
    # Add os import if not present
    if 'import os' not in content:
        content = content.replace('import psutil', 'import psutil\nimport os')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed cross-platform disk usage in {filepath}")

def fix_command_interface():
    """Fix security and path issues in command_interface.py"""
    filepath = "command_interface.py"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace hard-coded /home/ubuntu/ paths
    content = re.sub(
        r'/home/ubuntu/',
        'os.path.expanduser("~") + os.sep',
        content
    )
    
    # Fix subprocess call to use current directory
    old_subprocess = 'abs_script_path = os.path.abspath(script_path)'
    new_subprocess = '''abs_script_path = os.path.abspath(script_path)
        
        # Security check - only allow scripts in current directory tree
        allowed_root = os.path.abspath(os.getcwd())
        if not abs_script_path.startswith(allowed_root):
            return f"Error: Script must be in current directory tree: {abs_script_path}"'''
    
    if old_subprocess in content:
        content = content.replace(old_subprocess, new_subprocess)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed security and path issues in {filepath}")

def fix_api_server_cors():
    """Fix CORS security in api_server.py"""
    filepath = "api_server.py"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace insecure CORS
    old_cors = "CORS(app)"
    new_cors = '''# Secure CORS configuration
CORS(app, 
     origins=['http://localhost:3000', 'http://localhost:5173', 'https://localhost:5173'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)'''
    
    if old_cors in content:
        content = content.replace(old_cors, new_cors)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed CORS security in {filepath}")

def fix_websocket_imports():
    """Fix import handling in websocket_server.py"""
    filepath = "websocket_server.py"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import error handling
    old_import = "import websockets"
    new_import = '''try:
    import websockets
except ImportError:
    print("Error: websockets module not installed. Run: pip install websockets")
    import sys
    sys.exit(1)'''
    
    if old_import in content and "try:" not in content[:200]:
        content = content.replace(old_import, new_import, 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed import handling in {filepath}")

def fix_bot_launcher_shebang():
    """Fix shebang in bot_launcher.py for better compatibility"""
    filepath = "bot_launcher.py"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix shebang
    if content.startswith("#!/usr/bin/env python3.11"):
        content = content.replace("#!/usr/bin/env python3.11", "#!/usr/bin/env python3", 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed shebang in {filepath}")

def main():
    """Apply all critical fixes"""
    print("Applying critical bug fixes...")
    print("=" * 50)
    
    try:
        fix_bot_launcher_shebang()
        fix_self_aware_module()
        fix_command_interface()
        fix_api_server_cors()
        fix_websocket_imports()
        
        print("\n" + "=" * 50)
        print("Critical fixes applied successfully!")
        print("\nFixed issues:")
        print("✅ Cross-platform disk usage detection")
        print("✅ Secure CORS configuration")
        print("✅ Script execution security")
        print("✅ Hard-coded path replacements")
        print("✅ Import error handling")
        print("✅ Shebang compatibility")
        print("\nBackup files created with .backup extension")
        print("Test the application to ensure fixes work correctly.")
        
    except Exception as e:
        print(f"\nError applying fixes: {e}")
        print("Check backup files and apply fixes manually if needed.")

if __name__ == "__main__":
    main()