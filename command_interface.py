# command_interface.py

import logging
import shlex
import os
import json
import inspect
import subprocess
import time # For mock module

# Actual module imports
from self_aware_module import SelfAwareModule
from self_healing_coding_module import SelfHealingModule, SelfCodingModule
from text_humanization_module import TextHumanizer
from ai_text_detection_module import AITextDetector

# --- Logger Setup ---
LOG_FILE_CI = "/home/ubuntu/bot_command_interface.log"

def setup_logger_ci(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

ci_logger = setup_logger_ci("CommandInterfaceLogger", LOG_FILE_CI)

class CommandInterface:
    def __init__(self, awareness_module=None, coding_module=None, healing_module=None, humanizer_module=None, ai_detector_module=None):
        self.logger = ci_logger
        self.awareness_module = awareness_module
        self.coding_module = coding_module
        self.healing_module = healing_module
        self.humanizer_module = humanizer_module
        self.ai_detector_module = ai_detector_module
        
        self.commands = {
            "help": self._handle_help,
            "status": self._handle_status,
            "create_file": self._handle_create_file,
            "read_file": self._handle_read_file,
            "update_file_content": self._handle_update_file_content,
            "append_to_file": self._handle_append_to_file,
            "analyze_code": self._handle_analyze_code,
            "patch_code": self._handle_patch_code,
            "modify_config": self._handle_modify_config,
            "run_python_script": self._handle_run_python_script,
            "humanize_text": self._handle_humanize_text,
            "detect_ai_text": self._handle_detect_ai_text
        }
        self.logger.info("CommandInterface initialized.")

    def _handle_help(self, args):
        """Displays available commands and their usage."""
        help_text = "Available commands:\n"
        for cmd, handler in self.commands.items():
            docstring = inspect.getdoc(handler) or "No description available."
            help_text += f"  {cmd}: {docstring.splitlines()[0]}\n"
            if cmd == "detect_ai_text":
                 help_text += "    Note: This AI detection model may misclassify human-written text as AI-generated. Interpret results with caution.\n"
        return help_text

    def _handle_status(self, args):
        """Retrieves the bot"s current operational status (requires SelfAwareModule)."""
        if self.awareness_module:
            try:
                health_report = self.awareness_module.report_health()
                return json.dumps(health_report, indent=2)
            except Exception as e:
                self.logger.error(f"Error getting status from awareness module: {e}")
                return f"Error retrieving status: {e}"
        return "Status: SelfAwareModule not available."

    def _handle_create_file(self, args):
        """Creates a new file with optional content. Usage: create_file <filepath> [content]"""
        if not args:
            return "Error: Missing filepath. Usage: create_file <filepath> [content]"
        filepath = args[0]
        content = " ".join(args[1:]) if len(args) > 1 else ""
        try:
            abs_filepath = os.path.abspath(filepath)
            if os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} already exists."
            with open(abs_filepath, "w") as f:
                f.write(content)
            self.logger.info(f"File created: {abs_filepath}")
            return f"File created: {abs_filepath}"
        except Exception as e:
            self.logger.error(f"Error creating file {filepath}: {e}")
            if self.healing_module:
                self.healing_module.handle_error(e, {"operation": "create_file", "filepath": filepath})
            return f"Error creating file: {e}"

    def _handle_read_file(self, args):
        """Reads the content of a specified file. Usage: read_file <filepath>"""
        if not args:
            return "Error: Missing filepath. Usage: read_file <filepath>"
        filepath = args[0]
        try:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found."
            with open(abs_filepath, "r") as f:
                content = f.read()
            self.logger.info(f"Read file: {abs_filepath}")
            return f"Content of {abs_filepath}:\n{content}"
        except Exception as e:
            self.logger.error(f"Error reading file {filepath}: {e}")
            if self.healing_module:
                self.healing_module.handle_error(e, {"operation": "read_file", "filepath": filepath})
            return f"Error reading file: {e}"

    def _handle_update_file_content(self, args):
        """Overwrites the content of a specified file. Usage: update_file_content <filepath> <new_content>"""
        if len(args) < 2:
            return "Error: Missing filepath or content. Usage: update_file_content <filepath> <new_content>"
        filepath = args[0]
        content = " ".join(args[1:])
        try:
            abs_filepath = os.path.abspath(filepath)
            with open(abs_filepath, "w") as f:
                f.write(content)
            self.logger.info(f"File content updated: {abs_filepath}")
            return f"File content updated: {abs_filepath}"
        except Exception as e:
            self.logger.error(f"Error updating file {filepath}: {e}")
            if self.healing_module:
                self.healing_module.handle_error(e, {"operation": "update_file", "filepath": filepath})
            return f"Error updating file: {e}"

    def _handle_append_to_file(self, args):
        """Appends content to a specified file. Usage: append_to_file <filepath> <content_to_append>"""
        if len(args) < 2:
            return "Error: Missing filepath or content. Usage: append_to_file <filepath> <content_to_append>"
        filepath = args[0]
        content_to_append = " ".join(args[1:])
        try:
            abs_filepath = os.path.abspath(filepath)
            with open(abs_filepath, "a") as f:
                f.write(content_to_append + "\n") 
            self.logger.info(f"Content appended to: {abs_filepath}")
            return f"Content appended to: {abs_filepath}"
        except Exception as e:
            self.logger.error(f"Error appending to file {filepath}: {e}")
            if self.healing_module:
                self.healing_module.handle_error(e, {"operation": "append_to_file", "filepath": filepath})
            return f"Error appending to file: {e}"

    def _handle_analyze_code(self, args):
        """Analyzes the structure of a code file (requires SelfCodingModule). Usage: analyze_code <filepath>"""
        if not args:
            return "Error: Missing filepath. Usage: analyze_code <filepath>"
        filepath = args[0]
        if self.coding_module:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found for analysis."
            try:
                analysis_result = self.coding_module.analyze_code_structure(abs_filepath)
                if "error" in analysis_result:
                    # Corrected f-string to use single quotes for dictionary key
                    return f"Error analyzing code: {analysis_result['error']}"
                return f"Code analysis for {abs_filepath}:\n{json.dumps(analysis_result, indent=2)}"
            except Exception as e:
                self.logger.error(f"Error during code analysis via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "analyze_code", "filepath": filepath})
                return f"Error analyzing code: {e}"
        return "Error: SelfCodingModule not available for code analysis."

    def _handle_patch_code(self, args):
        """Applies a simple string patch to a file (requires SelfCodingModule). Usage: patch_code <filepath> \"<old_string>\" \"<new_string>\""""
        if len(args) < 3:
            return "Error: Insufficient arguments. Usage: patch_code <filepath> \"<old_string>\" \"<new_string>\""
        filepath, old_string, new_string = args[0], args[1], args[2]
        if self.coding_module:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found for patching."
            try:
                success = self.coding_module.apply_simple_code_patch(abs_filepath, old_string, new_string)
                if success:
                    return f"Successfully patched {abs_filepath}."
                return f"Failed to patch {abs_filepath}. Check logs or if old_string was found."
            except Exception as e:
                self.logger.error(f"Error during code patching via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "patch_code", "filepath": filepath})
                return f"Error patching code: {e}"
        return "Error: SelfCodingModule not available for patching code."

    def _handle_modify_config(self, args):
        """Modifies a parameter in a JSON config file (requires SelfCodingModule). Usage: modify_config <config_filepath> <parameter_key> <new_json_value>"""
        if len(args) < 3:
            return "Error: Insufficient arguments. Usage: modify_config <config_filepath> <parameter_key> <new_json_value>"
        config_filepath, param_key = args[0], args[1]
        try:
            new_value_str = " ".join(args[2:])
            new_value = json.loads(new_value_str) 
        except json.JSONDecodeError:
            return f"Error: Invalid JSON value provided for new_value: {new_value_str}"

        if self.coding_module:
            abs_config_filepath = os.path.abspath(config_filepath)
            if not os.path.exists(abs_config_filepath):
                return f"Error: Config file {abs_config_filepath} not found."
            try:
                success = self.coding_module.modify_config_parameter(abs_config_filepath, param_key, new_value)
                if success:
                    return f"Successfully modified {param_key} in {abs_config_filepath}."
                return f"Failed to modify config {abs_config_filepath}. Check logs."
            except Exception as e:
                self.logger.error(f"Error during config modification via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "modify_config", "filepath": config_filepath})
                return f"Error modifying config: {e}"
        return "Error: SelfCodingModule not available for modifying config."

    def _handle_run_python_script(self, args):
        """Runs a specified Python script. Usage: run_python_script <filepath> [script_args...]"""
        if not args:
            return "Error: Missing script filepath. Usage: run_python_script <filepath> [script_args...]"
        script_path = args[0]
        script_args = args[1:]
        abs_script_path = os.path.abspath(script_path)

        if not os.path.exists(abs_script_path):
            return f"Error: Script file {abs_script_path} not found."
        if not abs_script_path.endswith(".py"):
            return f"Error: File {abs_script_path} is not a Python script (.py)."

        try:
            self.logger.info(f"Executing Python script: {abs_script_path} with args: {script_args}")
            python_executable = "python3.11"
            command = [python_executable, abs_script_path] + script_args
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            output = f"--- Script: {script_path} ---\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            output += f"Return Code: {result.returncode}"
            self.logger.info(f"Script {abs_script_path} execution finished. Return code: {result.returncode}")
            return output
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Script {abs_script_path} timed out.")
            return f"Error: Script {abs_script_path} timed out after 60 seconds."
        except Exception as e:
            self.logger.error(f"Error running script {abs_script_path}: {e}")
            if self.healing_module:
                self.healing_module.handle_error(e, {"operation": "run_script", "filepath": abs_script_path})
            return f"Error running script {abs_script_path}: {e}"

    def _handle_humanize_text(self, args):
        """Humanizes the provided text using the TextHumanizer module. Usage: humanize_text \"<text_to_humanize>\""""
        if not args:
            return "Error: Missing text to humanize. Usage: humanize_text \"<text_to_humanize>\""
        text_to_humanize = " ".join(args)
        if self.humanizer_module:
            try:
                humanized_versions = self.humanizer_module.humanize_text(text_to_humanize)
                if humanized_versions and isinstance(humanized_versions, list) and humanized_versions[0].startswith("Error:"):
                    return f"Humanization failed: {humanized_versions[0]}"
                return f"Humanized versions:\n" + "\n".join([f"- {v}" for v in humanized_versions])
            except Exception as e:
                self.logger.error(f"Error during text humanization via humanizer module: {e}")
                return f"Error humanizing text: {e}"
        return "Error: TextHumanizerModule not available."

    def _handle_detect_ai_text(self, args):
        """Detects if the provided text is AI-generated (requires AITextDetectorModule). Usage: detect_ai_text \"<text_to_analyze>\""""
        if not args:
            return "Error: Missing text to analyze. Usage: detect_ai_text \"<text_to_analyze>\""
        text_to_analyze = " ".join(args)
        if self.ai_detector_module:
            try:
                detection_result = self.ai_detector_module.detect_ai_text(text_to_analyze)
                if "error" in detection_result:
                    # Corrected f-string to use single quotes for dictionary key
                    return f"AI text detection failed: {detection_result['error']}\n{detection_result.get('warning', '')}"
                
                result_str = f"AI Detection Results:\n  Human Probability: {detection_result.get('Human', 'N/A'):.4f}\n  AI Probability:    {detection_result.get('AI', 'N/A'):.4f}\n"
                if "warning" in detection_result:
                    result_str += f"\nWarning: {detection_result['warning']}"
                return result_str
            except Exception as e:
                self.logger.error(f"Error during AI text detection via AI detector module: {e}")
                return f"Error detecting AI text: {e}"
        return "Error: AITextDetectorModule not available."

    def process_command(self, command_string):
        self.logger.info(f"Received command string: {command_string!r}")
        try:
            parts = shlex.split(command_string)
        except ValueError as e:
            self.logger.error(f"Error parsing command string {command_string!r}: {e}")
            return f"Error: Invalid command string. Check quotes and special characters. Details: {e}"
        
        if not parts:
            return "Error: Empty command."
        
        command_name = parts[0].lower()
        args_list = parts[1:]
        
        handler = self.commands.get(command_name)
        if handler:
            self.logger.info(f"Executing command {command_name} with args: {args_list}")
            try:
                return handler(args_list)
            except Exception as e:
                self.logger.exception(f"Unhandled exception during execution of command {command_name}: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": f"command_{command_name}", "args": args_list})
                return f"Error executing command {command_name}: {type(e).__name__} - {e}. Check logs for details."
        else:
            self.logger.warning(f"Unknown command: {command_name!r}")
            return f"Error: Unknown command {command_name!r}. Type \"help\" for available commands."

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing actual modules for CommandInterface test...")
    try:
        awareness_module = SelfAwareModule()
        healing_module = SelfHealingModule(awareness_module=awareness_module)
        coding_module = SelfCodingModule(awareness_module=awareness_module) # Corrected: Removed healing_module
        humanizer_module = TextHumanizer() # Downloads model on init
        ai_detector_module = AITextDetector() # Downloads model on init
        print("All modules initialized.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize one or more core modules: {e}")
        ci_logger.critical(f"Failed to initialize core modules in __main__: {e}", exc_info=True)
        class MockAwarenessModule:
            def report_health(self): return {"status": "MOCK_OK"}
            def log_event(self, *args, **kwargs): pass
            def update_module_health(self, *args, **kwargs): pass
        class MockHealingModule:
            def handle_error(self, error, context): ci_logger.warning(f"MOCK_HEALING: {error}"); return {}
        class MockCodingModule:
            def analyze_code_structure(self, fp): 
                if fp == "/home/ubuntu/error_trigger.py":
                    return {"error": "Simulated analysis error from mock"}
                return {"mock_analysis": fp}
            def apply_simple_code_patch(self, fp, o, n): return True
            def modify_config_parameter(self, fp, k, v): return True
        class MockHumanizer:
            def humanize_text(self, text): return [f"Mock humanized: {text}"]
        class MockAIDetector:
            def detect_ai_text(self, text): return {"Human": 0.5, "AI": 0.5, "warning": "Mock AI Detection"}
        
        awareness_module = MockAwarenessModule()
        healing_module = MockHealingModule()
        coding_module = MockCodingModule()
        humanizer_module = MockHumanizer()
        ai_detector_module = MockAIDetector()
        print("Fell back to Mock Modules due to initialization error.")

    cmd_interface = CommandInterface(
        awareness_module=awareness_module, 
        healing_module=healing_module,
        coding_module=coding_module,
        humanizer_module=humanizer_module,
        ai_detector_module=ai_detector_module
    )

    print("Command Interface Test with integrated modules. Type \"exit\" or \"quit\" to stop.")
    
    dummy_script_path = "/home/ubuntu/dummy_test_script_ci.py"
    with open(dummy_script_path, "w") as f:
        f.write("import sys\nprint(\"Hello from CI dummy script!\")\nprint(f\"Script arguments: {sys.argv[1:]}\")\nsys.exit(0)\n")

    dummy_config_path = "/home/ubuntu/dummy_config_ci.json"
    with open(dummy_config_path, "w") as f:
        json.dump({"setting1": "value1", "nested": {"key": "original"}}, f, indent=2)

    error_trigger_path = "/home/ubuntu/error_trigger.py"
    with open(error_trigger_path, "w") as f:
        f.write("# This file is used to trigger a simulated error in analyze_code")

    test_commands = [
        "help",
        "status",
        "create_file /home/ubuntu/testfile_ci.txt \"Initial content for CI test\"",
        "read_file /home/ubuntu/testfile_ci.txt",
        "humanize_text \"This is a simple sentence that I want to make sound more natural.\"",
        "detect_ai_text \"This text was definitely written by a human being, I swear it.\"",
        "detect_ai_text \"Leveraging synergistic paradigms, we aim to optimize bleeding-edge infrastructures.\"",
        f"analyze_code {dummy_script_path}",
        f"analyze_code {error_trigger_path}",
        "unknown_command_test",
    ]

    for cmd_str in test_commands:
        print(f"\n>>> CMD: {cmd_str}")
        response = cmd_interface.process_command(cmd_str)
        print(f"<<< RESPONSE:\n{response}")

    print(f"\nLog file for Command Interface: {LOG_FILE_CI}")
    print(f"Log file for Self Aware Module: {awareness_module.log_file if hasattr(awareness_module, 'log_file') else 'N/A or Mock'}")
    print(f"Log file for Self Healing/Coding Module: {coding_module.logger.handlers[0].baseFilename if hasattr(coding_module, 'logger') and coding_module.logger.handlers else 'N/A or Mock'}")
    print(f"Log file for Text Humanizer: {humanizer_module.logger.handlers[0].baseFilename if hasattr(humanizer_module, 'logger') and humanizer_module.logger.handlers else 'N/A or Mock'}")
    print(f"Log file for AI Detector: {ai_detector_module.logger.handlers[0].baseFilename if hasattr(ai_detector_module, 'logger') and ai_detector_module.logger.handlers else 'N/A or Mock'}")

    # Cleanup
    if os.path.exists("/home/ubuntu/testfile_ci.txt"): os.remove("/home/ubuntu/testfile_ci.txt")
    if os.path.exists(dummy_script_path): os.remove(dummy_script_path)
    if os.path.exists(dummy_config_path): os.remove(dummy_config_path)
    if os.path.exists(error_trigger_path): os.remove(error_trigger_path)
    print("Cleaned up test files.")
    print("Test finished.")

