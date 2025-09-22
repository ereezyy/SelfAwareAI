#!/usr/bin/env python3.11
"""
WebSocket Server for Real-time Bot Management Communication
Handles real-time updates between web interface and bot management system
"""

import asyncio
import websockets
import json
import logging
from bot_management_system import websocket_handler, get_director_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotWebSocketServer:
    """WebSocket server for bot management real-time communication"""
    
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.server = None
        self.director = None
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting WebSocket server on ws://{self.host}:{self.port}")
        
        # Initialize director bot
        self.director = get_director_bot()
        await self.director.start()
        
        # Start WebSocket server
        self.server = await websockets.serve(
            websocket_handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info("✅ WebSocket server started successfully")
        logger.info(f"🌐 Bot Management System available at ws://{self.host}:{self.port}")
        
        # Keep server running
        await self.server.wait_closed()
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            logger.info("🛑 Stopping WebSocket server...")
            self.server.close()
            await self.server.wait_closed()
            
        if self.director:
            await self.director.stop()
            
        logger.info("✅ WebSocket server stopped")

async def main():
    """Main entry point"""
    server = BotWebSocketServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
        await server.stop_server()
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        await server.stop_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot Management System shutdown complete")