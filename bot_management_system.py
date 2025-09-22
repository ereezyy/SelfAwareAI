#!/usr/bin/env python3
"""
Comprehensive Bot Management System with Hierarchical Control
Implements Director Bot, Sub Bots, Swarm Management, and Real-time Monitoring
"""

import logging
import asyncio
import json
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import queue
import websockets
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Status Enumeration
class BotStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"

# Bot Types
class BotType(Enum):
    DIRECTOR = "director"
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    MONITOR = "monitor"
    EXECUTOR = "executor"
    CUSTOM = "custom"

@dataclass
class BotCommand:
    """Command structure for bot communication"""
    command_id: str
    command_type: str
    target_bot: Optional[str] = None
    target_swarm: Optional[str] = None
    parameters: Dict[str, Any] = None
    timestamp: float = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.parameters is None:
            self.parameters = {}

@dataclass
class BotMetrics:
    """Bot performance metrics"""
    commands_executed: int = 0
    uptime: float = 0
    cpu_usage: float = 0
    memory_usage: float = 0
    last_activity: float = None
    error_count: int = 0
    success_rate: float = 100.0

class BaseBotInterface(ABC):
    """Abstract base class for all bots"""
    
    def __init__(self, bot_id: str, bot_type: BotType, name: str = None):
        self.bot_id = bot_id
        self.bot_type = bot_type
        self.name = name or f"{bot_type.value}_{bot_id[:8]}"
        self.status = BotStatus.IDLE
        self.created_at = time.time()
        self.metrics = BotMetrics()
        self.command_queue = asyncio.Queue()
        self.is_running = False
        self.logger = logging.getLogger(f"Bot.{self.name}")
        self.listeners = set()
        
    @abstractmethod
    async def execute_command(self, command: BotCommand) -> Dict[str, Any]:
        """Execute a specific command"""
        pass
    
    @abstractmethod
    async def start(self):
        """Start the bot"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the bot"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            'bot_id': self.bot_id,
            'name': self.name,
            'type': self.bot_type.value,
            'status': self.status.value,
            'created_at': self.created_at,
            'uptime': time.time() - self.created_at,
            'metrics': asdict(self.metrics),
            'is_running': self.is_running
        }
    
    def add_listener(self, callback):
        """Add status change listener"""
        self.listeners.add(callback)
    
    def remove_listener(self, callback):
        """Remove status change listener"""
        self.listeners.discard(callback)
    
    def _notify_listeners(self, event_type: str, data: Dict[str, Any]):
        """Notify all listeners of status changes"""
        for callback in self.listeners.copy():
            try:
                callback(self.bot_id, event_type, data)
            except Exception as e:
                self.logger.error(f"Listener notification failed: {e}")

class SubBot(BaseBotInterface):
    """Base implementation for Sub Bots"""
    
    def __init__(self, bot_id: str, bot_type: BotType, name: str = None):
        super().__init__(bot_id, bot_type, name)
        self.director_connection = None
        self.task_handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default command handlers"""
        self.task_handlers.update({
            'ping': self._handle_ping,
            'status': self._handle_status_request,
            'shutdown': self._handle_shutdown,
            'configure': self._handle_configuration
        })
    
    async def _handle_ping(self, command: BotCommand) -> Dict[str, Any]:
        """Handle ping command"""
        return {
            'status': 'success',
            'message': f'Pong from {self.name}',
            'timestamp': time.time()
        }
    
    async def _handle_status_request(self, command: BotCommand) -> Dict[str, Any]:
        """Handle status request"""
        return {
            'status': 'success',
            'data': self.get_status()
        }
    
    async def _handle_shutdown(self, command: BotCommand) -> Dict[str, Any]:
        """Handle shutdown command"""
        await self.stop()
        return {
            'status': 'success',
            'message': f'{self.name} shutting down'
        }
    
    async def _handle_configuration(self, command: BotCommand) -> Dict[str, Any]:
        """Handle configuration updates"""
        config = command.parameters.get('config', {})
        # Apply configuration changes
        return {
            'status': 'success',
            'message': f'{self.name} configuration updated'
        }
    
    async def execute_command(self, command: BotCommand) -> Dict[str, Any]:
        """Execute command using registered handlers"""
        self.metrics.last_activity = time.time()
        self.metrics.commands_executed += 1
        
        try:
            handler = self.task_handlers.get(command.command_type)
            if not handler:
                raise ValueError(f"Unknown command type: {command.command_type}")
            
            self.logger.info(f"Executing command: {command.command_type}")
            result = await handler(command)
            
            # Update success rate
            success_count = self.metrics.commands_executed - self.metrics.error_count
            self.metrics.success_rate = (success_count / self.metrics.commands_executed) * 100
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            self.logger.error(f"Command execution failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'command_id': command.command_id
            }
    
    async def start(self):
        """Start the Sub Bot"""
        self.status = BotStatus.STARTING
        self.is_running = True
        self.logger.info(f"Starting {self.name}")
        
        # Start command processing loop
        asyncio.create_task(self._command_loop())
        
        self.status = BotStatus.IDLE
        self._notify_listeners('started', self.get_status())
    
    async def stop(self):
        """Stop the Sub Bot"""
        self.status = BotStatus.STOPPING
        self.is_running = False
        self.logger.info(f"Stopping {self.name}")
        
        self.status = BotStatus.STOPPED
        self._notify_listeners('stopped', self.get_status())
    
    async def _command_loop(self):
        """Main command processing loop"""
        while self.is_running:
            try:
                # Wait for commands with timeout
                command = await asyncio.wait_for(
                    self.command_queue.get(), 
                    timeout=1.0
                )
                
                self.status = BotStatus.ACTIVE
                result = await self.execute_command(command)
                
                # Send result back to director if needed
                if self.director_connection:
                    await self._send_to_director({
                        'type': 'command_result',
                        'command_id': command.command_id,
                        'result': result
                    })
                
                self.status = BotStatus.IDLE
                
            except asyncio.TimeoutError:
                # No commands, continue loop
                continue
            except Exception as e:
                self.logger.error(f"Command loop error: {e}")
                self.status = BotStatus.ERROR
    
    async def _send_to_director(self, message: Dict[str, Any]):
        """Send message to Director Bot"""
        if self.director_connection:
            try:
                await self.director_connection.put(message)
            except Exception as e:
                self.logger.error(f"Failed to send to director: {e}")

# Specialized Sub Bot Implementations
class AnalyzerBot(SubBot):
    """Bot specialized for code analysis tasks"""
    
    def __init__(self, bot_id: str, name: str = None):
        super().__init__(bot_id, BotType.ANALYZER, name)
        self.task_handlers.update({
            'analyze_code': self._analyze_code,
            'quality_check': self._quality_check
        })
    
    async def _analyze_code(self, command: BotCommand) -> Dict[str, Any]:
        """Analyze code structure"""
        filepath = command.parameters.get('filepath')
        if not filepath:
            raise ValueError("filepath parameter required")
        
        # Simulate code analysis
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            'status': 'success',
            'analysis': {
                'file': filepath,
                'functions': 5,
                'classes': 2,
                'lines': 150,
                'complexity': 'medium'
            }
        }
    
    async def _quality_check(self, command: BotCommand) -> Dict[str, Any]:
        """Perform quality check"""
        filepath = command.parameters.get('filepath')
        
        # Simulate quality analysis
        await asyncio.sleep(0.8)
        
        return {
            'status': 'success',
            'quality_score': 85,
            'issues': ['Missing docstring in function foo()']
        }

class GeneratorBot(SubBot):
    """Bot specialized for code generation tasks"""
    
    def __init__(self, bot_id: str, name: str = None):
        super().__init__(bot_id, BotType.GENERATOR, name)
        self.task_handlers.update({
            'generate_code': self._generate_code,
            'create_tests': self._create_tests
        })
    
    async def _generate_code(self, command: BotCommand) -> Dict[str, Any]:
        """Generate code based on template"""
        code_type = command.parameters.get('code_type')
        name = command.parameters.get('name')
        
        # Simulate code generation
        await asyncio.sleep(1.0)
        
        return {
            'status': 'success',
            'generated_code': f"class {name}:\n    def __init__(self):\n        pass",
            'type': code_type
        }
    
    async def _create_tests(self, command: BotCommand) -> Dict[str, Any]:
        """Create unit tests"""
        filepath = command.parameters.get('filepath')
        
        await asyncio.sleep(0.7)
        
        return {
            'status': 'success',
            'test_file': f"test_{filepath}",
            'tests_created': 3
        }

class MonitorBot(SubBot):
    """Bot specialized for system monitoring"""
    
    def __init__(self, bot_id: str, name: str = None):
        super().__init__(bot_id, BotType.MONITOR, name)
        self.task_handlers.update({
            'health_check': self._health_check,
            'monitor_system': self._monitor_system
        })
    
    async def _health_check(self, command: BotCommand) -> Dict[str, Any]:
        """Perform system health check"""
        await asyncio.sleep(0.3)
        
        return {
            'status': 'success',
            'health': {
                'cpu': 45.2,
                'memory': 67.8,
                'disk': 23.1,
                'overall': 'healthy'
            }
        }
    
    async def _monitor_system(self, command: BotCommand) -> Dict[str, Any]:
        """Start system monitoring"""
        duration = command.parameters.get('duration', 60)
        
        return {
            'status': 'success',
            'message': f'Monitoring started for {duration} seconds'
        }

@dataclass
class SwarmTemplate:
    """Template for creating bot swarms"""
    name: str
    description: str
    bot_types: List[Dict[str, Any]]
    default_size: int
    configuration: Dict[str, Any] = None

class BotSwarm:
    """Manages a group of bots working together"""
    
    def __init__(self, swarm_id: str, name: str, template: SwarmTemplate = None):
        self.swarm_id = swarm_id
        self.name = name
        self.template = template
        self.bots: Dict[str, BaseBotInterface] = {}
        self.created_at = time.time()
        self.status = BotStatus.IDLE
        self.logger = logging.getLogger(f"Swarm.{name}")
    
    def add_bot(self, bot: BaseBotInterface):
        """Add a bot to the swarm"""
        self.bots[bot.bot_id] = bot
        self.logger.info(f"Added bot {bot.name} to swarm {self.name}")
    
    def remove_bot(self, bot_id: str) -> bool:
        """Remove a bot from the swarm"""
        if bot_id in self.bots:
            bot = self.bots.pop(bot_id)
            self.logger.info(f"Removed bot {bot.name} from swarm {self.name}")
            return True
        return False
    
    async def start_all(self):
        """Start all bots in the swarm"""
        self.status = BotStatus.STARTING
        tasks = []
        
        for bot in self.bots.values():
            tasks.append(bot.start())
        
        await asyncio.gather(*tasks)
        self.status = BotStatus.ACTIVE
        self.logger.info(f"Started swarm {self.name} with {len(self.bots)} bots")
    
    async def stop_all(self):
        """Stop all bots in the swarm"""
        self.status = BotStatus.STOPPING
        tasks = []
        
        for bot in self.bots.values():
            tasks.append(bot.stop())
        
        await asyncio.gather(*tasks)
        self.status = BotStatus.STOPPED
        self.logger.info(f"Stopped swarm {self.name}")
    
    async def broadcast_command(self, command: BotCommand):
        """Send command to all bots in swarm"""
        tasks = []
        for bot in self.bots.values():
            bot_command = BotCommand(
                command_id=f"{command.command_id}_{bot.bot_id}",
                command_type=command.command_type,
                parameters=command.parameters.copy()
            )
            tasks.append(bot.command_queue.put(bot_command))
        
        await asyncio.gather(*tasks)
    
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status"""
        bot_statuses = {}
        for bot_id, bot in self.bots.items():
            bot_statuses[bot_id] = bot.get_status()
        
        return {
            'swarm_id': self.swarm_id,
            'name': self.name,
            'status': self.status.value,
            'bot_count': len(self.bots),
            'bots': bot_statuses,
            'created_at': self.created_at,
            'uptime': time.time() - self.created_at
        }

class DirectorBot(BaseBotInterface):
    """Central command bot that manages all Sub Bots and Swarms"""
    
    def __init__(self):
        super().__init__(
            bot_id=str(uuid.uuid4()),
            bot_type=BotType.DIRECTOR,
            name="DirectorBot"
        )
        self.sub_bots: Dict[str, BaseBotInterface] = {}
        self.swarms: Dict[str, BotSwarm] = {}
        self.command_history: List[Dict[str, Any]] = []
        self.result_queue = asyncio.Queue()
        self.websocket_clients = set()
        
        # Initialize swarm templates
        self.swarm_templates = self._initialize_swarm_templates()
        
        # Command handlers
        self.command_handlers = {
            'create_bot': self._handle_create_bot,
            'create_swarm': self._handle_create_swarm,
            'start_bot': self._handle_start_bot,
            'stop_bot': self._handle_stop_bot,
            'start_swarm': self._handle_start_swarm,
            'stop_swarm': self._handle_stop_swarm,
            'get_status': self._handle_get_status,
            'delegate_command': self._handle_delegate_command,
            'broadcast_to_swarm': self._handle_broadcast_to_swarm,
            'list_bots': self._handle_list_bots,
            'list_swarms': self._handle_list_swarms
        }
    
    def _initialize_swarm_templates(self) -> Dict[str, SwarmTemplate]:
        """Initialize predefined swarm templates"""
        return {
            'code_analysis': SwarmTemplate(
                name="Code Analysis Swarm",
                description="Specialized swarm for code analysis and quality checking",
                bot_types=[
                    {'type': 'analyzer', 'count': 2},
                    {'type': 'monitor', 'count': 1}
                ],
                default_size=3
            ),
            'code_generation': SwarmTemplate(
                name="Code Generation Swarm", 
                description="Swarm optimized for code generation and testing",
                bot_types=[
                    {'type': 'generator', 'count': 2},
                    {'type': 'analyzer', 'count': 1}
                ],
                default_size=3
            ),
            'full_service': SwarmTemplate(
                name="Full Service Swarm",
                description="Complete swarm with all bot types",
                bot_types=[
                    {'type': 'analyzer', 'count': 2},
                    {'type': 'generator', 'count': 2},
                    {'type': 'monitor', 'count': 1}
                ],
                default_size=5
            )
        }
    
    async def execute_command(self, command: BotCommand) -> Dict[str, Any]:
        """Execute director-level command"""
        self.metrics.last_activity = time.time()
        self.metrics.commands_executed += 1
        
        # Log command
        self.command_history.append({
            'command': asdict(command),
            'timestamp': time.time(),
            'status': 'executing'
        })
        
        try:
            handler = self.command_handlers.get(command.command_type)
            if not handler:
                return await self._handle_delegate_command(command)
            
            result = await handler(command)
            
            # Update command history
            if self.command_history:
                self.command_history[-1]['status'] = 'completed'
                self.command_history[-1]['result'] = result
            
            # Broadcast status update
            await self._broadcast_status_update()
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            self.logger.error(f"Director command failed: {e}")
            
            if self.command_history:
                self.command_history[-1]['status'] = 'error'
                self.command_history[-1]['error'] = str(e)
            
            return {
                'status': 'error',
                'message': str(e),
                'command_id': command.command_id
            }
    
    async def _handle_create_bot(self, command: BotCommand) -> Dict[str, Any]:
        """Create a new Sub Bot"""
        bot_type = command.parameters.get('bot_type', 'custom')
        bot_name = command.parameters.get('name')
        
        bot_id = str(uuid.uuid4())
        
        # Create appropriate bot type
        bot_classes = {
            'analyzer': AnalyzerBot,
            'generator': GeneratorBot,
            'monitor': MonitorBot
        }
        
        bot_class = bot_classes.get(bot_type, SubBot)
        bot = bot_class(bot_id, bot_name)
        
        # Add listener for bot events
        bot.add_listener(self._handle_bot_event)
        
        self.sub_bots[bot_id] = bot
        
        return {
            'status': 'success',
            'bot_id': bot_id,
            'message': f'Created {bot_type} bot: {bot.name}'
        }
    
    async def _handle_create_swarm(self, command: BotCommand) -> Dict[str, Any]:
        """Create a new bot swarm"""
        swarm_name = command.parameters.get('name', f'Swarm_{int(time.time())}')
        template_name = command.parameters.get('template')
        custom_config = command.parameters.get('config', {})
        
        swarm_id = str(uuid.uuid4())
        template = self.swarm_templates.get(template_name) if template_name else None
        
        swarm = BotSwarm(swarm_id, swarm_name, template)
        
        # Create bots based on template
        if template:
            for bot_type_config in template.bot_types:
                bot_type = bot_type_config['type']
                count = bot_type_config.get('count', 1)
                
                for i in range(count):
                    create_cmd = BotCommand(
                        command_id=str(uuid.uuid4()),
                        command_type='create_bot',
                        parameters={
                            'bot_type': bot_type,
                            'name': f'{swarm_name}_{bot_type}_{i+1}'
                        }
                    )
                    
                    result = await self._handle_create_bot(create_cmd)
                    if result['status'] == 'success':
                        bot = self.sub_bots[result['bot_id']]
                        swarm.add_bot(bot)
        
        self.swarms[swarm_id] = swarm
        
        return {
            'status': 'success',
            'swarm_id': swarm_id,
            'message': f'Created swarm: {swarm_name} with {len(swarm.bots)} bots'
        }
    
    async def _handle_start_bot(self, command: BotCommand) -> Dict[str, Any]:
        """Start a specific bot"""
        bot_id = command.parameters.get('bot_id')
        if bot_id not in self.sub_bots:
            raise ValueError(f"Bot {bot_id} not found")
        
        bot = self.sub_bots[bot_id]
        await bot.start()
        
        return {
            'status': 'success',
            'message': f'Started bot: {bot.name}'
        }
    
    async def _handle_stop_bot(self, command: BotCommand) -> Dict[str, Any]:
        """Stop a specific bot"""
        bot_id = command.parameters.get('bot_id')
        if bot_id not in self.sub_bots:
            raise ValueError(f"Bot {bot_id} not found")
        
        bot = self.sub_bots[bot_id]
        await bot.stop()
        
        return {
            'status': 'success',
            'message': f'Stopped bot: {bot.name}'
        }
    
    async def _handle_start_swarm(self, command: BotCommand) -> Dict[str, Any]:
        """Start all bots in a swarm"""
        swarm_id = command.parameters.get('swarm_id')
        if swarm_id not in self.swarms:
            raise ValueError(f"Swarm {swarm_id} not found")
        
        swarm = self.swarms[swarm_id]
        await swarm.start_all()
        
        return {
            'status': 'success',
            'message': f'Started swarm: {swarm.name}'
        }
    
    async def _handle_stop_swarm(self, command: BotCommand) -> Dict[str, Any]:
        """Stop all bots in a swarm"""
        swarm_id = command.parameters.get('swarm_id')
        if swarm_id not in self.swarms:
            raise ValueError(f"Swarm {swarm_id} not found")
        
        swarm = self.swarms[swarm_id]
        await swarm.stop_all()
        
        return {
            'status': 'success',
            'message': f'Stopped swarm: {swarm.name}'
        }
    
    async def _handle_delegate_command(self, command: BotCommand) -> Dict[str, Any]:
        """Delegate command to appropriate Sub Bot"""
        target_bot = command.target_bot
        
        if not target_bot or target_bot not in self.sub_bots:
            # Find appropriate bot type for command
            command_to_bot_mapping = {
                'analyze_code': 'analyzer',
                'quality_check': 'analyzer',
                'generate_code': 'generator',
                'create_tests': 'generator',
                'health_check': 'monitor',
                'monitor_system': 'monitor'
            }
            
            preferred_bot_type = command_to_bot_mapping.get(command.command_type)
            if preferred_bot_type:
                # Find first available bot of preferred type
                for bot in self.sub_bots.values():
                    if (bot.bot_type.value == preferred_bot_type and 
                        bot.status == BotStatus.IDLE):
                        target_bot = bot.bot_id
                        break
        
        if not target_bot or target_bot not in self.sub_bots:
            raise ValueError(f"No suitable bot found for command: {command.command_type}")
        
        bot = self.sub_bots[target_bot]
        await bot.command_queue.put(command)
        
        return {
            'status': 'success',
            'message': f'Command delegated to {bot.name}',
            'target_bot': target_bot
        }
    
    async def _handle_broadcast_to_swarm(self, command: BotCommand) -> Dict[str, Any]:
        """Broadcast command to all bots in a swarm"""
        swarm_id = command.target_swarm
        if not swarm_id or swarm_id not in self.swarms:
            raise ValueError(f"Swarm {swarm_id} not found")
        
        swarm = self.swarms[swarm_id]
        await swarm.broadcast_command(command)
        
        return {
            'status': 'success',
            'message': f'Command broadcast to swarm {swarm.name}',
            'bot_count': len(swarm.bots)
        }
    
    async def _handle_get_status(self, command: BotCommand) -> Dict[str, Any]:
        """Get comprehensive system status"""
        bot_statuses = {}
        swarm_statuses = {}
        
        for bot_id, bot in self.sub_bots.items():
            bot_statuses[bot_id] = bot.get_status()
        
        for swarm_id, swarm in self.swarms.items():
            swarm_statuses[swarm_id] = swarm.get_status()
        
        return {
            'status': 'success',
            'director': self.get_status(),
            'bots': bot_statuses,
            'swarms': swarm_statuses,
            'templates': list(self.swarm_templates.keys())
        }
    
    async def _handle_list_bots(self, command: BotCommand) -> Dict[str, Any]:
        """List all available bots"""
        bots = []
        for bot_id, bot in self.sub_bots.items():
            bots.append({
                'bot_id': bot_id,
                'name': bot.name,
                'type': bot.bot_type.value,
                'status': bot.status.value,
                'uptime': time.time() - bot.created_at
            })
        
        return {
            'status': 'success',
            'bots': bots,
            'total': len(bots)
        }
    
    async def _handle_list_swarms(self, command: BotCommand) -> Dict[str, Any]:
        """List all available swarms"""
        swarms = []
        for swarm_id, swarm in self.swarms.items():
            swarms.append({
                'swarm_id': swarm_id,
                'name': swarm.name,
                'status': swarm.status.value,
                'bot_count': len(swarm.bots),
                'uptime': time.time() - swarm.created_at
            })
        
        return {
            'status': 'success',
            'swarms': swarms,
            'total': len(swarms)
        }
    
    def _handle_bot_event(self, bot_id: str, event_type: str, data: Dict[str, Any]):
        """Handle events from Sub Bots"""
        self.logger.info(f"Bot event: {bot_id} - {event_type}")
        
        # Broadcast event to connected clients
        asyncio.create_task(self._broadcast_bot_event({
            'type': 'bot_event',
            'bot_id': bot_id,
            'event': event_type,
            'data': data,
            'timestamp': time.time()
        }))
    
    async def _broadcast_status_update(self):
        """Broadcast status update to all connected clients"""
        status_data = {
            'type': 'status_update',
            'timestamp': time.time(),
            'director_status': self.get_status(),
            'bot_count': len(self.sub_bots),
            'swarm_count': len(self.swarms)
        }
        
        await self._broadcast_to_websockets(status_data)
    
    async def _broadcast_bot_event(self, event_data: Dict[str, Any]):
        """Broadcast bot event to websocket clients"""
        await self._broadcast_to_websockets(event_data)
    
    async def _broadcast_to_websockets(self, data: Dict[str, Any]):
        """Broadcast data to all connected websocket clients"""
        if not self.websocket_clients:
            return
        
        message = json.dumps(data)
        disconnected_clients = set()
        
        for client in self.websocket_clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"Broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients
    
    def add_websocket_client(self, websocket):
        """Add websocket client for real-time updates"""
        self.websocket_clients.add(websocket)
        self.logger.info(f"Added websocket client. Total: {len(self.websocket_clients)}")
    
    def remove_websocket_client(self, websocket):
        """Remove websocket client"""
        self.websocket_clients.discard(websocket)
        self.logger.info(f"Removed websocket client. Total: {len(self.websocket_clients)}")
    
    async def start(self):
        """Start the Director Bot"""
        self.status = BotStatus.STARTING
        self.is_running = True
        self.logger.info("Starting Director Bot")
        
        # Start command processing loop
        asyncio.create_task(self._director_loop())
        
        self.status = BotStatus.ACTIVE
        await self._broadcast_status_update()
    
    async def stop(self):
        """Stop the Director Bot and all Sub Bots"""
        self.status = BotStatus.STOPPING
        self.logger.info("Stopping Director Bot")
        
        # Stop all swarms
        for swarm in self.swarms.values():
            await swarm.stop_all()
        
        # Stop all remaining bots
        for bot in self.sub_bots.values():
            await bot.stop()
        
        self.is_running = False
        self.status = BotStatus.STOPPED
    
    async def _director_loop(self):
        """Main director processing loop"""
        while self.is_running:
            try:
                # Periodic status broadcast every 5 seconds
                await asyncio.sleep(5)
                await self._broadcast_status_update()
                
            except Exception as e:
                self.logger.error(f"Director loop error: {e}")

# Global Director Bot instance
_director_bot = None

def get_director_bot() -> DirectorBot:
    """Get or create the global Director Bot instance"""
    global _director_bot
    if _director_bot is None:
        _director_bot = DirectorBot()
    return _director_bot

# Websocket handler for real-time communication
async def websocket_handler(websocket, path):
    """Handle websocket connections for real-time updates"""
    director = get_director_bot()
    director.add_websocket_client(websocket)
    
    try:
        # Send initial status
        await websocket.send(json.dumps({
            'type': 'initial_status',
            'data': await director.execute_command(BotCommand(
                command_id=str(uuid.uuid4()),
                command_type='get_status'
            ))
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                command = BotCommand(
                    command_id=data.get('command_id', str(uuid.uuid4())),
                    command_type=data.get('command_type'),
                    parameters=data.get('parameters', {}),
                    target_bot=data.get('target_bot'),
                    target_swarm=data.get('target_swarm')
                )
                
                result = await director.execute_command(command)
                
                await websocket.send(json.dumps({
                    'type': 'command_result',
                    'command_id': command.command_id,
                    'result': result
                }))
                
            except json.JSONDecodeError as e:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Invalid JSON: {str(e)}'
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'type': 'error', 
                    'message': str(e)
                }))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Websocket error: {e}")
    finally:
        director.remove_websocket_client(websocket)

# Example usage and testing
if __name__ == "__main__":
    async def demo():
        """Demonstration of the bot management system"""
        print("🚀 Starting Bot Management System Demo")
        
        # Create and start Director Bot
        director = get_director_bot()
        await director.start()
        
        print("\n📊 Creating bots...")
        
        # Create some bots
        commands = [
            BotCommand("1", "create_bot", parameters={'bot_type': 'analyzer', 'name': 'Analyzer1'}),
            BotCommand("2", "create_bot", parameters={'bot_type': 'generator', 'name': 'Generator1'}),
            BotCommand("3", "create_bot", parameters={'bot_type': 'monitor', 'name': 'Monitor1'}),
        ]
        
        for cmd in commands:
            result = await director.execute_command(cmd)
            print(f"✅ {result['message']}")
        
        print("\n🤖 Creating swarm...")
        
        # Create a swarm
        swarm_cmd = BotCommand(
            "4", "create_swarm", 
            parameters={'name': 'TestSwarm', 'template': 'code_analysis'}
        )
        result = await director.execute_command(swarm_cmd)
        print(f"✅ {result['message']}")
        
        # Get status
        status_cmd = BotCommand("5", "get_status")
        status = await director.execute_command(status_cmd)
        print(f"\n📈 System Status:")
        print(f"  Director: {status['result']['director']['status']}")
        print(f"  Bots: {len(status['result']['bots'])}")
        print(f"  Swarms: {len(status['result']['swarms'])}")
        
        print("\n🎯 Demo completed! System is ready for use.")
        
        return director
    
    # Run the demo
    import asyncio
    director = asyncio.run(demo())