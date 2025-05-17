# self_healing_coding_module.py

import logging
import os
import sys
import ast
import json
import traceback
import importlib.util
import inspect
import re
from typing import Dict, List, Any, Tuple, Optional, Union

# --- Logger Setup ---
LOG_FILE_SHC = "/home/ubuntu/bot_self_healing_coding.log"

def setup_logger_shc(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

shc_logger = setup_logger_shc("SelfHealingCodingLogger", LOG_FILE_SHC)

class SelfHealingModule:
    def __init__(self, awareness_module=None):
        self.logger = shc_logger
        self.awareness_module = awareness_module
        self.error_handlers = {}
        self.recovery_strategies = {
            "ModuleImportError": self._handle_import_error,
            "FileNotFoundError": self._handle_file_not_found,
            "SyntaxError": self._handle_syntax_error,
            "PermissionError": self._handle_permission_error,
            "JSONDecodeError": self._handle_json_decode_error,
            "Default": self._handle_default_error
        }
        self.logger.info("SelfHealingModule initialized.")
        
        # Register with awareness module if available
        if self.awareness_module:
            self.awareness_module.update_module_health("SelfHealingModule", "OK", "Initialized")
    
    def register_error_handler(self, error_type: str, handler_func):
        """Register a custom error handler for a specific error type."""
        self.recovery_strategies[error_type] = handler_func
        self.logger.info(f"Registered custom handler for {error_type}")
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main error handling method that dispatches to appropriate recovery strategy.
        Args:
            error: The exception that was raised
            context: Additional information about the error context
        Returns:
            Dict containing recovery status and any relevant information
        """
        if context is None:
            context = {}
        
        error_type = type(error).__name__
        error_msg = str(error)
        
        self.logger.error(f"Handling error: {error_type} - {error_msg}")
        if self.awareness_module:
            self.awareness_module.log_event(
                f"Error detected: {error_type} - {error_msg}", 
                logging.ERROR, 
                "SelfHealingModule"
            )
        
        # Get traceback information
        tb_info = traceback.format_exc()
        context["traceback"] = tb_info
        
        # Find appropriate handler
        handler = self.recovery_strategies.get(error_type, self.recovery_strategies["Default"])
        
        try:
            recovery_result = handler(error, context)
            if recovery_result.get("success", False):
                self.logger.info(f"Successfully recovered from {error_type}")
                if self.awareness_module:
                    self.awareness_module.update_module_health(
                        "SelfHealingModule", 
                        "OK", 
                        f"Recovered from {error_type}"
                    )
            else:
                self.logger.warning(f"Failed to recover from {error_type}: {recovery_result.get('message', 'Unknown reason')}")
                if self.awareness_module:
                    self.awareness_module.update_module_health(
                        "SelfHealingModule", 
                        "WARNING", 
                        f"Failed recovery: {error_type}"
                    )
            return recovery_result
        except Exception as recovery_error:
            self.logger.error(f"Error in recovery handler: {recovery_error}", exc_info=True)
            if self.awareness_module:
                self.awareness_module.update_module_health(
                    "SelfHealingModule", 
                    "ERROR", 
                    f"Recovery handler failed: {recovery_error}"
                )
            return {
                "success": False,
                "message": f"Recovery handler failed: {recovery_error}",
                "original_error": f"{error_type}: {error_msg}"
            }
    
    # --- Default Recovery Strategies ---
    
    def _handle_import_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle module import errors by suggesting installation."""
        module_name = context.get("module_name", "unknown_module")
        if not module_name or module_name == "unknown_module":
            # Try to extract module name from error message
            error_msg = str(error)
            match = re.search(r"No module named '([^']+)'", error_msg)
            if match:
                module_name = match.group(1)
        
        self.logger.info(f"Suggesting installation for missing module: {module_name}")
        return {
            "success": False,  # We can't automatically install packages
            "message": f"Module '{module_name}' is missing. Try installing it with 'pip install {module_name}'.",
            "recovery_action": "suggest_installation",
            "module_name": module_name
        }
    
    def _handle_file_not_found(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file not found errors."""
        file_path = context.get("file_path", "")
        if not file_path:
            # Try to extract file path from error message
            error_msg = str(error)
            match = re.search(r"No such file or directory: '([^']+)'", error_msg)
            if match:
                file_path = match.group(1)
        
        # Check if it's a directory issue
        dir_path = os.path.dirname(file_path) if file_path else ""
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.info(f"Created missing directory: {dir_path}")
                return {
                    "success": True,
                    "message": f"Created missing directory: {dir_path}",
                    "recovery_action": "created_directory",
                    "directory": dir_path
                }
            except Exception as dir_error:
                self.logger.error(f"Failed to create directory {dir_path}: {dir_error}")
        
        return {
            "success": False,
            "message": f"File not found: {file_path}",
            "recovery_action": "report_missing_file",
            "file_path": file_path
        }
    
    def _handle_syntax_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle syntax errors in code."""
        file_path = context.get("file_path", "")
        line_no = getattr(error, "lineno", None)
        offset = getattr(error, "offset", None)
        
        error_info = {
            "success": False,
            "message": f"Syntax error in {file_path or 'code'} at line {line_no or 'unknown'}: {error}",
            "recovery_action": "report_syntax_error",
            "file_path": file_path,
            "line_no": line_no,
            "offset": offset,
            "error_text": str(error)
        }
        
        self.logger.error(f"Syntax error detected: {error_info['message']}")
        return error_info
    
    def _handle_permission_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle permission errors."""
        file_path = context.get("file_path", "")
        if not file_path:
            # Try to extract file path from error message
            error_msg = str(error)
            match = re.search(r"Permission denied: '([^']+)'", error_msg)
            if match:
                file_path = match.group(1)
        
        return {
            "success": False,
            "message": f"Permission error for {file_path}: {error}",
            "recovery_action": "report_permission_error",
            "file_path": file_path
        }
    
    def _handle_json_decode_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON decoding errors."""
        file_path = context.get("file_path", "")
        
        error_info = {
            "success": False,
            "message": f"JSON decode error in {file_path or 'data'}: {error}",
            "recovery_action": "report_json_error",
            "file_path": file_path
        }
        
        # If we have the file path, we could try to validate the JSON
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Simple validation attempt - look for common JSON errors
                if content.strip() == "":
                    error_info["message"] += " (File is empty)"
                elif not (content.strip().startswith('{') or content.strip().startswith('[')):
                    error_info["message"] += " (Not a valid JSON object/array)"
                # More validation could be added here
                
            except Exception as read_error:
                self.logger.error(f"Error reading JSON file for validation: {read_error}")
        
        return error_info
    
    def _handle_default_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default error handler for unspecified error types."""
        return {
            "success": False,
            "message": f"Unhandled error: {type(error).__name__} - {error}",
            "recovery_action": "report_error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }


class SelfCodingModule:
    def __init__(self, awareness_module=None):
        self.logger = shc_logger
        self.awareness_module = awareness_module
        self.logger.info("SelfCodingModule initialized.")
        
        # Register with awareness module if available
        if self.awareness_module:
            self.awareness_module.update_module_health("SelfCodingModule", "OK", "Initialized")
    
    def analyze_code_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze the structure of a Python code file.
        Args:
            file_path: Path to the Python file to analyze
        Returns:
            Dict containing analysis results (functions, classes, imports, etc.)
        """
        self.logger.info(f"Analyzing code structure: {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Extract information
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(d).strip() for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                    }
                    functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "bases": [ast.unparse(b).strip() for b in node.bases] if hasattr(ast, 'unparse') else [],
                        "methods": []
                    }
                    
                    # Extract methods
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            method_info = {
                                "name": child.name,
                                "line_number": child.lineno,
                                "args": [arg.arg for arg in child.args.args]
                            }
                            class_info["methods"].append(method_info)
                    
                    classes.append(class_info)
                
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append({"name": name.name, "alias": name.asname})
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        imports.append({
                            "name": f"{module}.{name.name}" if module else name.name,
                            "alias": name.asname,
                            "from_import": True
                        })
            
            analysis_result = {
                "file_path": file_path,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "total_functions": len(functions),
                "total_classes": len(classes),
                "total_imports": len(imports)
            }
            
            self.logger.info(f"Code analysis completed for {file_path}: {len(functions)} functions, {len(classes)} classes")
            return analysis_result
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return {
                "error": f"Syntax error in {file_path}: {e}",
                "line_number": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}", exc_info=True)
            return {"error": f"Error analyzing {file_path}: {e}"}
    
    def apply_simple_code_patch(self, file_path: str, old_str: str, new_str: str) -> bool:
        """
        Apply a simple string replacement patch to a file.
        Args:
            file_path: Path to the file to patch
            old_str: String to replace
            new_str: Replacement string
        Returns:
            Boolean indicating success
        """
        self.logger.info(f"Applying code patch to {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if old_str not in content:
                self.logger.warning(f"String to replace not found in {file_path}")
                return False
            
            # Apply the patch
            new_content = content.replace(old_str, new_str)
            
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            self.logger.info(f"Successfully patched {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error patching {file_path}: {e}", exc_info=True)
            return False
    
    def modify_config_parameter(self, config_file: str, param_key: str, new_value: Any) -> bool:
        """
        Modify a parameter in a JSON configuration file.
        Args:
            config_file: Path to the JSON config file
            param_key: Parameter key to modify (supports dot notation for nested keys)
            new_value: New value for the parameter
        Returns:
            Boolean indicating success
        """
        self.logger.info(f"Modifying config parameter {param_key} in {config_file}")
        
        if not os.path.exists(config_file):
            self.logger.error(f"Config file not found: {config_file}")
            return False
        
        try:
            # Read the config file
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Parse the parameter key (support for nested keys with dot notation)
            key_parts = param_key.split('.')
            
            # Navigate to the nested location
            current = config
            for i, part in enumerate(key_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value
            current[key_parts[-1]] = new_value
            
            # Write back to the file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Successfully modified {param_key} in {config_file}")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {config_file}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error modifying config {config_file}: {e}", exc_info=True)
            return False
    
    def generate_simple_function(self, function_name: str, args: List[str], body: str, docstring: str = None) -> str:
        """
        Generate a simple Python function based on specifications.
        Args:
            function_name: Name of the function
            args: List of argument names
            body: Function body code
            docstring: Optional docstring
        Returns:
            String containing the generated function code
        """
        self.logger.info(f"Generating function: {function_name}")
        
        # Format the arguments
        args_str = ", ".join(args)
        
        # Format the docstring if provided
        doc_str = f'    """{docstring}"""\n' if docstring else ""
        
        # Indent the body
        body_lines = body.strip().split('\n')
        indented_body = "\n".join(f"    {line}" for line in body_lines)
        
        # Assemble the function
        function_code = f"def {function_name}({args_str}):\n{doc_str}{indented_body}\n"
        
        self.logger.info(f"Generated function {function_name} with {len(args)} arguments")
        return function_code
    
    def validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate Python code syntax without executing it.
        Args:
            code: Python code to validate
        Returns:
            Dict with validation results
        """
        self.logger.info("Validating Python syntax")
        
        try:
            ast.parse(code)
            return {"valid": True, "message": "Syntax is valid"}
        except SyntaxError as e:
            self.logger.warning(f"Syntax error: {e}")
            return {
                "valid": False,
                "message": f"Syntax error: {e}",
                "line_number": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            self.logger.error(f"Error validating syntax: {e}")
            return {"valid": False, "message": f"Error: {e}"}

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing SelfHealingModule and SelfCodingModule for testing...")
    
    # Create a simple test file
    test_file_path = "/home/ubuntu/test_code.py"
    with open(test_file_path, 'w') as f:
        f.write("""
import os
import sys

def hello_world():
    \"\"\"A simple hello world function.\"\"\"
    print("Hello, World!")
    return True

class TestClass:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"

def add_numbers(a, b):
    return a + b
""")
    
    # Create a test JSON config
    test_config_path = "/home/ubuntu/test_config.json"
    with open(test_config_path, 'w') as f:
        f.write("""
{
  "app": {
    "name": "TestApp",
    "version": "1.0.0"
  },
  "settings": {
    "debug": false,
    "log_level": "info"
  }
}
""")
    
    # Initialize modules
    healing_module = SelfHealingModule()
    coding_module = SelfCodingModule()
    
    print("\n--- Testing Code Analysis ---")
    analysis = coding_module.analyze_code_structure(test_file_path)
    print(f"Functions found: {len(analysis.get('functions', []))}")
    print(f"Classes found: {len(analysis.get('classes', []))}")
    
    print("\n--- Testing Code Patching ---")
    patch_result = coding_module.apply_simple_code_patch(
        test_file_path,
        'def hello_world():',
        'def hello_universe():'
    )
    print(f"Patch applied: {patch_result}")
    
    print("\n--- Testing Config Modification ---")
    config_result = coding_module.modify_config_parameter(
        test_config_path,
        'settings.debug',
        True
    )
    print(f"Config modified: {config_result}")
    
    print("\n--- Testing Function Generation ---")
    new_function = coding_module.generate_simple_function(
        "calculate_area",
        ["radius"],
        "import math\nreturn math.pi * radius * radius",
        "Calculate the area of a circle given its radius."
    )
    print(f"Generated function:\n{new_function}")
    
    print("\n--- Testing Syntax Validation ---")
    valid_code = "def test(): return 42"
    invalid_code = "def test() return 42"
    
    valid_result = coding_module.validate_python_syntax(valid_code)
    invalid_result = coding_module.validate_python_syntax(invalid_code)
    
    print(f"Valid code check: {valid_result['valid']}")
    print(f"Invalid code check: {invalid_result['valid']}")
    
    print("\n--- Testing Error Handling ---")
    try:
        # Simulate a file not found error
        with open("/nonexistent/file.txt", 'r') as f:
            content = f.read()
    except Exception as e:
        recovery_result = healing_module.handle_error(e, {"file_path": "/nonexistent/file.txt"})
        print(f"Recovery result: {recovery_result['message']}")
    
    print(f"\nSelf-Healing and Self-Coding Module log file located at: {LOG_FILE_SHC}")
    print("Test finished.")
