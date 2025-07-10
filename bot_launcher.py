#!/usr/bin/env python3
# bot_launcher.py - Production launcher for the Self-Aware Bot

import os
import sys
import logging
import json
from datetime import datetime

# Import all bot modules
from self_aware_module import SelfAwareModule
from self_healing_coding_module import SelfHealingModule, SelfCodingModule
from text_humanization_module import TextHumanizer
from ai_text_detection_module import AITextDetector
from command_interface import CommandInterface

# --- Configuration ---
CONFIG_FILE = "/home/ubuntu/bot_config.json"
MAIN_LOG_FILE = "/home/ubuntu/bot_main.log"

def setup_main_logger():
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(MAIN_LOG_FILE)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger("BotLauncher")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def create_default_config():
    """Create default configuration if it doesn't exist."""
    default_config = {
        "bot_name": "Self-Aware Assistant Bot",
        "version": "1.0.0",
        "modules": {
            "self_aware": {"enabled": True},
            "self_healing": {"enabled": True},
            "self_coding": {"enabled": True},
            "text_humanizer": {"enabled": True, "model": "Ateeqq/Text-Rewriter-Paraphraser"},
            "ai_detector": {"enabled": True, "model": "AICodexLab/answerdotai-ModernBERT-base-ai-detector"}
        },
        "interface": {
            "startup_message": True,
            "command_history": True,
            "auto_save_logs": True
        }
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    return default_config

def load_config():
    """Load bot configuration."""
    if not os.path.exists(CONFIG_FILE):
        return create_default_config()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        return create_default_config()

class BotManager:
    def __init__(self):
        self.logger = setup_main_logger()
        self.config = load_config()
        self.modules = {}
        self.command_interface = None
        
    def initialize_modules(self):
        """Initialize all bot modules based on configuration."""
        self.logger.info("Initializing bot modules...")
        
        try:
            # Initialize self-awareness module
            if self.config["modules"]["self_aware"]["enabled"]:
                self.modules["awareness"] = SelfAwareModule()
                self.logger.info("✓ Self-Awareness module initialized")
            
            # Initialize self-healing module
            if self.config["modules"]["self_healing"]["enabled"]:
                self.modules["healing"] = SelfHealingModule(
                    awareness_module=self.modules.get("awareness")
                )
                self.logger.info("✓ Self-Healing module initialized")
            
            # Initialize self-coding module
            if self.config["modules"]["self_coding"]["enabled"]:
                self.modules["coding"] = SelfCodingModule(
                    awareness_module=self.modules.get("awareness")
                )
                self.logger.info("✓ Self-Coding module initialized")
            
            # Initialize text humanizer (may take time to download model)
            if self.config["modules"]["text_humanizer"]["enabled"]:
                self.logger.info("Loading Text Humanizer (this may take a moment)...")
                self.modules["humanizer"] = TextHumanizer(
                    model_name=self.config["modules"]["text_humanizer"]["model"]
                )
                self.logger.info("✓ Text Humanizer module initialized")
            
            # Initialize AI detector (may take time to download model)
            if self.config["modules"]["ai_detector"]["enabled"]:
                self.logger.info("Loading AI Text Detector (this may take a moment)...")
                self.modules["ai_detector"] = AITextDetector(
                    model_name=self.config["modules"]["ai_detector"]["model"]
                )
                self.logger.info("✓ AI Text Detector module initialized")
            
            # Initialize command interface
            self.command_interface = CommandInterface(
                awareness_module=self.modules.get("awareness"),
                healing_module=self.modules.get("healing"),
                coding_module=self.modules.get("coding"),
                humanizer_module=self.modules.get("humanizer"),
                ai_detector_module=self.modules.get("ai_detector")
            )
            self.logger.info("✓ Command Interface initialized")
            
            self.logger.info("All modules initialized successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize modules: {e}", exc_info=True)
            return False
    
    def print_startup_banner(self):
        """Print startup banner with bot information."""
        if not self.config["interface"]["startup_message"]:
            return
            
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                    {self.config['bot_name']}                    ║
║                           v{self.config['version']}                            ║
╠══════════════════════════════════════════════════════════════╣
║  🧠 Self-Aware    🔧 Self-Healing    💻 Self-Coding         ║
║  📝 Text Humanizer    🤖 AI Detection                        ║
╠══════════════════════════════════════════════════════════════╣
║  Type 'help' for commands  |  'status' for system info      ║
║  'exit' or 'quit' to stop                                   ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
        # Show enabled modules
        enabled_modules = [name for name, config in self.config["modules"].items() if config["enabled"]]
        print(f"Enabled modules: {', '.join(enabled_modules)}")
        print(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log file: {MAIN_LOG_FILE}\n")
    
    def run_interactive_mode(self):
        """Run the bot in interactive command-line mode."""
        self.print_startup_banner()
        
        command_history = []
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input("🤖 > ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle exit commands
                    if user_input.lower() in ['exit', 'quit', 'bye']:
                        print("Shutting down bot... Goodbye! 👋")
                        self.logger.info("Bot shutdown requested by user")
                        break
                    
                    # Store command history
                    if self.config["interface"]["command_history"]:
                        command_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "command": user_input
                        })
                    
                    # Process command
                    self.logger.info(f"Processing user command: {user_input}")
                    response = self.command_interface.process_command(user_input)
                    
                    # Display response
                    print(f"\n{response}\n")
                    
                except KeyboardInterrupt:
                    print("\n\nBot interrupted. Type 'exit' to quit or continue with commands.")
                    continue
                except Exception as e:
                    print(f"Error processing command: {e}")
                    self.logger.error(f"Error in interactive mode: {e}", exc_info=True)
                    continue
        
        except Exception as e:
            self.logger.error(f"Critical error in interactive mode: {e}", exc_info=True)
            print(f"Critical error: {e}")
        
        # Save command history if enabled
        if self.config["interface"]["command_history"] and command_history:
            history_file = "/home/ubuntu/bot_command_history.json"
            try:
                with open(history_file, 'w') as f:
                    json.dump(command_history, f, indent=2)
                self.logger.info(f"Command history saved to {history_file}")
            except Exception as e:
                self.logger.error(f"Failed to save command history: {e}")
    
    def run_health_check(self):
        """Run a comprehensive health check and return status."""
        if not self.modules.get("awareness"):
            return {"status": "ERROR", "message": "Self-awareness module not available"}
        
        health_report = self.modules["awareness"].report_health()
        
        # Additional checks
        if self.command_interface:
            health_report["command_interface"] = "OK"
        
        return health_report

def main():
    """Main entry point for the bot."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--health-check":
            # Quick health check mode
            bot = BotManager()
            if bot.initialize_modules():
                health = bot.run_health_check()
                print(json.dumps(health, indent=2))
                sys.exit(0)
            else:
                print(json.dumps({"status": "ERROR", "message": "Failed to initialize"}))
                sys.exit(1)
        elif sys.argv[1] == "--version":
            config = load_config()
            print(f"{config['bot_name']} v{config['version']}")
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print("""
Self-Aware Assistant Bot

Usage:
    python3 bot_launcher.py                 - Run in interactive mode
    python3 bot_launcher.py --health-check  - Run health check and exit
    python3 bot_launcher.py --version       - Show version and exit
    python3 bot_launcher.py --help          - Show this help

Commands available in interactive mode:
    help                    - Show available commands
    status                  - Show bot status
    create_file <path>      - Create a new file
    read_file <path>        - Read file contents
    analyze_code <path>     - Analyze Python code structure
    humanize_text "<text>"  - Humanize/paraphrase text
    detect_ai_text "<text>" - Detect if text is AI-generated
    exit/quit               - Exit the bot
            """)
            sys.exit(0)
    
    # Default: run in interactive mode
    try:
        bot = BotManager()
        if bot.initialize_modules():
            bot.run_interactive_mode()
        else:
            print("❌ Failed to initialize bot modules. Check logs for details.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()