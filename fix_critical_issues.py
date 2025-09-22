#!/usr/bin/env python3
"""
Critical Bug Fixes for AI Bot Management System
This script implements the most critical fixes identified in the code analysis.
"""

import os
import sys
import platform
import tempfile

# Cross-platform path fixes
def get_cross_platform_disk_path():
    """Get appropriate disk path for current OS"""
    if platform.system() == "Windows":
        return "C:\\"
    else:
        return "/"

def get_safe_log_directory():
    """Get safe log directory that works on all platforms"""
    if platform.system() == "Windows":
        # Use user's temp directory on Windows
        return os.path.join(tempfile.gettempdir(), "bot_logs")
    else:
        # Use current working directory logs folder
        return os.path.join(os.getcwd(), "logs")

def get_safe_script_directory():
    """Get safe directory for script operations"""
    # Use current working directory instead of hard-coded /home/ubuntu/
    return os.getcwd()

# Error handling decorator
def handle_command_errors(func):
    """Decorator for consistent error handling across command methods"""
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except FileNotFoundError as e:
            error_msg = f"File not found: {e}"
            self.logger.error(error_msg)
            if hasattr(self, 'healing_module') and self.healing_module:
                self.healing_module.handle_error(e, {"operation": func.__name__, "args": args})
            return f"Error: {error_msg}"
        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {e}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error in {func.__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            if hasattr(self, 'healing_module') and self.healing_module:
                self.healing_module.handle_error(e, {"operation": func.__name__, "args": args})
            return f"Error: {error_msg}"
    return wrapper

# Secure subprocess execution
def secure_script_execution(script_path, script_args=None, timeout=60):
    """Securely execute Python scripts with validation"""
    import subprocess
    import os
    
    if script_args is None:
        script_args = []
    
    # Validate script path
    abs_script_path = os.path.abspath(script_path)
    
    # Security checks
    if not os.path.exists(abs_script_path):
        raise FileNotFoundError(f"Script not found: {abs_script_path}")
    
    if not abs_script_path.endswith(".py"):
        raise ValueError(f"Only Python scripts allowed: {abs_script_path}")
    
    # Check if script is in allowed directory (current working directory tree)
    allowed_root = os.path.abspath(os.getcwd())
    if not abs_script_path.startswith(allowed_root):
        raise PermissionError(f"Script outside allowed directory: {abs_script_path}")
    
    # Execute with restrictions
    python_executable = sys.executable
    command = [python_executable, abs_script_path] + script_args
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()  # Run in current directory
        )
        return result
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Script execution timed out after {timeout} seconds")

# CORS security configuration
SECURE_CORS_CONFIG = {
    'origins': ['http://localhost:3000', 'http://localhost:5173', 'https://localhost:5173'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'allow_headers': ['Content-Type', 'Authorization'],
    'expose_headers': ['Content-Range', 'X-Content-Range'],
    'supports_credentials': True,
    'max_age': 600
}

# Standardized error response format
def create_error_response(error_type, message, details=None, status_code=500):
    """Create standardized error response"""
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': message,
            'timestamp': time.time()
        }
    }
    
    if details:
        response['error']['details'] = details
    
    return response, status_code

def create_success_response(data, message=None):
    """Create standardized success response"""
    response = {
        'success': True,
        'data': data,
        'timestamp': time.time()
    }
    
    if message:
        response['message'] = message
    
    return response

# Resource cleanup utilities
class ResourceManager:
    """Manages AI model resources and cleanup"""
    
    def __init__(self):
        self.active_models = {}
        self.memory_threshold = 0.8  # 80% memory usage threshold
    
    def register_model(self, name, model_object):
        """Register a model for resource tracking"""
        self.active_models[name] = {
            'model': model_object,
            'last_used': time.time(),
            'memory_usage': self.get_model_memory_usage(model_object)
        }
    
    def cleanup_unused_models(self, max_age_seconds=3600):
        """Clean up models not used recently"""
        import time
        current_time = time.time()
        
        to_remove = []
        for name, info in self.active_models.items():
            if current_time - info['last_used'] > max_age_seconds:
                to_remove.append(name)
        
        for name in to_remove:
            self.cleanup_model(name)
    
    def cleanup_model(self, name):
        """Clean up specific model"""
        if name in self.active_models:
            model_info = self.active_models[name]
            model = model_info['model']
            
            # Clean up PyTorch models
            if hasattr(model, 'cpu'):
                model.cpu()
            if hasattr(model, 'to'):
                model.to('cpu')
            
            # Clear CUDA cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            del self.active_models[name]
            del model
    
    def get_model_memory_usage(self, model):
        """Estimate model memory usage"""
        try:
            import sys
            return sys.getsizeof(model)
        except:
            return 0
    
    def check_memory_pressure(self):
        """Check if system is under memory pressure"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent > (self.memory_threshold * 100)
        except ImportError:
            return False

# Retry mechanism for network operations
def retry_with_backoff(func, max_retries=3, base_delay=1, backoff_factor=2):
    """Retry function with exponential backoff"""
    import time
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (backoff_factor ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

if __name__ == "__main__":
    print("Critical Bug Fixes Module Loaded")
    print("Available fixes:")
    print("- Cross-platform path handling")
    print("- Secure script execution")
    print("- Standardized error responses")
    print("- Resource management utilities")
    print("- Retry mechanisms for network operations")
    print("- Command error handling decorator")