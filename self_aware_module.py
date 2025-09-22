# self_aware_module.py

import logging
import psutil
import os
import time
import json

# --- Logger Setup ---
# Create logs directory in current working directory for cross-platform compatibility
LOGS_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_SA = os.path.join(LOGS_DIR, "bot_self_aware.log")

def setup_logger_sa(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Avoid adding handlers multiple times if the logger is re-initialized
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

sa_logger = setup_logger_sa("SelfAwarenessLogger", LOG_FILE_SA)

class SelfAwareModule:
    def __init__(self):
        self.logger = sa_logger
        self.start_time = time.time()
        self.module_health = {"SelfAwareModule": "OK"} # Tracks health of this and other modules
        self.logger.info("SelfAwareModule initialized.")

    def get_system_metrics(self):
        """Retrieves current system metrics (CPU, memory, disk)."""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_usage = psutil.disk_usage("/")
            
            metrics = {
                "cpu_usage_percent": cpu_usage,
                "memory_total_gb": round(memory_info.total / (1024**3), 2),
                "memory_available_gb": round(memory_info.available / (1024**3), 2),
                "memory_used_percent": memory_info.percent,
                "disk_total_gb": round(disk_usage.total / (1024**3), 2),
                "disk_used_gb": round(disk_usage.used / (1024**3), 2),
                "disk_free_gb": round(disk_usage.free / (1024**3), 2),
                "disk_used_percent": disk_usage.percent
            }
            self.logger.debug(f"System metrics retrieved: {metrics}")
            return metrics
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}", exc_info=True)
            return {"error": f"Failed to retrieve system metrics: {e}"}

    def get_bot_uptime(self):
        """Calculates and returns the bot\"s uptime."""
        uptime_seconds = time.time() - self.start_time
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        self.logger.debug(f"Bot uptime: {uptime_str}")
        return uptime_str

    def log_event(self, message, level=logging.INFO, module_name="SelfAwareModule"):
        """Logs an event with a specified severity level."""
        log_entry = f"[{module_name}] {message}"
        if level == logging.DEBUG:
            self.logger.debug(log_entry)
        elif level == logging.INFO:
            self.logger.info(log_entry)
        elif level == logging.WARNING:
            self.logger.warning(log_entry)
        elif level == logging.ERROR:
            self.logger.error(log_entry)
        elif level == logging.CRITICAL:
            self.logger.critical(log_entry)
        else:
            self.logger.info(log_entry) # Default to INFO for unknown levels

    def update_module_health(self, module_name, status="OK", details=""):
        """Updates the health status of a specific module."""
        self.module_health[module_name] = {"status": status, "details": details, "last_updated": time.time()}
        self.logger.info(f"Health status updated for {module_name}: {status} - {details}")

    def report_health(self):
        """Generates a comprehensive health report for the bot."""
        self.update_module_health("SelfAwareModule", "OK") # Update its own health before reporting
        report = {
            "overall_status": "OK" if all(m.get("status", "ERROR") == "OK" for m in self.module_health.values()) else "WARNING",
            "bot_uptime": self.get_bot_uptime(),
            "system_metrics": self.get_system_metrics(),
            "module_health_details": self.module_health,
            "log_file_location": LOG_FILE_SA,
            "timestamp": time.time()
        }
        self.logger.info("Health report generated.")
        return report

    def perform_self_check(self):
        """Performs a basic self-check of the module."""
        self.logger.info("Performing self-check...")
        try:
            metrics = self.get_system_metrics()
            if "error" in metrics:
                self.update_module_health("SelfAwareModule", "ERROR", "Failed to get system metrics.")
                self.logger.error("Self-check failed: Could not retrieve system metrics.")
                return False
            self.update_module_health("SelfAwareModule", "OK", "Self-check passed.")
            self.logger.info("Self-check completed successfully.")
            return True
        except Exception as e:
            self.update_module_health("SelfAwareModule", "ERROR", f"Self-check exception: {e}")
            self.logger.critical(f"Critical error during self-check: {e}", exc_info=True)
            return False

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing SelfAwareModule for testing...")
    awareness_module = SelfAwareModule()
    
    print("\n--- Performing Self-Check ---")
    check_result = awareness_module.perform_self_check()
    # Corrected f-string to use single quotes for inner strings
    print(f"Self-check result: {'PASSED' if check_result else 'FAILED'}")

    print("\n--- Logging Test Events ---")
    awareness_module.log_event("This is a test debug message.", logging.DEBUG)
    awareness_module.log_event("This is a test info message.")
    awareness_module.log_event("This is a test warning message.", logging.WARNING, module_name="ExternalComponent")
    awareness_module.log_event("This is a test error message.", logging.ERROR)

    print("\n--- Simulating Module Health Updates ---")
    awareness_module.update_module_health("CommandInterface", "OK", "Initialized successfully.")
    awareness_module.update_module_health("TextProcessor", "WARNING", "High latency detected.")

    print("\n--- Retrieving System Metrics ---")
    metrics = awareness_module.get_system_metrics()
    print(json.dumps(metrics, indent=2))

    print("\n--- Retrieving Bot Uptime ---")
    uptime = awareness_module.get_bot_uptime()
    print(f"Bot Uptime: {uptime}")

    print("\n--- Generating Health Report ---")
    health_report = awareness_module.report_health()
    print(json.dumps(health_report, indent=2))

    print(f"\nSelf-Awareness Module log file located at: {LOG_FILE_SA}")
    print("Test finished.")

