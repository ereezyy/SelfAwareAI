#!/usr/bin/env python3.11
"""
Comprehensive Flask API server to bridge the web interface with the bot's Python modules.
This server provides RESTful endpoints for all bot functionalities.
"""

import os
import sys
import json
import logging
import tempfile
import uuid
from datetime import datetime
import asyncio
import subprocess
import signal
import psutil
import threading
import time
import websockets
import json as json_module
import traceback
from functools import wraps
import concurrent.futures
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/api_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot modules with error handling
BOT_MODULES_AVAILABLE = False
MANAGEMENT_SYSTEM_AVAILABLE = False

try:
    from self_aware_module import SelfAwareModule
    from self_healing_coding_module import SelfHealingModule, SelfCodingModule
    from text_humanization_module import TextHumanizer
    from ai_text_detection_module import AITextDetector
    from command_interface import CommandInterface
    BOT_MODULES_AVAILABLE = True
    logger.info("✅ Core bot modules imported successfully")
except ImportError as e:
    logger.error(f"⚠️ Failed to import core bot modules: {e}")
    BOT_MODULES_AVAILABLE = False

# Import bot management system with separate error handling
try:
    from bot_management_system import (
        DirectorBot, 
        BotCommand, 
        BotStatus, 
        BotType,
        SwarmTemplate,
        get_director_bot,
        get_director_bot, websocket_handler
    )
    MANAGEMENT_SYSTEM_AVAILABLE = True
    logger.info("✅ Bot management system imported successfully")
except ImportError as e:
    logger.error(f"⚠️ Failed to import bot management system: {e}")
    MANAGEMENT_SYSTEM_AVAILABLE = False
    # Create mock classes to prevent runtime errors
    class MockDirectorBot:
        def __init__(self):
            self.bot_id = "mock"
            self.created_at = time.time()
        async def execute_command(self, command):
            return {"status": "error", "message": "Bot management system not available"}
        async def start(self):
            pass
    
    class MockBotCommand:
        def __init__(self, command_id, command_type, **kwargs):
            self.command_id = command_id
            self.command_type = command_type
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    DirectorBot = MockDirectorBot
    BotCommand = MockBotCommand
    get_director_bot = lambda: MockDirectorBot()

# Flask app configuration
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global variables
bot_interface = None
backend_processes = {
    'websocket_server': None,
    'bot_management': None
# WebSocket integration
try:
    import asyncio
    import websockets
    import threading
    from websockets.server import serve
    WEBSOCKET_INTEGRATION = True
    logger.info("✅ WebSocket integration available")
except ImportError as e:
    logger.error(f"❌ WebSocket integration not available: {e}")
    WEBSOCKET_INTEGRATION = False

# Global WebSocket state
websocket_clients = set()
websocket_server = None
websocket_thread = None

}
uploaded_files = {}  # Track uploaded files by session
director_bot = None
websocket_server = None
websocket_clients = set()
websocket_server_running = False

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'.py', '.json', '.txt', '.md'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Enhanced validation and error handling decorators
def handle_api_errors(f):
    """Decorator for comprehensive API error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"ValueError in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': 'validation_error',
                'timestamp': datetime.now().isoformat()
            }), 400
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': 'Requested resource not found',
                'error_type': 'resource_not_found',
                'timestamp': datetime.now().isoformat()
            }), 404
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}\n{traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': 'Internal server error occurred',
                'error_type': 'server_error',
                'timestamp': datetime.now().isoformat()
            }), 500
    return decorated_function

def require_modules(*required_modules):
    """Decorator to check if required modules are available"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'bot_modules' in required_modules and not BOT_MODULES_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Bot modules not available',
                    'error_type': 'service_unavailable',
                    'timestamp': datetime.now().isoformat()
                }), 503
            
            if 'management_system' in required_modules and not MANAGEMENT_SYSTEM_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Bot management system not available',
                    'error_type': 'service_unavailable',
                    'timestamp': datetime.now().isoformat()
                }), 503
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def allowed_file(filename):
    """Check if file extension is allowed."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def generate_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def validate_json_request():
    """Validate that request contains valid JSON."""
    if not request.is_json:
        return {
            'error': 'Content-Type must be application/json',
            'error_type': 'invalid_content_type'
        }, 400
    
    try:
        data = request.get_json()
    except Exception as e:
        return {'error': f'Invalid JSON format: {str(e)}'}, 400
    
    if data is None:
        return {
            'error': 'Invalid JSON in request body',
            'error_type': 'invalid_json'
        }, 400
    
    return data, None

def validate_required_fields(data, required_fields, field_types=None):
    """Validate that all required fields are present and not empty."""
    if field_types is None:
        field_types = {}
    
    if not isinstance(data, dict):
        return "Request data must be a JSON object"
    
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
        
        value = data[field]
        if value is None:
            return f"Field '{field}' cannot be null"
        if isinstance(value, str) and not value.strip():
            return f"Field '{field}' cannot be empty"
        if isinstance(value, (list, dict)) and len(value) == 0:
            return f"Field '{field}' cannot be empty"
        
        # Type validation if specified
        if field in field_types:
            expected_type = field_types[field]
            if not isinstance(value, expected_type):
                return f"Field '{field}' must be of type {expected_type.__name__}, got {type(value).__name__}"
        
        # Additional validation for common fields
        if field == 'bot_type' and value not in ['analyzer', 'generator', 'monitor', 'custom']:
            return f"Invalid bot_type '{value}'. Must be one of: analyzer, generator, monitor, custom"
    
    return None

async def safe_broadcast_to_websockets(message):
    """Broadcast message to all connected WebSocket clients."""
    global websocket_clients
    
    if not websocket_clients:
        logger.debug("No WebSocket clients to broadcast to")
        return
    
    try:
        message_str = json_module.dumps(message) if isinstance(message, dict) else str(message)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize WebSocket message: {e}")
        return
    
    disconnected_clients = set()
    successful_broadcasts = 0
    
    for client in websocket_clients.copy():
        try:
            await client.send(message_str)
            successful_broadcasts += 1
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)
            logger.debug("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")
            disconnected_clients.add(client)
    
    # Remove disconnected clients
    websocket_clients -= disconnected_clients
    
    if disconnected_clients:
        logger.info(f"Removed {len(disconnected_clients)} disconnected WebSocket clients")
    
    logger.debug(f"Broadcast successful to {successful_broadcasts} clients")

def broadcast_to_websockets(message):
    """Synchronous wrapper for WebSocket broadcasting"""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the coroutine
            asyncio.create_task(safe_broadcast_to_websockets(message))
        else:
            # If no loop is running, run it directly
            loop.run_until_complete(safe_broadcast_to_websockets(message))
    except RuntimeError:
        # If no event loop exists, create a new one
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(safe_broadcast_to_websockets(message))
            new_loop.close()
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket message: {e}")
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")

async def websocket_handler(websocket, path):
    """Handle WebSocket connections for real-time updates."""
    global websocket_clients
    
    websocket_clients.add(websocket)
    logger.info(f"New WebSocket client connected. Total: {len(websocket_clients)}")
    
    try:
        # Send initial status
        initial_status = {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'client_count': len(websocket_clients),
            'bot_modules_available': BOT_MODULES_AVAILABLE,
            'management_system_available': MANAGEMENT_SYSTEM_AVAILABLE,
            'services': {
                'bot_interface': bot_interface is not None,
                'director_bot': director_bot is not None,
                'websocket_server': websocket_server_running
            }
        }
        await websocket.send(json_module.dumps(initial_status))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json_module.loads(message)
                
                # Enhanced message handling
                message_type = data.get('type', 'unknown')
                logger.info(f"WebSocket message received: {message_type}")
                
                # Handle different message types
                if message_type == 'ping':
                    await websocket.send(json_module.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }))
                elif message_type == 'get_status':
                    status_response = {
                        'type': 'status_response',
                        'data': {
                            'bot_modules_available': BOT_MODULES_AVAILABLE,
                            'management_system_available': MANAGEMENT_SYSTEM_AVAILABLE,
                            'connected_clients': len(websocket_clients),
                            'server_uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                    await websocket.send(json_module.dumps(status_response))
                else:
                    # Unknown message type
                    await websocket.send(json_module.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}',
                        'timestamp': datetime.now().isoformat()
                    }))
                    
            except json_module.JSONDecodeError as e:
                error_msg = {'type': 'error', 'message': f'Invalid JSON: {str(e)}'}
                await websocket.send(json_module.dumps(error_msg))
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                error_msg = {'type': 'error', 'message': str(e)}
                await websocket.send(json_module.dumps(error_msg))
                
    except websockets.exceptions.ConnectionClosed:
        logger.debug("WebSocket connection closed normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(websocket_clients)}")

def start_websocket_server():
    """Start WebSocket server in a separate thread."""
    global websocket_server, websocket_server_running
    
    async def run_server():
        global websocket_server, websocket_server_running
        try:
            websocket_server = await websockets.serve(
                websocket_handler,
                "localhost",
                8765,
                ping_interval=20,
                ping_timeout=10,
                max_size=1000000,  # 1MB max message size
                max_queue=32,      # Max pending messages
                compression=None   # Disable compression for better performance
            )
            websocket_server_running = True
            logger.info("🌐 WebSocket server started on ws://localhost:8765")
            
            # Broadcast server start event
            await safe_broadcast_to_websockets({
                'type': 'server_started',
                'message': 'WebSocket server is now running',
                'timestamp': datetime.now().isoformat()
            })
            
            await websocket_server.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
            websocket_server_running = False
        finally:
            websocket_server_running = False
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_server())
        except Exception as e:
            logger.error(f"WebSocket thread error: {e}")
            global websocket_server_running
            websocket_server_running = False
        finally:
            loop.close()
    
    websocket_thread = threading.Thread(target=run_in_thread, daemon=True, name="WebSocketServer")
    websocket_thread.start()
    logger.info("🚀 WebSocket server thread started")
    
    # Wait a moment for server to initialize
    time.sleep(1)
    
    return websocket_thread

async def initialize_director_bot():
    """Initialize Director Bot in async context."""
    global director_bot
    try:
        if MANAGEMENT_SYSTEM_AVAILABLE:
            director_bot = get_director_bot()
            await director_bot.start()
            logger.info("✅ Director Bot initialized and started")
            
            # Broadcast initialization success
            await safe_broadcast_to_websockets({
                'type': 'system_status',
                'message': 'Director Bot initialized successfully',
                'timestamp': datetime.now().isoformat()
            })
            return True
        else:
            logger.warning("⚠️ Bot management system not available - Director Bot not initialized")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize Director Bot: {e}\n{traceback.format_exc()}")
        director_bot = None
        
        # Broadcast initialization failure
        try:
            await safe_broadcast_to_websockets({
                'type': 'system_error',
                'message': f'Director Bot initialization failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as broadcast_error:
            logger.error(f"Failed to broadcast Director Bot initialization error: {broadcast_error}")
    
    return False

def start_director_bot():
    """Start Director Bot in a separate thread."""
    if not MANAGEMENT_SYSTEM_AVAILABLE:
        logger.warning("Cannot start Director Bot - management system not available")
        return
    
    def run_director():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(initialize_director_bot())
            if success:
                logger.info("✅ Director Bot thread running successfully")
                # Keep the loop running for Director Bot operations
                loop.run_forever()
            else:
                logger.error("❌ Director Bot initialization failed")
        except Exception as e:
            logger.error(f"Director Bot thread error: {e}\n{traceback.format_exc()}")
        finally:
            loop.close()
    
    director_thread = threading.Thread(target=run_director, daemon=True, name="DirectorBot")
    director_thread.start()
    logger.info("🤖 Director Bot thread started")
    
    return director_thread

def initialize_bot_modules():
    """Initialize all bot modules with comprehensive error handling."""
    global bot_interface, director_bot
    
    initialization_status = {
        'bot_interface': False,
        'director_bot': False,
        'websocket_server': False,
        'errors': []
    }
    
    if not BOT_MODULES_AVAILABLE:
        logger.warning("Bot modules not available - API will return error responses")
        initialization_status['errors'].append("Core bot modules not available")
        return initialization_status
    
    try:
        logger.info("🚀 Initializing bot modules...")
        
        # Initialize core modules
        try:
            awareness_module = SelfAwareModule()
            logger.info("✅ Self-Awareness module initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Self-Awareness module: {e}")
            initialization_status['errors'].append(f"Self-Awareness: {str(e)}")
            awareness_module = None
        
        try:
            healing_module = SelfHealingModule(awareness_module=awareness_module)
            logger.info("✅ Self-Healing module initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Self-Healing module: {e}")
            initialization_status['errors'].append(f"Self-Healing: {str(e)}")
            healing_module = None
        
        try:
            coding_module = SelfCodingModule(awareness_module=awareness_module)
            logger.info("✅ Self-Coding module initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Self-Coding module: {e}")
            initialization_status['errors'].append(f"Self-Coding: {str(e)}")
            coding_module = None
        
        # Initialize text processing modules (may fail due to model requirements)
        humanizer_module = None
        ai_detector_module = None
        
        try:
            logger.info("📝 Loading text humanizer (this may take time for model download)...")
            humanizer_module = TextHumanizer()
            logger.info("✅ Text humanizer module initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize text humanizer: {e}")
            initialization_status['errors'].append(f"Text Humanizer: {str(e)}")
        
        try:
            logger.info("🤖 Loading AI detector (this may take time for model download)...")
            ai_detector_module = AITextDetector()
            logger.info("✅ AI detector module initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize AI detector: {e}")
            initialization_status['errors'].append(f"AI Detector: {str(e)}")
        
        # Create command interface
        try:
            bot_interface = CommandInterface(
                awareness_module=awareness_module,
                healing_module=healing_module,
                coding_module=coding_module,
                humanizer_module=humanizer_module,
                ai_detector_module=ai_detector_module
            )
            initialization_status['bot_interface'] = True
            logger.info("✅ Command interface initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Command Interface: {e}")
            initialization_status['errors'].append(f"Command Interface: {str(e)}")
        
        # Start Director Bot and WebSocket server
        try:
            start_director_bot()
            initialization_status['director_bot'] = True
        except Exception as e:
            logger.error(f"Failed to start Director Bot: {e}")
            initialization_status['errors'].append(f"Director Bot: {str(e)}")
        
        try:
            start_websocket_server()
            initialization_status['websocket_server'] = True
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            initialization_status['errors'].append(f"WebSocket Server: {str(e)}")
        
        success_count = sum([initialization_status['bot_interface'], initialization_status['director_bot'], initialization_status['websocket_server']])
        logger.info(f"🎉 Bot modules initialization completed! ({success_count}/3 services started)")
        
        return initialization_status
        
    except Exception as e:

# Static file serving
@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    try:
        return send_from_directory('.', filename)
    except FileNotFoundError:
        return jsonify({'error': f'File {filename} not found'}), 404

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'api_status': 'healthy',
            'modules_available': BOT_MODULES_AVAILABLE,
            'bot_initialized': bot_interface is not None,
            'director_bot_available': director_bot is not None,
            'websocket_server_running': websocket_server is not None,
            'websocket_clients': len(websocket_clients)
        }
        
        if bot_interface:
            try:
                bot_status = bot_interface.process_command('status')
                health_status['bot_status'] = 'healthy'
                health_status['bot_details'] = bot_status[:500] + '...' if len(bot_status) > 500 else bot_status
            except Exception as e:
                health_status['bot_status'] = 'error'
                health_status['bot_error'] = str(e)
        else:
            health_status['bot_status'] = 'not_initialized'
        
        # Check Director Bot status
        if director_bot:
            try:
                health_status['director_status'] = 'healthy'
                health_status['director_uptime'] = time.time() - director_bot.created_at if hasattr(director_bot, 'created_at') else 0
            except Exception as e:
                health_status['director_status'] = 'error'
                health_status['director_error'] = str(e)
        else:
            health_status['director_status'] = 'not_initialized'
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'api_status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/initialize', methods=['POST'])
def initialize_modules():
    """Force re-initialization of bot modules."""
    try:
        success = initialize_bot_modules()
        return jsonify({
            'success': success,
            'message': 'Bot modules initialized successfully' if success else 'Failed to initialize bot modules',
            'modules_available': BOT_MODULES_AVAILABLE,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@handle_api_errors
def upload_file():
    """Handle file uploads with proper validation and storage."""
        if 'file' not in request.files:
            raise ValueError('No file provided in request')
        
        file = request.files['file']
        if file.filename == '':
            raise ValueError('No file selected')
        
        if not file.filename or not file.filename.strip():
            raise ValueError('Invalid filename')
        
        if not allowed_file(file.filename):
            raise ValueError(f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}')
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)     # Reset to beginning
        
        if file_size > MAX_CONTENT_LENGTH:
            raise ValueError(f'File too large. Maximum size: {MAX_CONTENT_LENGTH // (1024*1024)}MB')
        
        # Generate secure filename and session ID
        filename = secure_filename(file.filename)
        if not filename:
            raise ValueError('Invalid filename after sanitization')
            
        session_id = generate_session_id()
        filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        file.save(filepath)
        
        # Store file info in session
        file_info = {
            'original_name': filename,
            'filepath': filepath,
            'upload_time': datetime.now().isoformat(),
            'size': file_size
        }
        uploaded_files[session_id] = file_info
        
        logger.info(f"File uploaded: {filename} -> {filepath}")
        
        # Broadcast file upload event
        broadcast_to_websockets({
            'type': 'file_uploaded',
            'filename': filename,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'size': file_size
        })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'message': f'File {filename} uploaded successfully',
            'file_info': file_info
        })

@app.route('/api/command', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def handle_generic_command():
    """Handle generic bot commands."""
    return _process_command_request()

@app.route('/api/analyze/structure', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def analyze_code_structure():
    """Analyze code structure of uploaded file."""
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, ['session_id'], {'session_id': str})
        if validation_error:
            raise ValueError(validation_error)
        
        session_id = data.get('session_id')
        
        if session_id not in uploaded_files:
            raise ValueError('Invalid session ID or file not found')
        
        filepath = uploaded_files[session_id]['filepath']
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'Uploaded file no longer exists: {filepath}')
            
        return _execute_bot_command('analyze_code', [filepath])

@app.route('/api/analyze/quality', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def analyze_code_quality():
    """Analyze code quality of uploaded file."""
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, ['session_id'], {'session_id': str})
        if validation_error:
            raise ValueError(validation_error)
        
        session_id = data.get('session_id')
        
        if session_id not in uploaded_files:
            raise ValueError('Invalid session ID or file not found')
        
        filepath = uploaded_files[session_id]['filepath']
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'Uploaded file no longer exists: {filepath}')
            
        return _execute_bot_command('analyze_quality', [filepath])

@app.route('/api/generate/code', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def generate_code():
    """Generate code using templates."""
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, ['code_type', 'name'], {
            'code_type': str,
            'name': str
        })
        if validation_error:
            raise ValueError(validation_error)
        
        code_type = data.get('code_type')
        name = data.get('name')
        params = data.get('params', {})
        
        # Validate code_type
        valid_code_types = ['class_basic', 'singleton', 'context_manager', 'api_client', 'unit_test']
        if code_type not in valid_code_types:
            raise ValueError(f'Invalid code_type. Must be one of: {", ".join(valid_code_types)}')
        
        # Build arguments
        args = [code_type, name]
        for key, value in params.items():
            args.extend([key, value])
        
        return _execute_bot_command('generate_code', args)

@app.route('/api/generate/tests', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def generate_tests():
    """Generate unit tests for uploaded file."""
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, ['session_id'], {'session_id': str})
        if validation_error:
            raise ValueError(validation_error)
        
        session_id = data.get('session_id')
        
        if session_id not in uploaded_files:
            raise ValueError('Invalid session ID or file not found')
        
        filepath = uploaded_files[session_id]['filepath']
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'Uploaded file no longer exists: {filepath}')
            
        return _execute_bot_command('generate_tests', [filepath])

@app.route('/api/refactor', methods=['POST'])
def refactor_code():
    """Refactor code using various techniques."""
    try:
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        validation_error = validate_required_fields(data, ['session_id', 'refactor_type'])
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        session_id = data.get('session_id')
        refactor_type = data.get('refactor_type')
        params = data.get('params', {})
        
        if session_id not in uploaded_files:
            return jsonify({'error': 'Invalid session ID or file not found'}), 400
        
        filepath = uploaded_files[session_id]['filepath']
        
        # Build arguments
        args = [filepath, refactor_type]
        for key, value in params.items():
            args.extend([key, value])
        
        return _execute_bot_command('refactor_code', args)
        
    except Exception as e:
        logger.error(f"Refactoring failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/autofix', methods=['POST'])
def auto_fix_issues():
    """Automatically fix common code issues."""
    try:
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        validation_error = validate_required_fields(data, ['session_id'])
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        session_id = data.get('session_id')
        
        if session_id not in uploaded_files:
            return jsonify({'error': 'Invalid session ID or file not found'}), 400
        
        filepath = uploaded_files[session_id]['filepath']
        return _execute_bot_command('auto_fix', [filepath])
        
    except Exception as e:
        logger.error(f"Auto-fix failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/text/humanize', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def humanize_text():
    """Humanize text using AI."""
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, ['text'], {'text': str})
        if validation_error:
            raise ValueError(validation_error)
        
        text = data.get('text')
        
        # Additional text validation
        if len(text.strip()) < 10:
            raise ValueError('Text must be at least 10 characters long')
        if len(text) > 5000:
            raise ValueError('Text must be less than 5000 characters')
        
        return _execute_bot_command('humanize_text', [text])

@app.route('/api/text/detect', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def detect_ai_text():
    """Detect if text is AI-generated."""
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, ['text'], {'text': str})
        if validation_error:
            raise ValueError(validation_error)
        
        text = data.get('text')
        
        # Additional text validation
        if len(text.strip()) < 5:
            raise ValueError('Text must be at least 5 characters long')
        if len(text) > 10000:
            raise ValueError('Text must be less than 10000 characters')
        
        return _execute_bot_command('detect_ai_text', [text])

@app.route('/api/status', methods=['GET'])
@require_modules('bot_modules')
@handle_api_errors
def get_system_status():
    """Get comprehensive system status."""
    return _execute_bot_command('status', [])

@app.route('/api/autonomy/enable', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def enable_autonomy():
    """Enable autonomous self-healing."""
    return _execute_bot_command('enable_autonomy', [])

@app.route('/api/autonomy/disable', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def disable_autonomy():
    """Disable autonomous self-healing."""
    return _execute_bot_command('disable_autonomy', [])

@app.route('/api/autonomy/status', methods=['GET'])
@require_modules('bot_modules')
@handle_api_errors
def get_autonomy_status():
    """Get autonomy and health status."""
    return _execute_bot_command('autonomy_status', [])

@app.route('/api/system/health-check', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def force_health_check():
    """Force immediate health check."""
    return _execute_bot_command('force_health_check', [])

@app.route('/api/system/optimize', methods=['POST'])
@require_modules('bot_modules')
@handle_api_errors
def optimize_system():
    """Trigger system optimization."""
    return _execute_bot_command('system_optimize', [])

@app.route('/api/system/recovery-history', methods=['GET'])
@require_modules('bot_modules')
@handle_api_errors
def get_recovery_history():
    """Get recovery action history."""
    return _execute_bot_command('recovery_history', [])

@app.route('/api/files', methods=['GET'])
def list_uploaded_files():
    """List all uploaded files in current session."""
    try:
        files_info = {}
        for session_id, file_info in uploaded_files.items():
            files_info[session_id] = {
                'filename': file_info['original_name'],
                'upload_time': file_info['upload_time'],
                'size': file_info['size']
            }
        
        return jsonify({
            'success': True,
            'files': files_info,
            'total_files': len(files_info)
        })
        
    except Exception as e:
        logger.error(f"File listing failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<session_id>', methods=['DELETE'])
def delete_uploaded_file(session_id):
    """Delete an uploaded file."""
    try:
        if session_id not in uploaded_files:
            return jsonify({'error': 'File not found'}), 404
        
        filepath = uploaded_files[session_id]['filepath']
        
        # Remove file from filesystem
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remove from tracking
        filename = uploaded_files[session_id]['original_name']
        del uploaded_files[session_id]
        
        logger.info(f"File deleted: {filename}")
        return jsonify({
            'success': True,
            'message': f'File {filename} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        return jsonify({'error': str(e)}), 500

# Bot Management API Routes

@app.route('/api/websocket-info', methods=['GET'])
@handle_api_errors
def websocket_info():
    """Get WebSocket server information."""
    return jsonify({
        'websocket_url': 'ws://localhost:8765',
        'connected_clients': len(websocket_clients),
        'server_running': websocket_server_running,
        'bot_modules_available': BOT_MODULES_AVAILABLE,
        'management_system_available': MANAGEMENT_SYSTEM_AVAILABLE,
        'director_bot_available': director_bot is not None,
        'services': {
            'websocket_port': 8765,
            'api_port': int(os.environ.get('PORT', 3000)),
            'max_clients': 100,  # You can make this configurable
            'ping_interval': 20
        }
    })

@app.route('/api/bots', methods=['GET'])
@require_modules('management_system')
@handle_api_errors
def list_all_bots():
    """List all bots managed by Director Bot"""
        if not director_bot:
            raise ValueError('Director Bot not initialized')
        
        # Create command to list bots
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='list_bots'
        )
        
        # Use a more robust async execution
        result = execute_director_command_sync(command)
        
        if result:
            # Broadcast bot list update
            broadcast_to_websockets({
                'type': 'bot_list_updated',
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            raise ValueError('Failed to execute list bots command')

@app.route('/api/bots', methods=['POST'])
@require_modules('management_system')
@handle_api_errors
def create_bot():
    """Create a new bot"""
        if not director_bot:
            raise ValueError('Director Bot not initialized')
        
        data, error = validate_json_request()
        if error:
            raise ValueError(error[0]['error'])
        
        validation_error = validate_required_fields(data, [], {
            'bot_type': str,
            'name': str
        } if 'bot_type' in data or 'name' in data else {})
        if validation_error:
            raise ValueError(validation_error)
        
        bot_type = data.get('bot_type', 'custom')
        bot_name = data.get('name', f'{bot_type}_bot')
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='create_bot',
            parameters={
                'bot_type': bot_type,
                'name': bot_name
            }
        )
        
        result = execute_director_command_sync(command)
        if result:
            # Broadcast bot creation event
            broadcast_to_websockets({
                'type': 'bot_created',
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'data': result
            })

@app.route('/api/bots/<bot_id>/start', methods=['POST'])
def start_bot(bot_id):
    """Start a specific bot"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='start_bot',
            parameters={'bot_id': bot_id}
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Start bot failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots/<bot_id>/stop', methods=['POST'])
def stop_bot(bot_id):
    """Stop a specific bot"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='stop_bot',
            parameters={'bot_id': bot_id}
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Stop bot failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/swarms', methods=['GET'])
def list_swarms():
    """List all swarms"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='list_swarms'
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"List swarms failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/swarms', methods=['POST'])
def create_swarm():
    """Create a new swarm"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        data = request.get_json()
        swarm_name = data.get('name', 'New Swarm')
        template = data.get('template')
        config = data.get('config', {})
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='create_swarm',
            parameters={
                'name': swarm_name,
                'template': template,
                'config': config
            }
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Create swarm failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/swarms/<swarm_id>/start', methods=['POST'])
def start_swarm(swarm_id):
    """Start all bots in a swarm"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='start_swarm',
            parameters={'swarm_id': swarm_id}
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Start swarm failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/swarms/<swarm_id>/stop', methods=['POST'])
def stop_swarm(swarm_id):
    """Stop all bots in a swarm"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='stop_swarm',
            parameters={'swarm_id': swarm_id}
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Stop swarm failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot-status', methods=['GET'])
def get_bot_management_status():
    """Get comprehensive bot management status"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='get_status'
        )
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(director_bot.execute_command(command))
            return jsonify({
                'success': True,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Get bot status failed: {e}")
        return jsonify({'error': str(e)}), 500
        else:
            raise ValueError('Failed to create bot')

# Helper functions

def execute_director_command_sync(command, timeout=30):
    """Execute a Director Bot command synchronously."""
    if not director_bot or not MANAGEMENT_SYSTEM_AVAILABLE:
        logger.error("Director Bot or management system not available")
        return None
    
    try:
        # Use concurrent.futures for better async/sync bridging
        def run_command():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(director_bot.execute_command(command))
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_command)
            return future.result(timeout=timeout)
        
    except Exception as e:
        logger.error(f"Director command execution failed: {e}\n{traceback.format_exc()}")
        return None

def _process_command_request():
    """Process generic command requests."""
    try:
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        command = data.get('command')
        args = data.get('args', [])
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        if not isinstance(args, list):
            return jsonify({'error': 'Args must be a list'}), 400
        
        return _execute_bot_command(command, args)
        
    except Exception as e:
        logger.error(f"Command processing failed: {e}")
        return jsonify({'error': str(e)}), 500

def _execute_bot_command(command, args):
    """Execute a bot command with proper error handling."""
    global bot_interface
    
        # Initialize bot if not already done
        if bot_interface is None:
            status = initialize_bot_modules()
            if not status['bot_interface']:
                raise ValueError('Bot modules not available or failed to initialize')
        
        # Validate command and args
        if not isinstance(command, str) or not command.strip():
            raise ValueError('Command must be a non-empty string')
        
        if not isinstance(args, list):
            raise ValueError('Args must be a list')
        
        # Build command string with better escaping
        command_str = command
        if args:
            escaped_args = []
            for arg in args:
                arg_str = str(arg)
                # Better argument escaping
                if ' ' in arg_str or '"' in arg_str or "'" in arg_str or '\n' in arg_str:
                    # Use double quotes and escape internal quotes
                    escaped_arg = '"' + arg_str.replace('"', '\\"') + '"'
                    escaped_args.append(escaped_arg)
                else:
                    escaped_args.append(arg_str)
            command_str += ' ' + ' '.join(escaped_args)
        
        logger.info(f"Executing command: {command_str}")
        
        # Execute command with timeout protection
        start_time = time.time()
        result = bot_interface.process_command(command_str)
        execution_time = time.time() - start_time
        
        # Check for command errors
        if isinstance(result, str) and result.startswith('Error:'):
            raise ValueError(result)
        
        # Broadcast command execution event
        try:
            broadcast_to_websockets({
                'type': 'command_executed',
                'command': command_str,
                'result': result[:200] + '...' if len(str(result)) > 200 else result,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as broadcast_error:
            logger.warning(f"Failed to broadcast command execution: {broadcast_error}")
        
        return jsonify({
            'success': True,
            'result': result,
            'command': command_str,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        })

# Enhanced error handlers with detailed logging
@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors."""
    logger.warning(f"Bad request: {e}")
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(e.description) if hasattr(e, 'description') else str(e),
        'error_type': 'bad_request',
        'timestamp': datetime.now().isoformat()
    }), 400

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    logger.warning(f"Not found: {request.url}")
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'requested_url': request.url,
        'error_type': 'not_found',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors."""
    logger.warning(f"File too large: {e}")
    return jsonify({
        'success': False,
        'error': 'File too large',
        'message': f'Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB',
        'error_type': 'file_too_large',
        'timestamp': datetime.now().isoformat()
    }), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {e}\n{traceback.format_exc()}")
    return jsonify({
        'success': False,
        'error': 'Internal server error occurred',
        'error_type': 'server_error',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(503)
def service_unavailable(e):
    """Handle service unavailable errors."""
    logger.warning(f"Service unavailable: {e}")
    return jsonify({
        'success': False,
        'error': 'Service temporarily unavailable',
        'message': str(e.description) if hasattr(e, 'description') else str(e),
        'error_type': 'service_unavailable',
        'timestamp': datetime.now().isoformat()
    }), 503
                    'success': False,
                    'result': 'Error: Bot modules not available. Please check if all dependencies are installed.'
                })
        
        # Validate command and args
        if not isinstance(command, str) or not command.strip():
            return jsonify({
                'success': False,
                'error': 'Command must be a non-empty string'
            }), 400
        
        if not isinstance(args, list):
            return jsonify({
                'success': False,
                'error': 'Args must be a list'
            }), 400
        
        # Build command string
        command_str = command
        if args:
            # Properly escape arguments
            escaped_args = []
            for arg in args:
                arg_str = str(arg)
                if ' ' in arg_str or '"' in arg_str or "'" in arg_str:
                    escaped_args.append(f"\"{arg_str.replace('\"', '\\\"')}\"")
                else:
                    escaped_args.append(arg_str)
            command_str += ' ' + ' '.join(escaped_args)
        
        logger.info(f"Executing command: {command_str}")
        
        # Execute command
        result = bot_interface.process_command(command_str)
        
        # Broadcast command execution event
        try:
            asyncio.create_task(broadcast_to_websockets({
                'type': 'command_executed',
                'command': command_str,
                'result': result[:200] + '...' if len(str(result)) > 200 else result,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as broadcast_error:
            logger.warning(f"Failed to broadcast command execution: {broadcast_error}")
        
        return jsonify({
            'success': True,
            'result': result,
            'command': command_str,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'command': command,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/backend/status', methods=['GET'])
@handle_api_errors
def get_backend_status():
    """Get backend service status"""
    status = {
        'api_server': 'running',
        'websocket_server': 'stopped',
        'bot_management': 'stopped',
        'processes': {}
    }
    
    # Check WebSocket server
    if backend_processes['websocket_server']:
        try:
            proc = psutil.Process(backend_processes['websocket_server'].pid)
            if proc.is_running():
                status['websocket_server'] = 'running'
                status['processes']['websocket_server'] = {
                    'pid': proc.pid,
                    'cpu_percent': proc.cpu_percent(),
                    'memory_percent': proc.memory_percent()
                }
            else:
                status['websocket_server'] = 'stopped'
                backend_processes['websocket_server'] = None
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            status['websocket_server'] = 'stopped'
            backend_processes['websocket_server'] = None
    
    # Check if director bot is available
    global director_bot, MANAGEMENT_SYSTEM_AVAILABLE
    if director_bot and MANAGEMENT_SYSTEM_AVAILABLE:
        status['bot_management'] = 'running'
    
    return jsonify({
        'success': True,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/backend/start/<service>', methods=['POST'])
@handle_api_errors
def start_backend_service(service):
    """Start a backend service"""
    global director_bot, MANAGEMENT_SYSTEM_AVAILABLE
    
    if service == 'websocket':
        if backend_processes['websocket_server']:
            try:
                proc = psutil.Process(backend_processes['websocket_server'].pid)
                if proc.is_running():
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket server is already running',
                        'pid': proc.pid
                    }), 400
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                backend_processes['websocket_server'] = None
        
        try:
            # Start WebSocket server
            proc = subprocess.Popen([
                sys.executable, 'websocket_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            backend_processes['websocket_server'] = proc
            logger.info(f"Started WebSocket server with PID: {proc.pid}")
            
            return jsonify({
                'success': True,
                'message': 'WebSocket server started successfully',
                'pid': proc.pid,
                'service': 'websocket_server'
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to start WebSocket server: {str(e)}'
            }), 500
    
    elif service == 'bot_management':
        if not MANAGEMENT_SYSTEM_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Bot management system is not available'
            }), 400
        
        if director_bot and director_bot.is_running:
            return jsonify({
                'success': False,
                'error': 'Bot management system is already running'
            }), 400
        
        try:
            # Start Bot Management System
            result = subprocess.Popen([
                sys.executable, 'bot_management_system.py'
            ])
            return jsonify({
                'status': 'success',
                'message': f'Bot Management System started with PID {result.pid}'
            })
            
        except Exception as e:
            logger.error(f"Failed to start bot management system: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to start bot management system: {str(e)}'
            }), 500
    
    else:
        return jsonify({
            'success': False,
            'error': f'Unknown service: {service}'
        }), 400

@app.route('/api/backend/stop/<service>', methods=['POST'])
@handle_api_errors
def stop_backend_service(service):
    """Stop a backend service"""
    global director_bot
    
    if service == 'websocket':
        if not backend_processes['websocket_server']:
            return jsonify({
                'success': False,
                'error': 'WebSocket server is not running'
            }), 400
        
        try:
            proc = backend_processes['websocket_server']
            
            # Try graceful shutdown first
            proc.terminate()
            
            try:
                proc.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                proc.kill()
                proc.wait()
            
            backend_processes['websocket_server'] = None
            logger.info("Stopped WebSocket server")
            
            return jsonify({
                'success': True,
                'message': 'WebSocket server stopped successfully',
                'service': 'websocket_server'
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to stop WebSocket server: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to stop WebSocket server: {str(e)}'
            }), 500
    
    elif service == 'bot_management':
        # Stop Bot Management System processes
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'bot_management_system.py' in ' '.join(cmdline):
                    proc.terminate()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify({
            'status': 'success',
            'message': f'Stopped {killed_count} Bot Management System process(es)'
        })
    
    else:
        return jsonify({
            'success': False,
            'error': f'Unknown service: {service}'
        }), 400

@app.route('/api/backend/restart/<service>', methods=['POST'])
@handle_api_errors
def restart_backend_service(service):
    """Restart a backend service"""
    try:
        # Stop the service first
        stop_response = stop_backend_service(service)
        if stop_response[1] not in [200, 400]:  # 400 is OK if service wasn't running
            return stop_response
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Start the service
        start_response = start_backend_service(service)
        
        if start_response[1] == 200:
            return jsonify({
                'success': True,
                'message': f'{service} restarted successfully',
                'service': service
            }), 200
        else:
            return start_response
            
    except Exception as e:
        logger.error(f"Failed to restart {service}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to restart {service}: {str(e)}'
        }), 500

# Error handlers

@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors."""
    return jsonify({'error': 'Bad request', 'message': str(e)}), 400

@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors."""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

# Cleanup on shutdown
import atexit

def cleanup_uploaded_files():
    """Clean up uploaded files on server shutdown."""
    logger.info("Cleaning up uploaded files...")
    for session_id, file_info in uploaded_files.items():
        filepath = file_info['filepath']
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up: {file_info['original_name']}")
        except Exception as e:
            logger.error(f"Failed to clean up {filepath}: {e}")

atexit.register(cleanup_uploaded_files)

if __name__ == '__main__':
    # Record app start time for uptime calculations
    app.start_time = time.time()
    
    print("🚀 Starting AI Bot API Server...")
    print("=" * 50)
    
    # Initialize bot modules on startup
    initialization_status = initialize_bot_modules()
    
    success_count = sum([
        initialization_status['bot_interface'],
        initialization_status['director_bot'],
        initialization_status['websocket_server']
    ])
    
    if success_count > 0:
        print(f"✅ Bot modules initialized successfully ({success_count}/3 services)")
        if initialization_status['errors']:
            print("⚠️ Some services failed to initialize:")
            for error in initialization_status['errors']:
                print(f"   - {error}")
    else:
        print("⚠️  Running with limited functionality - some bot modules not available")
        if initialization_status['errors']:
            print("Errors encountered:")
            for error in initialization_status['errors']:
                print(f"   - {error}")
    
    print("=" * 50)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 3000))
    print(f"🌐 API server starting on http://localhost:{port}")
    print(f"🔗 WebSocket server on ws://localhost:8765")
    print(f"📊 Health check: http://localhost:{port}/api/health")
    print(f"🎯 API endpoints available at /api/*")
    print(f"📁 File uploads: Max {MAX_CONTENT_LENGTH // (1024*1024)}MB")
    print(f"🔧 Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}")
    print("=" * 50)
    
    try:
        services = {
            'api_server': {'status': 'running', 'pid': os.getpid()},
            'websocket': {'status': 'stopped', 'pid': None},
            'bot_management': {'status': 'stopped', 'pid': None}
        }
        
        # Check WebSocket server
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'websocket_server.py' in ' '.join(cmdline):
                    services['websocket'] = {
                        'status': 'running',
                        'pid': proc.info['pid']
                    }
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check Bot Management System
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'bot_management_system.py' in ' '.join(cmdline):
                    services['bot_management'] = {
                        'status': 'running',
                        'pid': proc.info['pid']
                    }
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify(services)
    
    except Exception as e:
        logger.error(f"Service status check failed: {e}")
        return jsonify({'error': str(e)}), 500

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)