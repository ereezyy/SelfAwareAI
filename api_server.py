#!/usr/bin/env python3
"""
Simple Flask API server to bridge the web interface with the bot's Python modules.
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add the current directory to Python path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot modules
try:
    from self_aware_module import SelfAwareModule
    from self_healing_coding_module import SelfHealingModule, SelfCodingModule
    from text_humanization_module import TextHumanizer
    from ai_text_detection_module import AITextDetector
    from command_interface import CommandInterface
    
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import bot modules: {e}")
    MODULES_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for bot modules
bot_interface = None

def initialize_bot_modules():
    """Initialize all bot modules."""
    global bot_interface
    
    if not MODULES_AVAILABLE:
        logger.warning("Bot modules not available - using mock interface")
        return False
    
    try:
        logger.info("Initializing bot modules...")
        
        # Initialize modules
        awareness_module = SelfAwareModule()
        healing_module = SelfHealingModule(awareness_module=awareness_module)
        coding_module = SelfCodingModule(awareness_module=awareness_module)
        
        # Try to initialize text processing modules (they might fail due to model downloads)
        try:
            humanizer_module = TextHumanizer()
            logger.info("Text humanizer module initialized")
        except Exception as e:
            logger.warning(f"Could not initialize text humanizer: {e}")
            humanizer_module = None
        
        try:
            ai_detector_module = AITextDetector()
            logger.info("AI detector module initialized")
        except Exception as e:
            logger.warning(f"Could not initialize AI detector: {e}")
            ai_detector_module = None
        
        # Create command interface
        bot_interface = CommandInterface(
            awareness_module=awareness_module,
            healing_module=healing_module,
            coding_module=coding_module,
            humanizer_module=humanizer_module,
            ai_detector_module=ai_detector_module
        )
        
        logger.info("Bot modules initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize bot modules: {e}")
        return False

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('.', filename)

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Handle API commands from the web interface."""
    global bot_interface
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        command = data.get('command')
        args = data.get('args', [])
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        # If bot interface not initialized, try to initialize it
        if bot_interface is None:
            if not initialize_bot_modules():
                return jsonify({
                    'result': 'Error: Bot modules not available. Please check if all dependencies are installed.'
                })
        
        # Build command string
        command_str = command
        if args:
            # Properly escape arguments that might contain spaces
            escaped_args = []
            for arg in args:
                if ' ' in str(arg) or '"' in str(arg):
                    escaped_args.append(f'"{str(arg).replace('"', '\\"')}"')
                else:
                    escaped_args.append(str(arg))
            command_str += ' ' + ' '.join(escaped_args)
        
        logger.info(f"Processing command: {command_str}")
        
        # Process the command
        result = bot_interface.process_command(command_str)
        
        return jsonify({'result': result})
        
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        if bot_interface is None:
            return jsonify({'status': 'Bot modules not initialized'}), 503
        
        # Try to get status from bot
        result = bot_interface.process_command('status')
        return jsonify({'status': 'healthy', 'bot_status': result})
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def handle_file_upload():
    """Handle file uploads from the web interface."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save the file temporarily
        filename = file.filename
        filepath = os.path.join('/tmp', filename)
        file.save(filepath)
        
        logger.info(f"File uploaded: {filename}")
        return jsonify({'message': f'File {filename} uploaded successfully', 'filepath': filepath})
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize bot modules on startup
    if initialize_bot_modules():
        logger.info("Bot modules initialized successfully")
    else:
        logger.warning("Running with limited functionality - bot modules not available")
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)