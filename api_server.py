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
import threading
import time
import websockets
import json as json_module
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add the current directory to Python path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot modules with error handling
try:
    from self_aware_module import SelfAwareModule
    from self_healing_coding_module import SelfHealingModule, SelfCodingModule
    from text_humanization_module import TextHumanizer
    from ai_text_detection_module import AITextDetector
    from command_interface import CommandInterface
    from bot_management_system import DirectorBot, BotCommand, BotStatus, BotType
    from bot_management_system import AnalyzerBot, GeneratorBot, MonitorBot, BotSwarm
    from bot_management_system import get_director_bot
    from bot_management_system import DirectorBot, BotCommand, BotStatus, BotType
    from bot_management_system import AnalyzerBot, GeneratorBot, MonitorBot, BotSwarm
    
    BOT_MODULES_AVAILABLE = True
    print("✅ All bot modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import bot modules: {e}")
    BOT_MODULES_AVAILABLE = False

# Flask app configuration
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
bot_interface = None
uploaded_files = {}  # Track uploaded files by session
director_bot = None
websocket_server = None
websocket_clients = set()

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'.py', '.json', '.txt', '.md'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    """Check if file extension is allowed."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def generate_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def validate_json_request():
    """Validate that request contains valid JSON."""
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    
    data = request.get_json()
    if data is None:
        return {'error': 'Invalid JSON in request body'}, 400
    
    return data, None

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present and not empty."""
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
        if not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            return f"Field '{field}' cannot be empty"
    return None

async def broadcast_to_websockets(message):
    """Broadcast message to all connected WebSocket clients."""
    if not websocket_clients:
        return
    
    message_str = json_module.dumps(message) if isinstance(message, dict) else str(message)
    disconnected_clients = set()
    
    for client in websocket_clients.copy():
        try:
            await client.send(message_str)
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")
            disconnected_clients.add(client)
    
    # Remove disconnected clients
    websocket_clients -= disconnected_clients

async def websocket_handler(websocket, path):
    """Handle WebSocket connections for real-time updates."""
    websocket_clients.add(websocket)
    logger.info(f"New WebSocket client connected. Total: {len(websocket_clients)}")
    
    try:
        # Send initial status
        initial_status = {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'client_count': len(websocket_clients)
        }
        await websocket.send(json_module.dumps(initial_status))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json_module.loads(message)
                # Handle WebSocket commands here if needed
                logger.info(f"WebSocket message received: {data}")
            except json_module.JSONDecodeError as e:
                error_msg = {'type': 'error', 'message': f'Invalid JSON: {str(e)}'}
                await websocket.send(json_module.dumps(error_msg))
            except Exception as e:
                error_msg = {'type': 'error', 'message': str(e)}
                await websocket.send(json_module.dumps(error_msg))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(websocket_clients)}")

def start_websocket_server():
    """Start WebSocket server in a separate thread."""
    global websocket_server
    
    async def run_server():
        global websocket_server
        try:
            websocket_server = await websockets.serve(
                websocket_handler,
                "localhost",
                8765,
                ping_interval=20,
                ping_timeout=10
            )
            logger.info("🌐 WebSocket server started on ws://localhost:8765")
            await websocket_server.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_server())
        except Exception as e:
            logger.error(f"WebSocket thread error: {e}")
        finally:
            loop.close()
    
    websocket_thread = threading.Thread(target=run_in_thread, daemon=True)
    websocket_thread.start()
    logger.info("🚀 WebSocket server thread started")

async def initialize_director_bot():
    """Initialize Director Bot in async context."""
    global director_bot
    try:
        if BOT_MODULES_AVAILABLE:
            director_bot = get_director_bot()
            await director_bot.start()
            logger.info("✅ Director Bot initialized and started")
            return True
    except Exception as e:
        logger.error(f"Failed to initialize Director Bot: {e}")
        director_bot = None
    return False

def start_director_bot():
    """Start Director Bot in a separate thread."""
    def run_director():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(initialize_director_bot())
            # Keep the loop running for Director Bot operations
            loop.run_forever()
        except Exception as e:
            logger.error(f"Director Bot thread error: {e}")
        finally:
            loop.close()
    
    director_thread = threading.Thread(target=run_director, daemon=True)
    director_thread.start()
    logger.info("🤖 Director Bot thread started")

def initialize_bot_modules():
    """Initialize all bot modules with comprehensive error handling."""
    global bot_interface, director_bot
    
    if not MODULES_AVAILABLE:
        logger.warning("Bot modules not available - API will return error responses")
        return False
    
    try:
        logger.info("🚀 Initializing bot modules...")
        
        # Initialize core modules
        awareness_module = SelfAwareModule()
        logger.info("✅ Self-Awareness module initialized")
        
        healing_module = SelfHealingModule(awareness_module=awareness_module)
        logger.info("✅ Self-Healing module initialized")
        
        coding_module = SelfCodingModule(awareness_module=awareness_module)
        logger.info("✅ Self-Coding module initialized")
        
        # Initialize text processing modules (may fail due to model requirements)
        humanizer_module = None
        ai_detector_module = None
        
        try:
            logger.info("📝 Loading text humanizer (this may take time for model download)...")
            humanizer_module = TextHumanizer()
            logger.info("✅ Text humanizer module initialized")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize text humanizer: {e}")
        
        try:
            logger.info("🤖 Loading AI detector (this may take time for model download)...")
            ai_detector_module = AITextDetector()
            logger.info("✅ AI detector module initialized")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize AI detector: {e}")
        
        # Create command interface
        bot_interface = CommandInterface(
            awareness_module=awareness_module,
            healing_module=healing_module,
            coding_module=coding_module,
            humanizer_module=humanizer_module,
            ai_detector_module=ai_detector_module
        )
        
        logger.info("🎉 Bot modules initialized successfully!")
        
        # Start Director Bot and WebSocket server
        start_director_bot()
        start_websocket_server()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot modules: {e}")
        return False

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
            'bot_initialized': bot_interface is not None
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
def upload_file():
    """Handle file uploads with proper validation and storage."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename or not file.filename.strip():
            return jsonify({'error': 'Invalid filename'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Generate secure filename and session ID
        filename = secure_filename(file.filename)
        session_id = generate_session_id()
        filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
        
        # Save file
        file.save(filepath)
        
        # Store file info in session
        file_info = {
            'original_name': filename,
            'filepath': filepath,
            'upload_time': datetime.now().isoformat(),
            'size': os.path.getsize(filepath)
        }
        uploaded_files[session_id] = file_info
        
        logger.info(f"File uploaded: {filename} -> {filepath}")
        
        # Broadcast file upload event
        asyncio.create_task(broadcast_to_websockets({
            'type': 'file_uploaded',
            'filename': filename,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }))
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'message': f'File {filename} uploaded successfully',
            'file_info': file_info
        })
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/command', methods=['POST'])
def handle_generic_command():
    """Handle generic bot commands."""
    return _process_command_request()

@app.route('/api/analyze/structure', methods=['POST'])
def analyze_code_structure():
    """Analyze code structure of uploaded file."""
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
        return _execute_bot_command('analyze_code', [filepath])
        
    except Exception as e:
        logger.error(f"Structure analysis failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/quality', methods=['POST'])
def analyze_code_quality():
    """Analyze code quality of uploaded file."""
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
        return _execute_bot_command('analyze_quality', [filepath])
        
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/code', methods=['POST'])
def generate_code():
    """Generate code using templates."""
    try:
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        validation_error = validate_required_fields(data, ['code_type', 'name'])
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        code_type = data.get('code_type')
        name = data.get('name')
        params = data.get('params', {})
        
        # Build arguments
        args = [code_type, name]
        for key, value in params.items():
            args.extend([key, value])
        
        return _execute_bot_command('generate_code', args)
        
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/tests', methods=['POST'])
def generate_tests():
    """Generate unit tests for uploaded file."""
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
        return _execute_bot_command('generate_tests', [filepath])
        
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        return jsonify({'error': str(e)}), 500

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
def humanize_text():
    """Humanize text using AI."""
    try:
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        validation_error = validate_required_fields(data, ['text'])
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        text = data.get('text')
        
        return _execute_bot_command('humanize_text', [text])
        
    except Exception as e:
        logger.error(f"Text humanization failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/text/detect', methods=['POST'])
def detect_ai_text():
    """Detect if text is AI-generated."""
    try:
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        validation_error = validate_required_fields(data, ['text'])
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        text = data.get('text')
        
        return _execute_bot_command('detect_ai_text', [text])
        
    except Exception as e:
        logger.error(f"AI text detection failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system status."""
    return _execute_bot_command('status', [])

@app.route('/api/autonomy/enable', methods=['POST'])
def enable_autonomy():
    """Enable autonomous self-healing."""
    return _execute_bot_command('enable_autonomy', [])

@app.route('/api/autonomy/disable', methods=['POST'])
def disable_autonomy():
    """Disable autonomous self-healing."""
    return _execute_bot_command('disable_autonomy', [])

@app.route('/api/autonomy/status', methods=['GET'])
def get_autonomy_status():
    """Get autonomy and health status."""
    return _execute_bot_command('autonomy_status', [])

@app.route('/api/system/health-check', methods=['POST'])
def force_health_check():
    """Force immediate health check."""
    return _execute_bot_command('force_health_check', [])

@app.route('/api/system/optimize', methods=['POST'])
def optimize_system():
    """Trigger system optimization."""
    return _execute_bot_command('system_optimize', [])

@app.route('/api/system/recovery-history', methods=['GET'])
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
def websocket_info():
    """Get WebSocket server information."""
    return jsonify({
        'websocket_url': 'ws://localhost:8765',
        'connected_clients': len(websocket_clients),
        'server_running': websocket_server is not None
    })

@app.route('/api/bots', methods=['GET'])
def list_all_bots():
    """List all bots managed by Director Bot"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        if not BOT_MODULES_AVAILABLE:
            return jsonify({'error': 'Bot modules not available'}), 503
        
        # Create command to list bots
        from bot_management_system import BotCommand
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='list_bots'
        )
        
        # Execute command synchronously (we'll need async support for better implementation)
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
        logger.error(f"List bots failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots', methods=['POST'])
def create_bot():
    """Create a new bot"""
    try:
        if not director_bot:
            return jsonify({'error': 'Director Bot not available'}), 503
        
        if not BOT_MODULES_AVAILABLE:
            return jsonify({'error': 'Bot modules not available'}), 503
        
        data, error = validate_json_request()
        if error:
            return jsonify(error[0]), error[1]
        
        bot_type = data.get('bot_type', 'custom')
        bot_name = data.get('name', f'{bot_type}_bot')
        
        from bot_management_system import BotCommand
        command = BotCommand(
            command_id=str(uuid.uuid4()),
            command_type='create_bot',
            parameters={
                'bot_type': bot_type,
                'name': bot_name
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
        logger.error(f"Create bot failed: {e}")
        return jsonify({'error': str(e)}), 500

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

# Helper functions

def _process_command_request():
    """Process generic command requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        command = data.get('command')
        args = data.get('args', [])
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        return _execute_bot_command(command, args)
        
    except Exception as e:
        logger.error(f"Command processing failed: {e}")
        return jsonify({'error': str(e)}), 500

def _execute_bot_command(command, args):
    """Execute a bot command with proper error handling."""
    global bot_interface
    
    try:
        # Initialize bot if not already done
        if bot_interface is None:
            if not initialize_bot_modules():
                return jsonify({
                    'success': False,
                    'result': 'Error: Bot modules not available. Please check if all dependencies are installed.'
                })
        
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
        asyncio.create_task(broadcast_to_websockets({
            'type': 'command_executed',
            'command': command_str,
            'result': result[:200] + '...' if len(result) > 200 else result,
            'timestamp': datetime.now().isoformat()
        }))
        
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

# Error handlers

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
    print("🚀 Starting AI Bot API Server...")
    print("=" * 50)
    
    # Initialize bot modules on startup
    initialization_success = initialize_bot_modules()
    
    if initialization_success:
        print("✅ Bot modules initialized successfully")
    else:
        print("⚠️  Running with limited functionality - some bot modules not available")
    
    print("=" * 50)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 3000))
    print(f"🌐 API server starting on http://localhost:{port}")
    print(f"📊 Health check: http://localhost:{port}/api/health")
    print(f"🎯 API endpoints available at /api/*")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)