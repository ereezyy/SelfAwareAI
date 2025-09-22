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
            "analyze_quality": self._handle_analyze_quality,
            "generate_code": self._handle_generate_code,
            "refactor_code": self._handle_refactor_code,
            "auto_fix": self._handle_auto_fix,
            "generate_tests": self._handle_generate_tests,
            "enable_autonomy": self._handle_enable_autonomy,
            "disable_autonomy": self._handle_disable_autonomy,
            "autonomy_status": self._handle_autonomy_status,
            "force_health_check": self._handle_force_health_check,
            "system_optimize": self._handle_system_optimize,
            "recovery_history": self._handle_recovery_history,
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

    def _handle_analyze_quality(self, args):
        """Performs comprehensive code quality analysis (requires SelfCodingModule). Usage: analyze_quality <filepath>"""
        if not args:
            return "Error: Missing filepath. Usage: analyze_quality <filepath>"
        filepath = args[0]
        if self.coding_module:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found for analysis."
            try:
                analysis_result = self.coding_module.analyze_code_quality(abs_filepath)
                if "error" in analysis_result:
                    return f"Error analyzing code quality: {analysis_result['error']}"
                
                # Format the results nicely
                report = f"Code Quality Analysis for {abs_filepath}:\n"
                report += f"Lines of code: {analysis_result.get('line_count', 'N/A')}\n"
                report += f"Complexity score: {analysis_result.get('complexity_score', 'N/A')}\n"
                report += f"Issues found: {len(analysis_result.get('issues', []))}\n"
                report += f"Suggestions: {len(analysis_result.get('suggestions', []))}\n\n"
                
                # List issues
                if analysis_result.get("issues"):
                    report += "Issues:\n"
                    for issue in analysis_result["issues"][:10]:  # Show first 10 issues
                        report += f"  Line {issue.get('line', '?')}: {issue.get('message', 'Unknown issue')} ({issue.get('severity', 'unknown')})\n"
                    if len(analysis_result["issues"]) > 10:
                        report += f"  ... and {len(analysis_result['issues']) - 10} more issues\n"
                    report += "\n"
                
                # List suggestions
                if analysis_result.get("suggestions"):
                    report += "Suggestions:\n"
                    for suggestion in analysis_result["suggestions"][:5]:  # Show first 5 suggestions
                        report += f"  - {suggestion.get('message', 'Unknown suggestion')}\n"
                    if len(analysis_result["suggestions"]) > 5:
                        report += f"  ... and {len(analysis_result['suggestions']) - 5} more suggestions\n"
                
                return report
            except Exception as e:
                self.logger.error(f"Error during quality analysis via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "analyze_quality", "filepath": filepath})
                return f"Error analyzing code quality: {e}"
        return "Error: SelfCodingModule not available for quality analysis."
    
    def _handle_generate_code(self, args):
        """Generates code using templates (requires SelfCodingModule). Usage: generate_code <type> <name> [params...]"""
        if len(args) < 2:
            return "Error: Insufficient arguments. Usage: generate_code <type> <name> [params...]\nAvailable types: class_basic, singleton, context_manager, api_client, unit_test"
        
        code_type = args[0]
        name = args[1]
        
        if self.coding_module:
            try:
                # Parse additional parameters
                params = {"class_name": name}
                for i in range(2, len(args), 2):
                    if i + 1 < len(args):
                        params[args[i]] = args[i + 1]
                
                generated_code = self.coding_module.generate_advanced_code(code_type, **params)
                return f"Generated {code_type} code:\n\n{generated_code}"
            except Exception as e:
                self.logger.error(f"Error during code generation via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "generate_code", "type": code_type})
                return f"Error generating code: {e}"
        return "Error: SelfCodingModule not available for code generation."
    
    def _handle_refactor_code(self, args):
        """Refactors code using various techniques (requires SelfCodingModule). Usage: refactor_code <filepath> <type> [params...]"""
        if len(args) < 2:
            return "Error: Insufficient arguments. Usage: refactor_code <filepath> <type> [params...]\nAvailable types: format_with_black, format_with_autopep8, add_docstrings"
        
        filepath = args[0]
        refactor_type = args[1]
        
        if self.coding_module:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found for refactoring."
            try:
                # Parse additional parameters
                params = {}
                for i in range(2, len(args), 2):
                    if i + 1 < len(args):
                        params[args[i]] = args[i + 1]
                
                success = self.coding_module.refactor_code(abs_filepath, refactor_type, **params)
                if success:
                    return f"Successfully refactored {abs_filepath} using {refactor_type}"
                return f"Failed to refactor {abs_filepath}. Check logs for details."
            except Exception as e:
                self.logger.error(f"Error during code refactoring via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "refactor_code", "filepath": filepath})
                return f"Error refactoring code: {e}"
        return "Error: SelfCodingModule not available for code refactoring."
    
    def _handle_auto_fix(self, args):
        """Automatically fixes common code issues (requires SelfCodingModule). Usage: auto_fix <filepath>"""
        if not args:
            return "Error: Missing filepath. Usage: auto_fix <filepath>"
        filepath = args[0]
        if self.coding_module:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found for auto-fixing."
            try:
                fix_result = self.coding_module.auto_fix_issues(abs_filepath)
                if "error" in fix_result:
                    return f"Error auto-fixing: {fix_result['error']}"
                
                if fix_result.get("success"):
                    fixes = fix_result.get("fixes_applied", [])
                    remaining = fix_result.get("remaining_issues", 0)
                    report = f"Auto-fix completed for {abs_filepath}:\n"
                    if fixes:
                        report += "Fixes applied:\n"
                        for fix in fixes:
                            report += f"  - {fix}\n"
                    else:
                        report += "No automatic fixes were applied.\n"
                    report += f"Remaining issues: {remaining}"
                    return report
                else:
                    return f"Auto-fix failed for {abs_filepath}"
            except Exception as e:
                self.logger.error(f"Error during auto-fix via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "auto_fix", "filepath": filepath})
                return f"Error auto-fixing: {e}"
        return "Error: SelfCodingModule not available for auto-fixing."
    
    def _handle_generate_tests(self, args):
        """Generates unit tests for a Python file (requires SelfCodingModule). Usage: generate_tests <filepath>"""
        if not args:
            return "Error: Missing filepath. Usage: generate_tests <filepath>"
        filepath = args[0]
        if self.coding_module:
            abs_filepath = os.path.abspath(filepath)
            if not os.path.exists(abs_filepath):
                return f"Error: File {abs_filepath} not found for test generation."
            try:
                test_code = self.coding_module.generate_unit_tests(abs_filepath)
                if test_code.startswith("# Error"):
                    return f"Error generating tests: {test_code}"
                
                # Save the test file
                test_filename = f"test_{os.path.basename(abs_filepath)}"
                test_filepath = os.path.join(os.path.dirname(abs_filepath), test_filename)
                
                try:
                    with open(test_filepath, 'w') as f:
                        f.write(test_code)
                    return f"Generated unit tests and saved to {test_filepath}\n\nGenerated test code:\n{test_code[:500]}{'...' if len(test_code) > 500 else ''}"
                except Exception as save_error:
                    return f"Generated test code but failed to save to file: {save_error}\n\nGenerated code:\n{test_code[:500]}{'...' if len(test_code) > 500 else ''}"
                
            except Exception as e:
                self.logger.error(f"Error during test generation via coding module: {e}")
                if self.healing_module:
                    self.healing_module.handle_error(e, {"operation": "generate_tests", "filepath": filepath})
                return f"Error generating tests: {e}"
        return "Error: SelfCodingModule not available for test generation."

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

    def _handle_enable_autonomy(self, args):
        """Enable autonomous self-healing and optimization (requires SelfHealingModule)."""
        if self.healing_module:
            try:
                self.healing_module.enable_autonomy()
                return "✅ Autonomy enabled - Bot will now self-heal and optimize automatically"
            except Exception as e:
                self.logger.error(f"Error enabling autonomy: {e}")
                return f"Error enabling autonomy: {e}"
        return "Error: SelfHealingModule not available for autonomy control."
    
    def _handle_disable_autonomy(self, args):
        """Disable autonomous operation (requires SelfHealingModule)."""
        if self.healing_module:
            try:
                self.healing_module.disable_autonomy()
                return "⏸️ Autonomy disabled - Bot will require manual intervention for issues"
            except Exception as e:
                self.logger.error(f"Error disabling autonomy: {e}")
                return f"Error disabling autonomy: {e}"
        return "Error: SelfHealingModule not available for autonomy control."
    
    def _handle_autonomy_status(self, args):
        """Get comprehensive autonomy and system health status (requires SelfHealingModule)."""
        if self.healing_module:
            try:
                status = self.healing_module.get_autonomy_status()
                
                report = "🤖 AUTONOMY & HEALTH STATUS\n"
                report += "=" * 50 + "\n\n"
                
                # Autonomy status
                autonomy_icon = "✅" if status["autonomy_enabled"] else "⏸️"
                report += f"{autonomy_icon} Autonomy: {'Enabled' if status['autonomy_enabled'] else 'Disabled'}\n"
                
                monitoring_icon = "🔍" if status["health_monitoring"] else "⚠️"
                report += f"{monitoring_icon} Health Monitoring: {'Active' if status['health_monitoring'] else 'Inactive'}\n"
                
                # Health summary
                health = status["health_summary"]
                if health.get("status") != "no_data":
                    health_icon = "💚" if health["status"] == "healthy" else "⚠️"
                    report += f"\n{health_icon} SYSTEM HEALTH:\n"
                    
                    current = health.get("current", {})
                    report += f"  CPU: {current.get('cpu', 0):.1f}%\n"
                    report += f"  Memory: {current.get('memory', 0):.1f}%\n"
                    report += f"  Disk: {current.get('disk', 0):.1f}%\n"
                    report += f"  Response Time: {current.get('response_time', 0):.3f}s\n"
                    
                    # Trends
                    trends = health.get("trends", [])
                    if trends:
                        report += f"\n⚠️ TRENDS DETECTED:\n"
                        for trend in trends:
                            report += f"  - {trend}\n"
                
                # Recovery queue
                queue_size = status["recovery_queue_size"]
                queue_icon = "📋" if queue_size > 0 else "✅"
                report += f"\n{queue_icon} Recovery Queue: {queue_size} pending actions\n"
                
                # Action history
                history = status["action_history"]
                if history:
                    report += f"\n📊 RECENT RECOVERY ACTIONS:\n"
                    for action, stats in list(history.items())[-5:]:  # Last 5 actions
                        success_rate = (stats['successes'] / stats['attempts']) * 100 if stats['attempts'] > 0 else 0
                        report += f"  {action}: {stats['attempts']} attempts, {success_rate:.0f}% success\n"
                
                # Available strategies
                strategies = status["available_strategies"]
                report += f"\n🛠️ Available Recovery Strategies: {len(strategies)}\n"
                report += f"  {', '.join(strategies[:10])}{'...' if len(strategies) > 10 else ''}\n"
                
                return report
                
            except Exception as e:
                self.logger.error(f"Error getting autonomy status: {e}")
                return f"Error getting autonomy status: {e}"
        return "Error: SelfHealingModule not available for status check."
    
    def _handle_force_health_check(self, args):
        """Force an immediate comprehensive health check (requires SelfHealingModule)."""
        if self.healing_module:
            try:
                result = self.healing_module.force_health_check()
                
                report = "🔍 FORCED HEALTH CHECK RESULTS\n"
                report += "=" * 40 + "\n\n"
                
                metrics = result["metrics"]
                report += f"📊 CURRENT METRICS:\n"
                report += f"  CPU Usage: {metrics['cpu_usage']:.1f}%\n"
                report += f"  Memory Usage: {metrics['memory_usage']:.1f}%\n"
                report += f"  Disk Usage: {metrics['disk_usage']:.1f}%\n"
                report += f"  Response Time: {metrics['response_time']:.3f}s\n"
                report += f"  Error Rate: {metrics['error_rate']:.1%}\n"
                
                report += f"\n⏰ Check completed at: {datetime.datetime.fromtimestamp(result['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                # Health assessment
                cpu_status = "🟢" if metrics['cpu_usage'] < 70 else "🟡" if metrics['cpu_usage'] < 90 else "🔴"
                memory_status = "🟢" if metrics['memory_usage'] < 70 else "🟡" if metrics['memory_usage'] < 85 else "🔴"
                disk_status = "🟢" if metrics['disk_usage'] < 80 else "🟡" if metrics['disk_usage'] < 95 else "🔴"
                
                report += f"\n🎯 HEALTH ASSESSMENT:\n"
                report += f"  {cpu_status} CPU: {'Healthy' if metrics['cpu_usage'] < 70 else 'Warning' if metrics['cpu_usage'] < 90 else 'Critical'}\n"
                report += f"  {memory_status} Memory: {'Healthy' if metrics['memory_usage'] < 70 else 'Warning' if metrics['memory_usage'] < 85 else 'Critical'}\n"
                report += f"  {disk_status} Disk: {'Healthy' if metrics['disk_usage'] < 80 else 'Warning' if metrics['disk_usage'] < 95 else 'Critical'}\n"
                
                return report
                
            except Exception as e:
                self.logger.error(f"Error during forced health check: {e}")
                return f"Error during health check: {e}"
        return "Error: SelfHealingModule not available for health checks."
    
    def _handle_system_optimize(self, args):
        """Trigger system optimization and cleanup (requires SelfHealingModule)."""
        if self.healing_module:
            try:
                # Schedule optimization actions
                context = {"manual_trigger": True}
                healing_module = self.healing_module
                
                results = []
                
                # Memory cleanup
                memory_result = healing_module._clear_memory_cache(context)
                results.append(f"Memory cleanup: {memory_result.get('message', 'failed')}")
                
                # Temp file cleanup
                temp_result = healing_module._cleanup_temp_files(context)
                results.append(f"Temp cleanup: {temp_result.get('message', 'failed')}")
                
                # Performance optimization
                perf_result = healing_module._optimize_performance(context)
                results.append(f"Performance: {perf_result.get('message', 'failed')}")
                
                # Log cleanup
                log_result = healing_module._cleanup_old_logs()
                results.append(f"Log cleanup: {log_result.get('message', 'failed')}")
                
                report = "🔧 SYSTEM OPTIMIZATION COMPLETED\n"
                report += "=" * 45 + "\n\n"
                
                for i, result in enumerate(results, 1):
                    report += f"{i}. {result}\n"
                
                # Get final system state
                final_check = healing_module.force_health_check()
                final_metrics = final_check["metrics"]
                
                report += f"\n📊 POST-OPTIMIZATION METRICS:\n"
                report += f"  CPU: {final_metrics['cpu_usage']:.1f}%\n"
                report += f"  Memory: {final_metrics['memory_usage']:.1f}%\n"
                report += f"  Disk: {final_metrics['disk_usage']:.1f}%\n"
                
                return report
                
            except Exception as e:
                self.logger.error(f"Error during system optimization: {e}")
                return f"Error during optimization: {e}"
        return "Error: SelfHealingModule not available for optimization."
    
    def _handle_recovery_history(self, args):
        """Show recovery action history and statistics (requires SelfHealingModule)."""
        if self.healing_module:
            try:
                status = self.healing_module.get_autonomy_status()
                history = status["action_history"]
                
                if not history:
                    return "📊 No recovery actions have been performed yet."
                
                report = "📊 RECOVERY ACTION HISTORY\n"
                report += "=" * 35 + "\n\n"
                
                total_attempts = sum(stats['attempts'] for stats in history.values())
                total_successes = sum(stats['successes'] for stats in history.values())
                overall_success_rate = (total_successes / total_attempts) * 100 if total_attempts > 0 else 0
                
                report += f"📈 OVERALL STATISTICS:\n"
                report += f"  Total Actions: {len(history)}\n"
                report += f"  Total Attempts: {total_attempts}\n"
                report += f"  Success Rate: {overall_success_rate:.1f}%\n\n"
                
                report += f"📋 ACTION DETAILS:\n"
                
                # Sort by most recent
                sorted_history = sorted(history.items(), 
                                      key=lambda x: x[1].get('last_attempt', 0), 
                                      reverse=True)
                
                for action, stats in sorted_history:
                    success_rate = (stats['successes'] / stats['attempts']) * 100 if stats['attempts'] > 0 else 0
                    last_attempt = stats.get('last_attempt', 0)
                    
                    if last_attempt > 0:
                        last_attempt_str = datetime.datetime.fromtimestamp(last_attempt).strftime('%m/%d %H:%M')
                    else:
                        last_attempt_str = "Never"
                    
                    success_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
                    
                    report += f"  {success_icon} {action}:\n"
                    report += f"      Attempts: {stats['attempts']}, Success: {success_rate:.0f}%\n"
                    report += f"      Last: {last_attempt_str}\n"
                
                return report
                
            except Exception as e:
                self.logger.error(f"Error getting recovery history: {e}")
                return f"Error getting recovery history: {e}"
        return "Error: SelfHealingModule not available for history."

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

