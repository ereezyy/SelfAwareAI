#!/usr/bin/env python3.11
"""
API Server for Bot Management System
Provides HTTP API endpoints and serves the web interface
"""

import os
import sys
import json
import psutil
import subprocess
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging

# Import bot components
try:
    from bot_launcher import BotManager
except ImportError:
    BotManager = None
    logger.warning("Could not import BotManager - some endpoints will be unavailable")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global process tracking
running_processes = {}

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': psutil.boot_time(),
        'api_server': 'running'
    })

@app.route('/api/backend/status')
def get_backend_status():
    """Get status of all backend services"""
    try:
        services = {
            'api_server': {
                'running': True,
                'pid': os.getpid(),
                'status': 'running',
                'cpu_percent': psutil.Process(os.getpid()).cpu_percent(),
                'memory_percent': psutil.Process(os.getpid()).memory_percent()
            },
            'websocket': {
                'running': is_service_running('websocket_server.py'),
                'pid': get_service_pid('websocket_server.py'),
                'status': 'running' if is_service_running('websocket_server.py') else 'stopped'
            }
        }
        
        return jsonify({
            'success': True,
            'services': services
        })
    except Exception as e:
        logger.error(f"Error getting backend status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bot/status')
def get_bot_status():
    """Get bot status endpoint"""
    try:
        if BotManager is None:
            return jsonify({
                'success': False,
                'error': 'BotManager not available'
            }), 503
            
        return jsonify({
            'success': True,
            'status': 'operational',
            'websocket_running': is_service_running('websocket_server.py'),
            'api_server_running': True
        })
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/humanize', methods=['POST'])
def humanize_text():
    """Humanize text endpoint"""
    try:
        if BotManager is None:
            return jsonify({
                'success': False,
                'error': 'BotManager not available'
            }), 503
            
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text field required'
            }), 400
            
        # Placeholder response - actual implementation would use BotManager
        return jsonify({
            'success': True,
            'humanized_text': data['text'],  # Placeholder
            'message': 'Text processing complete'
        })
    except Exception as e:
        logger.error(f"Error in humanize endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detect', methods=['POST'])
def detect_ai_text():
    """AI text detection endpoint"""
    try:
        if BotManager is None:
            return jsonify({
                'success': False,
                'error': 'BotManager not available'
            }), 503
            
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text field required'
            }), 400
            
        # Placeholder response - actual implementation would use BotManager
        return jsonify({
            'success': True,
            'is_ai_generated': False,  # Placeholder
            'confidence': 0.5,
            'message': 'Detection complete'
        })
    except Exception as e:
        logger.error(f"Error in detect endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backend/start/<service>', methods=['POST'])
def start_service(service):
    """Start a backend service"""
    try:
        if service == 'api_server':
            return jsonify({
                'success': True,
                'message': 'API Server is already running'
            })
        
        elif service == 'websocket':
            if is_service_running('websocket_server.py'):
                return jsonify({
                    'success': False,
                    'error': 'WebSocket server is already running'
                })
            
            # Ensure proper process tracking
            process = subprocess.Popen([
                sys.executable, 'websocket_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            running_processes['websocket'] = process
            
            # Give the process time to start
            time.sleep(2)
            
            if process.poll() is None:  # Process is still running
                return jsonify({
                    'success': True,
                    'message': f'WebSocket server started with PID {process.pid}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'WebSocket server failed to start'
                })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown service: {service}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting {service}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backend/stop/<service>', methods=['POST'])
def stop_service(service):
    """Stop a backend service"""
    try:
        if service == 'api_server':
            return jsonify({
                'success': False,
                'error': 'Cannot stop API server from itself'
            }), 400
        
        elif service == 'websocket':
            script_name = 'websocket_server.py'
            
            # Find and terminate the process
            terminated = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                        terminated = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Also clean up from running_processes if exists
            if 'websocket' in running_processes:
                try:
                    running_processes['websocket'].terminate()
                    del running_processes['websocket']
                except:
                    pass
            
            if terminated:
                return jsonify({
                    'success': True,
                    'message': 'WebSocket service stopped'
                })
            else:
                        return jsonify({
                            'success': True,
                    'message': 'WebSocket service was not running'
                        })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown service: {service}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error stopping {service}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backend/restart/<service>', methods=['POST'])
def restart_service(service):
    """Restart a backend service"""
    try:
        # Stop the service first
        stop_response = stop_service(service)
        
        # Wait a moment for cleanup
        time.sleep(2)
        
        # Start the service
        start_response = start_service(service)
        return start_response
        
    except Exception as e:
        logger.error(f"Error restarting {service}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def is_service_running(script_name):
    """Check if a service script is running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
                return True
        return False
    except Exception:
        return False

def get_service_pid(script_name):
    """Get the PID of a running service"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
                return proc.info['pid']
        return None
    except Exception:
        return None

if __name__ == '__main__':
    logger.info("🚀 Starting Bot Management API Server...")
    logger.info("📊 API Server available at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)