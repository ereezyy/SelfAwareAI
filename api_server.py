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
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
# Global process tracking
running_processes = {}

@app.route('/')
def serve_index():
    """Serve the main index.html file"""
    return send_from_directory('.', 'index.html')

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
            
            process = subprocess.Popen([
                sys.executable, 'websocket_server.py'
            ])
            running_processes['websocket'] = process
            
            return jsonify({
                'success': True,
                'message': f'WebSocket server started with PID {process.pid}'
            })
        
        elif service == 'bot_management':
            if is_service_running('bot_management_system.py'):
                return jsonify({
                    'success': False,
                    'error': 'Bot Management system is already running'
                })
            
            process = subprocess.Popen([
                sys.executable, 'bot_management_system.py'
            ])
            running_processes['bot_management'] = process
            
            return jsonify({
                'success': True,
                'message': f'Bot Management system started with PID {process.pid}'
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
        
        elif service in ['websocket', 'bot_management']:
            script_name = f"{service.replace('_', '_')}_server.py" if service == 'websocket' else 'bot_management_system.py'
            
            # Find and terminate the process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                        return jsonify({
                            'success': True,
                            'message': f'{service.title()} service stopped'
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return jsonify({
                'success': False,
                'error': f'{service.title()} service not found'
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
        if not stop_response[0].get_json().get('success', False):
            # If stop failed, try to start anyway
            pass
        
        # Wait a moment for cleanup
        import time
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
    logger.info("📊 Web interface available at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)