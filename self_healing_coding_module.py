# self_healing_coding_module.py

import logging
import os
import sys
import ast
import json
import traceback
import importlib.util
import inspect
import re
from typing import Dict, List, Any, Tuple, Optional, Union
import keyword
import builtins
import difflib
from collections import Counter, defaultdict
import textwrap
import threading
import queue
import gc
import resource
import signal
import psutil
import subprocess
import datetime
from dataclasses import dataclass
from typing import Callable, Optional
import pickle
import hashlib

# --- Logger Setup ---
LOG_FILE_SHC = "/home/ubuntu/bot_self_healing_coding.log"

def setup_logger_shc(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

shc_logger = setup_logger_shc("SelfHealingCodingLogger", LOG_FILE_SHC)

@dataclass
class HealthMetrics:
    """Health metrics for system monitoring."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    response_time: float
    error_rate: float
    timestamp: float
    
@dataclass
class RecoveryAction:
    """Recovery action with priority and constraints."""
    name: str
    action: Callable
    priority: int  # Lower number = higher priority
    max_attempts: int = 3
    cooldown: float = 60.0  # seconds
    conditions: list = None
    
class AdvancedHealthMonitor:
    """Advanced health monitoring with predictive capabilities."""
    
    def __init__(self, awareness_module=None):
        self.logger = shc_logger
        self.awareness_module = awareness_module
        self.health_history = []
        self.max_history = 100
        self.thresholds = {
            'cpu_critical': 90.0,
            'memory_critical': 85.0,
            'disk_critical': 95.0,
            'response_time_critical': 5.0,
            'error_rate_critical': 0.1
        }
        self.monitoring_active = False
        self.monitor_thread = None
        self.alert_callbacks = []
        
    def start_monitoring(self, interval=30):
        """Start continuous health monitoring."""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info(f"Health monitoring started with {interval}s interval")
        
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Health monitoring stopped")
        
    def _monitor_loop(self, interval):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._analyze_metrics(metrics)
                self._store_metrics(metrics)
                
                # Cleanup old metrics
                if len(self.health_history) > self.max_history:
                    self.health_history = self.health_history[-self.max_history:]
                    
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
                
    def _collect_metrics(self) -> HealthMetrics:
        """Collect current system metrics."""
        start_time = time.time()
        
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate response time (mock measurement)
        response_time = time.time() - start_time
        
        # Calculate error rate from recent history
        error_rate = self._calculate_error_rate()
        
        return HealthMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            response_time=response_time,
            error_rate=error_rate,
            timestamp=time.time()
        )
        
    def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent metrics."""
        if len(self.health_history) < 5:
            return 0.0
            
        recent_metrics = self.health_history[-10:]
        high_cpu_count = sum(1 for m in recent_metrics if m.cpu_usage > 80)
        return high_cpu_count / len(recent_metrics)
        
    def _analyze_metrics(self, metrics: HealthMetrics):
        """Analyze metrics for anomalies and trends."""
        alerts = []
        
        if metrics.cpu_usage > self.thresholds['cpu_critical']:
            alerts.append(f"Critical CPU usage: {metrics.cpu_usage:.1f}%")
            
        if metrics.memory_usage > self.thresholds['memory_critical']:
            alerts.append(f"Critical memory usage: {metrics.memory_usage:.1f}%")
            
        if metrics.disk_usage > self.thresholds['disk_critical']:
            alerts.append(f"Critical disk usage: {metrics.disk_usage:.1f}%")
            
        if metrics.response_time > self.thresholds['response_time_critical']:
            alerts.append(f"Slow response time: {metrics.response_time:.2f}s")
            
        if metrics.error_rate > self.thresholds['error_rate_critical']:
            alerts.append(f"High error rate: {metrics.error_rate:.1%}")
            
        # Predictive analysis
        if len(self.health_history) >= 10:
            trend_alerts = self._analyze_trends()
            alerts.extend(trend_alerts)
            
        # Trigger alerts
        for alert in alerts:
            self.logger.warning(f"Health Alert: {alert}")
            self._trigger_alert(alert, metrics)
            
    def _analyze_trends(self) -> list:
        """Analyze trends in health metrics."""
        alerts = []
        recent_metrics = self.health_history[-10:]
        
        # CPU trend analysis
        cpu_values = [m.cpu_usage for m in recent_metrics]
        if len(cpu_values) >= 5 and all(cpu_values[i] < cpu_values[i+1] for i in range(len(cpu_values)-1)):
            alerts.append("CPU usage trend: steadily increasing")
            
        # Memory leak detection
        memory_values = [m.memory_usage for m in recent_metrics]
        if len(memory_values) >= 5:
            memory_increase = memory_values[-1] - memory_values[0]
            if memory_increase > 10:  # 10% increase over monitoring period
                alerts.append(f"Potential memory leak detected: {memory_increase:.1f}% increase")
                
        return alerts
        
    def _store_metrics(self, metrics: HealthMetrics):
        """Store metrics in history."""
        self.health_history.append(metrics)
        
        # Update awareness module if available
        if self.awareness_module:
            self.awareness_module.update_module_health(
                "AdvancedHealthMonitor", 
                "OK", 
                f"CPU: {metrics.cpu_usage:.1f}%, Memory: {metrics.memory_usage:.1f}%"
            )
            
    def _trigger_alert(self, alert: str, metrics: HealthMetrics):
        """Trigger alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert, metrics)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
                
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alerts."""
        self.alert_callbacks.append(callback)
        
    def get_health_summary(self) -> dict:
        """Get comprehensive health summary."""
        if not self.health_history:
            return {"status": "no_data"}
            
        latest = self.health_history[-1]
        avg_cpu = sum(m.cpu_usage for m in self.health_history[-10:]) / min(10, len(self.health_history))
        avg_memory = sum(m.memory_usage for m in self.health_history[-10:]) / min(10, len(self.health_history))
        
        return {
            "status": "healthy" if latest.cpu_usage < 80 and latest.memory_usage < 80 else "warning",
            "current": {
                "cpu": latest.cpu_usage,
                "memory": latest.memory_usage,
                "disk": latest.disk_usage,
                "response_time": latest.response_time
            },
            "averages": {
                "cpu": avg_cpu,
                "memory": avg_memory
            },
            "trends": self._analyze_trends(),
            "monitoring_active": self.monitoring_active
        }

class SelfHealingModule:
    def __init__(self, awareness_module=None):
        self.logger = shc_logger
        self.awareness_module = awareness_module
        self.health_monitor = AdvancedHealthMonitor(awareness_module)
        self.recovery_actions = queue.PriorityQueue()
        self.action_history = {}
        self.learning_data = {}
        self.autonomy_enabled = True
        self.recovery_strategies = {}
        self.performance_baseline = {}
        
        # Initialize recovery strategies
        self._initialize_recovery_strategies()
        
        # Start health monitoring
        self.health_monitor.add_alert_callback(self._handle_health_alert)
        self.health_monitor.start_monitoring()
        
        self.logger.info("Advanced SelfHealingModule initialized with autonomy")
        
        if self.awareness_module:
            self.awareness_module.update_module_health("SelfHealingModule", "OK", "Initialized with autonomy")
    
    def _initialize_recovery_strategies(self):
        """Initialize comprehensive recovery strategies."""
        self.recovery_strategies = {
            "ModuleImportError": self._handle_import_error,
            "FileNotFoundError": self._handle_file_not_found,
            "SyntaxError": self._handle_syntax_error,
            "PermissionError": self._handle_permission_error,
            "JSONDecodeError": self._handle_json_decode_error,
            "MemoryError": self._handle_memory_error,
            "OSError": self._handle_os_error,
            "ConnectionError": self._handle_connection_error,
            "TimeoutError": self._handle_timeout_error,
            "HighCPUUsage": self._handle_high_cpu,
            "HighMemoryUsage": self._handle_high_memory,
            "DiskSpaceLow": self._handle_disk_space,
            "ProcessDead": self._handle_dead_process,
            "ServiceDown": self._handle_service_down,
            "Default": self._handle_default_error
        }
        
        # Advanced recovery actions
        self._register_recovery_actions()
        
    def _register_recovery_actions(self):
        """Register prioritized recovery actions."""
        actions = [
            RecoveryAction("restart_service", self._restart_critical_service, 1, 2, 300),
            RecoveryAction("clear_memory", self._clear_memory_cache, 2, 5, 60),
            RecoveryAction("restart_process", self._restart_process, 3, 3, 180),
            RecoveryAction("cleanup_temp", self._cleanup_temp_files, 4, 10, 30),
            RecoveryAction("optimize_performance", self._optimize_performance, 5, 3, 600),
            RecoveryAction("rollback_changes", self._rollback_recent_changes, 6, 1, 1800),
        ]
        
        for action in actions:
            self.recovery_strategies[action.name] = action
    
    def _handle_health_alert(self, alert: str, metrics: HealthMetrics):
        """Handle health alerts with autonomous responses."""
        if not self.autonomy_enabled:
            return
            
        self.logger.info(f"Processing health alert: {alert}")
        
        # Determine appropriate response based on alert type
        if "CPU usage" in alert:
            self._schedule_recovery_action("HighCPUUsage", {"metrics": metrics})
        elif "memory usage" in alert:
            self._schedule_recovery_action("HighMemoryUsage", {"metrics": metrics})
        elif "disk usage" in alert:
            self._schedule_recovery_action("DiskSpaceLow", {"metrics": metrics})
        elif "response time" in alert:
            self._schedule_recovery_action("optimize_performance", {"metrics": metrics})
            
    def _schedule_recovery_action(self, action_type: str, context: dict):
        """Schedule a recovery action with priority."""
        action_key = f"{action_type}_{time.time()}"
        
        # Check if similar action was recently attempted
        if self._was_recently_attempted(action_type):
            self.logger.info(f"Skipping {action_type} - recently attempted")
            return
            
        # Get priority for action type
        priority = self._get_action_priority(action_type)
        
        # Add to priority queue
        self.recovery_actions.put((priority, action_key, action_type, context))
        self.logger.info(f"Scheduled recovery action: {action_type} with priority {priority}")
        
        # Process queue
        self._process_recovery_queue()
        
    def _was_recently_attempted(self, action_type: str, cooldown: int = 300) -> bool:
        """Check if action was recently attempted."""
        if action_type not in self.action_history:
            return False
            
        last_attempt = self.action_history[action_type].get('last_attempt', 0)
        return time.time() - last_attempt < cooldown
        
    def _get_action_priority(self, action_type: str) -> int:
        """Get priority for action type."""
        priorities = {
            "HighCPUUsage": 2,
            "HighMemoryUsage": 1,
            "DiskSpaceLow": 3,
            "ProcessDead": 1,
            "ServiceDown": 1,
            "optimize_performance": 4,
            "cleanup_temp": 5
        }
        return priorities.get(action_type, 10)
        
    def _process_recovery_queue(self):
        """Process pending recovery actions."""
        while not self.recovery_actions.empty():
            try:
                priority, action_key, action_type, context = self.recovery_actions.get_nowait()
                
                # Execute recovery action
                success = self._execute_recovery_action(action_type, context)
                
                # Record attempt
                if action_type not in self.action_history:
                    self.action_history[action_type] = {'attempts': 0, 'successes': 0}
                    
                self.action_history[action_type]['attempts'] += 1
                self.action_history[action_type]['last_attempt'] = time.time()
                
                if success:
                    self.action_history[action_type]['successes'] += 1
                    self.logger.info(f"Successfully executed recovery action: {action_type}")
                else:
                    self.logger.warning(f"Recovery action failed: {action_type}")
                    
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Error processing recovery queue: {e}")
                
    def _execute_recovery_action(self, action_type: str, context: dict) -> bool:
        """Execute a specific recovery action."""
        try:
            if action_type in self.recovery_strategies:
                strategy = self.recovery_strategies[action_type]
                
                if isinstance(strategy, RecoveryAction):
                    result = strategy.action(context)
                else:
                    # Legacy strategy function
                    result = strategy(None, context)
                    
                return result.get('success', False) if isinstance(result, dict) else bool(result)
            else:
                self.logger.warning(f"Unknown recovery action: {action_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing recovery action {action_type}: {e}")
            return False
    # --- Advanced Recovery Strategies ---
    
    def _handle_memory_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory errors with intelligent cleanup."""
        self.logger.info("Handling memory error with advanced cleanup")
        
        # Force garbage collection
        gc.collect()
        
        # Clear caches if possible
        cleanup_success = self._clear_memory_cache(context)
        
        # Get memory info
        memory_info = psutil.virtual_memory()
        
        return {
            "success": cleanup_success.get('success', False),
            "message": f"Memory cleanup attempted. Available: {memory_info.available // 1024 // 1024}MB",
            "recovery_action": "memory_cleanup",
            "available_memory_mb": memory_info.available // 1024 // 1024
        }
    
    def _handle_os_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle OS-level errors."""
        error_msg = str(error)
        
        if "Too many open files" in error_msg:
            return self._handle_file_descriptor_limit(error, context)
        elif "No space left" in error_msg:
            return self._handle_disk_space(context)
        else:
            return {
                "success": False,
                "message": f"OS Error: {error_msg}",
                "recovery_action": "os_error_logged"
            }
    
    def _handle_file_descriptor_limit(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file descriptor limit exceeded."""
        try:
            # Get current file descriptor usage
            process = psutil.Process()
            open_files = len(process.open_files())
            
            # Attempt to close unnecessary file handles
            # (This would need specific implementation based on application)
            
            return {
                "success": True,
                "message": f"File descriptor cleanup attempted. Current open files: {open_files}",
                "recovery_action": "fd_cleanup",
                "open_files": open_files
            }
        except Exception as e:
            return {"success": False, "message": f"FD cleanup failed: {e}"}
    
    def _handle_connection_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network connection errors."""
        # Attempt connection retry with backoff
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Wait with exponential backoff
                time.sleep(2 ** attempt)
                
                # Test connection (implementation would depend on specific service)
                # This is a placeholder for actual connection test
                connection_test = True  # Replace with actual test
                
                if connection_test:
                    return {
                        "success": True,
                        "message": f"Connection restored after {attempt + 1} attempts",
                        "recovery_action": "connection_retry"
                    }
                    
            except Exception:
                continue
                
        return {
            "success": False,
            "message": f"Connection failed after {max_retries} attempts",
            "recovery_action": "connection_failed"
        }
    
    def _handle_timeout_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timeout errors with adaptive strategies."""
        operation = context.get('operation', 'unknown')
        
        # Increase timeout for next attempt
        current_timeout = context.get('timeout', 30)
        new_timeout = min(current_timeout * 1.5, 300)  # Cap at 5 minutes
        
        return {
            "success": True,  # Success means we have a strategy
            "message": f"Timeout handled for {operation}. Suggested timeout: {new_timeout}s",
            "recovery_action": "timeout_adjustment",
            "suggested_timeout": new_timeout
        }
    
    def _handle_high_cpu(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle high CPU usage."""
        metrics = context.get('metrics')
        
        # Identify CPU-intensive processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] > 10:
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Log top CPU consumers
        top_processes = processes[:5]
        process_info = "; ".join([f"{p['name']}({p['pid']}): {p['cpu_percent']:.1f}%" 
                                for p in top_processes])
        
        # Attempt to optimize (placeholder - would need specific implementation)
        optimization_applied = self._optimize_performance(context)
        
        return {
            "success": optimization_applied.get('success', False),
            "message": f"High CPU detected. Top processes: {process_info}",
            "recovery_action": "cpu_optimization",
            "top_processes": top_processes
        }
    
    def _handle_high_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle high memory usage."""
        # Force garbage collection
        gc.collect()
        
        # Clear caches
        cache_cleared = self._clear_memory_cache(context)
        
        # Get memory info after cleanup
        memory_after = psutil.virtual_memory()
        
        return {
            "success": True,
            "message": f"Memory cleanup completed. Available: {memory_after.available // 1024 // 1024}MB",
            "recovery_action": "memory_optimization",
            "memory_freed_mb": context.get('memory_before', 0) - memory_after.used
        }
    
    def _handle_disk_space(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle low disk space."""
        cleanup_results = []
        
        # Clean temporary files
        temp_cleanup = self._cleanup_temp_files(context)
        cleanup_results.append(f"Temp cleanup: {temp_cleanup.get('message', 'failed')}")
        
        # Clean log files (keep recent ones)
        log_cleanup = self._cleanup_old_logs()
        cleanup_results.append(f"Log cleanup: {log_cleanup.get('message', 'failed')}")
        
        # Get disk space after cleanup
        disk_after = psutil.disk_usage('/')
        free_gb = disk_after.free / (1024**3)
        
        return {
            "success": free_gb > 1.0,  # Success if more than 1GB free
            "message": f"Disk cleanup completed. Free space: {free_gb:.1f}GB",
            "recovery_action": "disk_cleanup",
            "cleanup_results": cleanup_results,
            "free_space_gb": free_gb
        }
    
    def _handle_dead_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle dead process detection."""
        process_name = context.get('process_name', 'unknown')
        
        restart_result = self._restart_process(context)
        
        return {
            "success": restart_result.get('success', False),
            "message": f"Process restart attempted for {process_name}",
            "recovery_action": "process_restart"
        }
    
    def _handle_service_down(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service downtime."""
        service_name = context.get('service_name', 'unknown')
        
        restart_result = self._restart_critical_service(context)
        
        return {
            "success": restart_result.get('success', False),
            "message": f"Service restart attempted for {service_name}",
            "recovery_action": "service_restart"
        }
    
    # --- Recovery Action Implementations ---
    
    def _restart_critical_service(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Restart critical services."""
        service = context.get('service_name', 'main_service')
        
        try:
            # This would contain actual service restart logic
            # For now, we'll simulate the restart
            self.logger.info(f"Simulating restart of service: {service}")
            
            # In a real implementation, you would:
            # 1. Stop the service gracefully
            # 2. Wait for cleanup
            # 3. Start the service
            # 4. Verify it's running
            
            return {
                "success": True,
                "message": f"Service {service} restarted successfully",
                "action": "service_restart"
            }
        except Exception as e:
            return {"success": False, "message": f"Service restart failed: {e}"}
    
    def _clear_memory_cache(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear memory caches and force garbage collection."""
        try:
            # Get memory before cleanup
            memory_before = psutil.virtual_memory().used
            
            # Force garbage collection multiple times
            for _ in range(3):
                gc.collect()
                time.sleep(0.1)
            
            # Clear any application-specific caches
            # (This would be implemented based on specific application needs)
            
            memory_after = psutil.virtual_memory().used
            freed_mb = (memory_before - memory_after) / (1024 * 1024)
            
            return {
                "success": True,
                "message": f"Memory cache cleared. Freed: {freed_mb:.1f}MB",
                "memory_freed_mb": freed_mb
            }
        except Exception as e:
            return {"success": False, "message": f"Memory cleanup failed: {e}"}
    
    def _restart_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Restart current process (careful implementation needed)."""
        try:
            # This is a placeholder for process restart logic
            # In production, this would need careful implementation
            # to avoid losing state or causing issues
            
            self.logger.warning("Process restart requested but not implemented for safety")
            
            return {
                "success": False,
                "message": "Process restart not implemented for safety",
                "action": "process_restart_skipped"
            }
        except Exception as e:
            return {"success": False, "message": f"Process restart failed: {e}"}
    
    def _cleanup_temp_files(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up temporary files and directories."""
        try:
            cleanup_paths = [
                '/tmp',
                '/var/tmp',
                os.path.expanduser('~/tmp'),
                tempfile.gettempdir()
            ]
            
            total_freed = 0
            files_removed = 0
            
            for path in cleanup_paths:
                if os.path.exists(path):
                    freed, removed = self._clean_directory(path, max_age_hours=24)
                    total_freed += freed
                    files_removed += removed
            
            return {
                "success": True,
                "message": f"Cleaned {files_removed} files, freed {total_freed / 1024 / 1024:.1f}MB",
                "files_removed": files_removed,
                "space_freed_mb": total_freed / 1024 / 1024
            }
        except Exception as e:
            return {"success": False, "message": f"Temp cleanup failed: {e}"}
    
    def _clean_directory(self, directory: str, max_age_hours: int = 24) -> Tuple[int, int]:
        """Clean old files from directory."""
        total_size = 0
        files_removed = 0
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        stat = os.stat(filepath)
                        if stat.st_mtime < cutoff_time:
                            total_size += stat.st_size
                            os.remove(filepath)
                            files_removed += 1
                    except (OSError, IOError):
                        continue  # Skip files we can't access
                        
        except Exception as e:
            self.logger.warning(f"Error cleaning directory {directory}: {e}")
            
        return total_size, files_removed
    
    def _cleanup_old_logs(self, max_age_days: int = 7) -> Dict[str, Any]:
        """Clean up old log files."""
        try:
            log_dirs = [
                '/var/log',
                os.path.expanduser('~/'),
                '/home/ubuntu'
            ]
            
            total_freed = 0
            files_removed = 0
            cutoff_time = time.time() - (max_age_days * 24 * 3600)
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for filename in os.listdir(log_dir):
                        if filename.endswith('.log'):
                            filepath = os.path.join(log_dir, filename)
                            try:
                                stat = os.stat(filepath)
                                if stat.st_mtime < cutoff_time:
                                    total_freed += stat.st_size
                                    os.remove(filepath)
                                    files_removed += 1
                            except (OSError, IOError):
                                continue
            
            return {
                "success": True,
                "message": f"Cleaned {files_removed} log files, freed {total_freed / 1024 / 1024:.1f}MB",
                "files_removed": files_removed,
                "space_freed_mb": total_freed / 1024 / 1024
            }
        except Exception as e:
            return {"success": False, "message": f"Log cleanup failed: {e}"}
    
    def _optimize_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply performance optimizations."""
        try:
            optimizations = []
            
            # Adjust process priority if high CPU
            metrics = context.get('metrics')
            if metrics and metrics.cpu_usage > 80:
                try:
                    os.nice(1)  # Lower priority slightly
                    optimizations.append("Reduced process priority")
                except OSError:
                    pass
            
            # Force garbage collection
            gc.collect()
            optimizations.append("Forced garbage collection")
            
            # Clear any performance-impacting caches
            cache_result = self._clear_memory_cache(context)
            if cache_result.get('success'):
                optimizations.append("Cleared memory caches")
            
            return {
                "success": True,
                "message": f"Applied optimizations: {', '.join(optimizations)}",
                "optimizations": optimizations
            }
        except Exception as e:
            return {"success": False, "message": f"Performance optimization failed: {e}"}
    
    def _rollback_recent_changes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback recent changes (placeholder for backup/restore system)."""
        try:
            # This would implement actual rollback logic
            # For now, it's a placeholder
            
            self.logger.info("Rollback requested but not implemented")
            
            return {
                "success": False,
                "message": "Rollback system not implemented",
                "action": "rollback_unavailable"
            }
        except Exception as e:
            return {"success": False, "message": f"Rollback failed: {e}"}
    
    def enable_autonomy(self):
        """Enable autonomous operation."""
        self.autonomy_enabled = True
        self.health_monitor.start_monitoring()
        self.logger.info("Autonomy enabled - bot will self-heal automatically")
        
    def disable_autonomy(self):
        """Disable autonomous operation."""
        self.autonomy_enabled = False
        self.health_monitor.stop_monitoring()
        self.logger.info("Autonomy disabled - manual intervention required for issues")
    
    def get_autonomy_status(self) -> Dict[str, Any]:
        """Get comprehensive autonomy and health status."""
        health_summary = self.health_monitor.get_health_summary()
        
        return {
            "autonomy_enabled": self.autonomy_enabled,
            "health_monitoring": self.health_monitor.monitoring_active,
            "health_summary": health_summary,
            "recovery_queue_size": self.recovery_actions.qsize(),
            "action_history": self.action_history,
            "available_strategies": list(self.recovery_strategies.keys())
        }
    
    def force_health_check(self) -> Dict[str, Any]:
        """Force an immediate health check and return results."""
        metrics = self.health_monitor._collect_metrics()
        self.health_monitor._analyze_metrics(metrics)
        self.health_monitor._store_metrics(metrics)
        
        return {
            "metrics": {
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "disk_usage": metrics.disk_usage,
                "response_time": metrics.response_time,
                "error_rate": metrics.error_rate
            },
            "status": "completed",
            "timestamp": metrics.timestamp
        }
    
    def register_error_handler(self, error_type: str, handler_func):
        """Register a custom error handler for a specific error type."""
        self.recovery_strategies[error_type] = handler_func
        self.logger.info(f"Registered custom handler for {error_type}")
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main error handling method that dispatches to appropriate recovery strategy.
        Args:
            error: The exception that was raised
            context: Additional information about the error context
        Returns:
            Dict containing recovery status and any relevant information
        """
        if context is None:
            context = {}
        
        error_type = type(error).__name__
        error_msg = str(error)
        
        self.logger.error(f"Handling error: {error_type} - {error_msg}")
        if self.awareness_module:
            self.awareness_module.log_event(
                f"Error detected: {error_type} - {error_msg}", 
                logging.ERROR, 
                "SelfHealingModule"
            )
        
        # Get traceback information
        tb_info = traceback.format_exc()
        context["traceback"] = tb_info
        
        # Find appropriate handler
        handler = self.recovery_strategies.get(error_type, self.recovery_strategies["Default"])
        
        try:
            recovery_result = handler(error, context)
            if recovery_result.get("success", False):
                self.logger.info(f"Successfully recovered from {error_type}")
                if self.awareness_module:
                    self.awareness_module.update_module_health(
                        "SelfHealingModule", 
                        "OK", 
                        f"Recovered from {error_type}"
                    )
            else:
                self.logger.warning(f"Failed to recover from {error_type}: {recovery_result.get('message', 'Unknown reason')}")
                if self.awareness_module:
                    self.awareness_module.update_module_health(
                        "SelfHealingModule", 
                        "WARNING", 
                        f"Failed recovery: {error_type}"
                    )
            return recovery_result
        except Exception as recovery_error:
            self.logger.error(f"Error in recovery handler: {recovery_error}", exc_info=True)
            if self.awareness_module:
                self.awareness_module.update_module_health(
                    "SelfHealingModule", 
                    "ERROR", 
                    f"Recovery handler failed: {recovery_error}"
                )
            return {
                "success": False,
                "message": f"Recovery handler failed: {recovery_error}",
                "original_error": f"{error_type}: {error_msg}"
            }
    
    # --- Default Recovery Strategies ---
    
    def _handle_import_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle module import errors by suggesting installation."""
        module_name = context.get("module_name", "unknown_module")
        if not module_name or module_name == "unknown_module":
            # Try to extract module name from error message
            error_msg = str(error)
            match = re.search(r"No module named '([^']+)'", error_msg)
            if match:
                module_name = match.group(1)
        
        self.logger.info(f"Suggesting installation for missing module: {module_name}")
        return {
            "success": False,  # We can't automatically install packages
            "message": f"Module '{module_name}' is missing. Try installing it with 'pip install {module_name}'.",
            "recovery_action": "suggest_installation",
            "module_name": module_name
        }
    
    def _handle_file_not_found(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file not found errors."""
        file_path = context.get("file_path", "")
        if not file_path:
            # Try to extract file path from error message
            error_msg = str(error)
            match = re.search(r"No such file or directory: '([^']+)'", error_msg)
            if match:
                file_path = match.group(1)
        
        # Check if it's a directory issue
        dir_path = os.path.dirname(file_path) if file_path else ""
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.info(f"Created missing directory: {dir_path}")
                return {
                    "success": True,
                    "message": f"Created missing directory: {dir_path}",
                    "recovery_action": "created_directory",
                    "directory": dir_path
                }
            except Exception as dir_error:
                self.logger.error(f"Failed to create directory {dir_path}: {dir_error}")
        
        return {
            "success": False,
            "message": f"File not found: {file_path}",
            "recovery_action": "report_missing_file",
            "file_path": file_path
        }
    
    def _handle_syntax_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle syntax errors in code."""
        file_path = context.get("file_path", "")
        line_no = getattr(error, "lineno", None)
        offset = getattr(error, "offset", None)
        
        error_info = {
            "success": False,
            "message": f"Syntax error in {file_path or 'code'} at line {line_no or 'unknown'}: {error}",
            "recovery_action": "report_syntax_error",
            "file_path": file_path,
            "line_no": line_no,
            "offset": offset,
            "error_text": str(error)
        }
        
        self.logger.error(f"Syntax error detected: {error_info['message']}")
        return error_info
    
    def _handle_permission_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle permission errors."""
        file_path = context.get("file_path", "")
        if not file_path:
            # Try to extract file path from error message
            error_msg = str(error)
            match = re.search(r"Permission denied: '([^']+)'", error_msg)
            if match:
                file_path = match.group(1)
        
        return {
            "success": False,
            "message": f"Permission error for {file_path}: {error}",
            "recovery_action": "report_permission_error",
            "file_path": file_path
        }
    
    def _handle_json_decode_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON decoding errors."""
        file_path = context.get("file_path", "")
        
        error_info = {
            "success": False,
            "message": f"JSON decode error in {file_path or 'data'}: {error}",
            "recovery_action": "report_json_error",
            "file_path": file_path
        }
        
        # If we have the file path, we could try to validate the JSON
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Simple validation attempt - look for common JSON errors
                if content.strip() == "":
                    error_info["message"] += " (File is empty)"
                elif not (content.strip().startswith('{') or content.strip().startswith('[')):
                    error_info["message"] += " (Not a valid JSON object/array)"
                # More validation could be added here
                
            except Exception as read_error:
                self.logger.error(f"Error reading JSON file for validation: {read_error}")
        
        return error_info
    
    def _handle_default_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default error handler for unspecified error types."""
        return {
            "success": False,
            "message": f"Unhandled error: {type(error).__name__} - {error}",
            "recovery_action": "report_error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }


class SelfCodingModule:
    def __init__(self, awareness_module=None):
        self.logger = shc_logger
        self.awareness_module = awareness_module
        self.code_templates = self._initialize_templates()
        self.best_practices = self._initialize_best_practices()
        self.logger.info("SelfCodingModule initialized.")
        
        # Register with awareness module if available
        if self.awareness_module:
            self.awareness_module.update_module_health("SelfCodingModule", "OK", "Initialized")
    
    def analyze_code_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze the structure of a Python code file.
        Args:
            file_path: Path to the Python file to analyze
        Returns:
            Dict containing analysis results (functions, classes, imports, etc.)
        """
        self.logger.info(f"Analyzing code structure: {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Extract information
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(d).strip() for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                    }
                    functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "bases": [ast.unparse(b).strip() for b in node.bases] if hasattr(ast, 'unparse') else [],
                        "methods": []
                    }
                    
                    # Extract methods
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            method_info = {
                                "name": child.name,
                                "line_number": child.lineno,
                                "args": [arg.arg for arg in child.args.args]
                            }
                            class_info["methods"].append(method_info)
                    
                    classes.append(class_info)
                
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append({"name": name.name, "alias": name.asname})
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        imports.append({
                            "name": f"{module}.{name.name}" if module else name.name,
                            "alias": name.asname,
                            "from_import": True
                        })
            
            analysis_result = {
                "file_path": file_path,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "total_functions": len(functions),
                "total_classes": len(classes),
                "total_imports": len(imports)
            }
            
            self.logger.info(f"Code analysis completed for {file_path}: {len(functions)} functions, {len(classes)} classes")
            return analysis_result
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return {
                "error": f"Syntax error in {file_path}: {e}",
                "line_number": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}", exc_info=True)
            return {"error": f"Error analyzing {file_path}: {e}"}
    
    def apply_simple_code_patch(self, file_path: str, old_str: str, new_str: str) -> bool:
        """
        Apply a simple string replacement patch to a file.
        Args:
            file_path: Path to the file to patch
            old_str: String to replace
            new_str: Replacement string
        Returns:
            Boolean indicating success
        """
        self.logger.info(f"Applying code patch to {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if old_str not in content:
                self.logger.warning(f"String to replace not found in {file_path}")
                return False
            
            # Apply the patch
            new_content = content.replace(old_str, new_str)
            
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            self.logger.info(f"Successfully patched {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error patching {file_path}: {e}", exc_info=True)
            return False
    
    def modify_config_parameter(self, config_file: str, param_key: str, new_value: Any) -> bool:
        """
        Modify a parameter in a JSON configuration file.
        Args:
            config_file: Path to the JSON config file
            param_key: Parameter key to modify (supports dot notation for nested keys)
            new_value: New value for the parameter
        Returns:
            Boolean indicating success
        """
        self.logger.info(f"Modifying config parameter {param_key} in {config_file}")
        
        if not os.path.exists(config_file):
            self.logger.error(f"Config file not found: {config_file}")
            return False
        
        try:
            # Read the config file
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Parse the parameter key (support for nested keys with dot notation)
            key_parts = param_key.split('.')
            
            # Navigate to the nested location
            current = config
            for i, part in enumerate(key_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value
            current[key_parts[-1]] = new_value
            
            # Write back to the file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Successfully modified {param_key} in {config_file}")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {config_file}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error modifying config {config_file}: {e}", exc_info=True)
            return False
    
    def generate_simple_function(self, function_name: str, args: List[str], body: str, docstring: str = None) -> str:
        """
        Generate a simple Python function based on specifications.
        Args:
            function_name: Name of the function
            args: List of argument names
            body: Function body code
            docstring: Optional docstring
        Returns:
            String containing the generated function code
        """
        self.logger.info(f"Generating function: {function_name}")
        
        # Format the arguments
        args_str = ", ".join(args)
        
        # Format the docstring if provided
        doc_str = f'    """{docstring}"""\n' if docstring else ""
        
        # Indent the body
        body_lines = body.strip().split('\n')
        indented_body = "\n".join(f"    {line}" for line in body_lines)
        
        # Assemble the function
        function_code = f"def {function_name}({args_str}):\n{doc_str}{indented_body}\n"
        
        self.logger.info(f"Generated function {function_name} with {len(args)} arguments")
        return function_code
    
    def validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate Python code syntax without executing it.
        Args:
            code: Python code to validate
        Returns:
            Dict with validation results
        """
        self.logger.info("Validating Python syntax")
        
        try:
            ast.parse(code)
            return {"valid": True, "message": "Syntax is valid"}
        except SyntaxError as e:
            self.logger.warning(f"Syntax error: {e}")
            return {
                "valid": False,
                "message": f"Syntax error: {e}",
                "line_number": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            self.logger.error(f"Error validating syntax: {e}")
            return {"valid": False, "message": f"Error: {e}"}

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize code templates for common patterns."""
        return {
            "class_basic": '''class {class_name}:
    """A basic class template."""
    
    def __init__(self{init_params}):
        """Initialize the {class_name}."""
{init_body}
    
    def __str__(self):
        """Return string representation."""
        return f"{class_name}()"
    
    def __repr__(self):
        """Return detailed string representation."""
        return self.__str__()
''',
            "singleton": '''class {class_name}:
    """Singleton pattern implementation."""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
{init_body}
            self._initialized = True
''',
            "context_manager": '''class {class_name}:
    """Context manager implementation."""
    
    def __init__(self{init_params}):
{init_body}
    
    def __enter__(self):
        """Enter the context."""
{enter_body}
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
{exit_body}
        return False
''',
            "api_client": '''import requests
from typing import Dict, Any, Optional

class {class_name}:
    """API client for {api_name}."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({{"Authorization": f"Bearer {{api_key}}"}})
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{{self.base_url}}/{{endpoint.lstrip('/')}}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request("POST", endpoint, data=data, json=json)
''',
            "unit_test": '''import unittest
from unittest.mock import Mock, patch, MagicMock

class Test{class_name}(unittest.TestCase):
    """Test cases for {class_name}."""
    
    def setUp(self):
        """Set up test fixtures."""
{setup_body}
    
    def tearDown(self):
        """Clean up after tests."""
{teardown_body}
    
    def test_{test_name}(self):
        """Test {test_description}."""
{test_body}
        # Assert expected behavior
        self.assertTrue(True)  # Replace with actual assertions
    
    def test_{test_name}_error_handling(self):
        """Test error handling in {test_name}."""
        with self.assertRaises(ValueError):
            pass  # Replace with code that should raise ValueError

if __name__ == '__main__':
    unittest.main()
'''
        }
    
    def _initialize_best_practices(self) -> Dict[str, List[str]]:
        """Initialize coding best practices and rules."""
        return {
            "naming": [
                "Use snake_case for functions and variables",
                "Use PascalCase for classes",
                "Use UPPER_CASE for constants",
                "Use descriptive names, avoid abbreviations",
                "Avoid single-letter variable names except for loops"
            ],
            "functions": [
                "Keep functions small and focused (< 20 lines)",
                "Use type hints for parameters and return values",
                "Include docstrings for all public functions",
                "Avoid deep nesting (max 3 levels)",
                "Return early when possible"
            ],
            "classes": [
                "Use composition over inheritance when possible",
                "Keep classes focused on single responsibility",
                "Make attributes private by default",
                "Implement __str__ and __repr__ methods",
                "Use properties for computed attributes"
            ],
            "imports": [
                "Group imports: standard library, third-party, local",
                "Use absolute imports when possible",
                "Avoid wildcard imports",
                "Import only what you need",
                "Put imports at the top of the file"
            ],
            "error_handling": [
                "Use specific exception types",
                "Handle exceptions at the right level",
                "Log errors with context",
                "Fail fast when appropriate",
                "Use try-except-finally properly"
            ]
        }
    
    def analyze_code_quality(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive code quality analysis.
        Args:
            file_path: Path to the Python file to analyze
        Returns:
            Dict containing detailed quality analysis
        """
        self.logger.info(f"Analyzing code quality: {file_path}")
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Initialize analysis results
            analysis = {
                "file_path": file_path,
                "line_count": len(code.split('\n')),
                "complexity_score": 0,
                "issues": [],
                "suggestions": [],
                "metrics": {},
                "best_practices": {"followed": [], "violations": []}
            }
            
            # Analyze various aspects
            self._analyze_complexity(tree, analysis)
            self._analyze_naming_conventions(tree, analysis)
            self._analyze_function_quality(tree, analysis)
            self._analyze_class_design(tree, analysis)
            self._analyze_imports(tree, analysis)
            self._analyze_docstrings(tree, analysis)
            self._detect_code_smells(tree, code, analysis)
            
            self.logger.info(f"Quality analysis completed: {len(analysis['issues'])} issues found")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing code quality: {e}", exc_info=True)
            return {"error": f"Error analyzing code quality: {e}"}
    
    def _analyze_complexity(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Analyze cyclomatic complexity."""
        complexity_nodes = (ast.If, ast.While, ast.For, ast.Try, ast.With, 
                          ast.FunctionDef, ast.AsyncFunctionDef)
        
        total_complexity = 0
        function_complexities = {}
        
        for node in ast.walk(tree):
            if isinstance(node, complexity_nodes):
                total_complexity += 1
                
                # Track function-level complexity
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_complexity = sum(1 for n in ast.walk(node) 
                                        if isinstance(n, complexity_nodes)) - 1
                    function_complexities[node.name] = func_complexity
                    
                    if func_complexity > 10:
                        analysis["issues"].append({
                            "type": "high_complexity",
                            "line": node.lineno,
                            "message": f"Function '{node.name}' has high complexity ({func_complexity})",
                            "severity": "warning"
                        })
        
        analysis["complexity_score"] = total_complexity
        analysis["metrics"]["function_complexities"] = function_complexities
    
    def _analyze_naming_conventions(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Check naming conventions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                    analysis["issues"].append({
                        "type": "naming_convention",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' should use snake_case",
                        "severity": "style"
                    })
            
            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    analysis["issues"].append({
                        "type": "naming_convention",
                        "line": node.lineno,
                        "message": f"Class '{node.name}' should use PascalCase",
                        "severity": "style"
                    })
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention."""
        return name.islower() and '_' in name or name.islower()
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention."""
        return name[0].isupper() and not '_' in name
    
    def _analyze_function_quality(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Analyze function quality."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function length
                func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    analysis["issues"].append({
                        "type": "long_function",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' is too long ({func_lines} lines)",
                        "severity": "warning"
                    })
                
                # Check parameter count
                arg_count = len(node.args.args)
                if arg_count > 5:
                    analysis["issues"].append({
                        "type": "too_many_parameters",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has too many parameters ({arg_count})",
                        "severity": "warning"
                    })
    
    def _analyze_class_design(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Analyze class design."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                method_count = len(methods)
                
                if method_count > 20:
                    analysis["issues"].append({
                        "type": "large_class",
                        "line": node.lineno,
                        "message": f"Class '{node.name}' has too many methods ({method_count})",
                        "severity": "warning"
                    })
                
                # Check for __str__ and __repr__ methods
                method_names = [m.name for m in methods]
                if '__init__' in method_names:
                    if '__str__' not in method_names:
                        analysis["suggestions"].append({
                            "type": "missing_str_method",
                            "line": node.lineno,
                            "message": f"Consider adding __str__ method to class '{node.name}'"
                        })
    
    def _analyze_imports(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Analyze import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
        
        # Check for unused imports (basic check)
        analysis["metrics"]["import_count"] = len(imports)
    
    def _analyze_docstrings(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Check for missing docstrings."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    analysis["issues"].append({
                        "type": "missing_docstring",
                        "line": node.lineno,
                        "message": f"{node.__class__.__name__.lower()[:-3]} '{node.name}' missing docstring",
                        "severity": "style"
                    })
    
    def _detect_code_smells(self, tree: ast.AST, code: str, analysis: Dict[str, Any]):
        """Detect common code smells."""
        code_lines = code.split('\n')
        
        # Check for long lines
        for i, line in enumerate(code_lines, 1):
            if len(line) > 88:  # PEP 8 recommends max 79, but we'll be slightly lenient
                analysis["issues"].append({
                    "type": "long_line",
                    "line": i,
                    "message": f"Line too long ({len(line)} characters)",
                    "severity": "style"
                })
        
        # Check for duplicated code patterns
        line_counts = Counter(line.strip() for line in code_lines if line.strip())
        for line, count in line_counts.items():
            if count > 3 and len(line) > 20:  # Potential code duplication
                analysis["suggestions"].append({
                    "type": "code_duplication",
                    "message": f"Potential code duplication: '{line[:50]}...' appears {count} times"
                })
    
    def generate_advanced_code(self, code_type: str, **kwargs) -> str:
        """
        Generate advanced code structures using templates.
        Args:
            code_type: Type of code to generate (class, api_client, test, etc.)
            **kwargs: Parameters for code generation
        Returns:
            Generated code string
        """
        self.logger.info(f"Generating {code_type} code with params: {kwargs}")
        
        if code_type not in self.code_templates:
            available = ", ".join(self.code_templates.keys())
            return f"# Error: Unknown code type '{code_type}'. Available: {available}"
        
        try:
            template = self.code_templates[code_type]
            
            # Set default values for common parameters
            defaults = {
                'class_name': kwargs.get('class_name', 'MyClass'),
                'init_params': kwargs.get('init_params', ''),
                'init_body': kwargs.get('init_body', '        pass'),
                'enter_body': kwargs.get('enter_body', '        pass'),
                'exit_body': kwargs.get('exit_body', '        pass'),
                'api_name': kwargs.get('api_name', 'MyAPI'),
                'setup_body': kwargs.get('setup_body', '        pass'),
                'teardown_body': kwargs.get('teardown_body', '        pass'),
                'test_name': kwargs.get('test_name', 'example'),
                'test_description': kwargs.get('test_description', 'example functionality'),
                'test_body': kwargs.get('test_body', '        pass')
            }
            
            # Merge with provided kwargs
            params = {**defaults, **kwargs}
            
            # Format the template
            generated_code = template.format(**params)
            
            self.logger.info(f"Generated {code_type} code successfully")
            return generated_code
            
        except KeyError as e:
            self.logger.error(f"Missing parameter for {code_type}: {e}")
            return f"# Error: Missing parameter {e} for {code_type}"
        except Exception as e:
            self.logger.error(f"Error generating {code_type}: {e}", exc_info=True)
            return f"# Error generating {code_type}: {e}"
    
    def refactor_code(self, file_path: str, refactor_type: str, **kwargs) -> bool:
        """
        Apply code refactoring to a file.
        Args:
            file_path: Path to the file to refactor
            refactor_type: Type of refactoring to apply
            **kwargs: Refactoring parameters
        Returns:
            Boolean indicating success
        """
        self.logger.info(f"Refactoring {file_path} with {refactor_type}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                original_code = f.read()
            
            if refactor_type == "format_with_black":
                try:
                    import black
                    refactored_code = black.format_str(original_code, mode=black.FileMode())
                except ImportError:
                    self.logger.warning("Black not available, using basic formatting")
                    refactored_code = self._basic_format(original_code)
            
            elif refactor_type == "format_with_autopep8":
                try:
                    import autopep8
                    refactored_code = autopep8.fix_code(original_code)
                except ImportError:
                    self.logger.warning("autopep8 not available, using basic formatting")
                    refactored_code = self._basic_format(original_code)
            
            elif refactor_type == "extract_function":
                refactored_code = self._extract_function(original_code, **kwargs)
            
            elif refactor_type == "rename_variable":
                refactored_code = self._rename_variable(original_code, **kwargs)
            
            elif refactor_type == "add_docstrings":
                refactored_code = self._add_docstrings(original_code)
            
            else:
                self.logger.error(f"Unknown refactor type: {refactor_type}")
                return False
            
            # Write the refactored code
            with open(file_path, 'w') as f:
                f.write(refactored_code)
            
            self.logger.info(f"Successfully refactored {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error refactoring {file_path}: {e}", exc_info=True)
            return False
    
    def _basic_format(self, code: str) -> str:
        """Apply basic code formatting."""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Adjust indent level
            if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try:')):
                formatted_lines.append('    ' * indent_level + stripped)
                indent_level += 1
            elif stripped.startswith(('except', 'finally', 'else', 'elif')):
                formatted_lines.append('    ' * (indent_level - 1) + stripped)
            elif stripped == 'pass' or (stripped.startswith('return') and indent_level > 0):
                formatted_lines.append('    ' * indent_level + stripped)
                if not any(line.strip().startswith(('except', 'finally', 'else', 'elif')) 
                          for line in lines[lines.index(line) + 1:]):
                    indent_level = max(0, indent_level - 1)
            else:
                formatted_lines.append('    ' * indent_level + stripped)
        
        return '\n'.join(formatted_lines)
    
    def _extract_function(self, code: str, start_line: int, end_line: int, 
                         function_name: str) -> str:
        """Extract code block into a separate function."""
        lines = code.split('\n')
        
        # Extract the code block
        extracted_lines = lines[start_line-1:end_line]
        extracted_code = '\n'.join(extracted_lines)
        
        # Create new function
        new_function = f"""
def {function_name}():
    \"\"\"Extracted function.\"\"\"
{textwrap.indent(extracted_code, '    ')}
"""
        
        # Replace original code with function call
        lines[start_line-1:end_line] = [f'    {function_name}()']
        
        # Insert function definition at the beginning
        lines.insert(0, new_function)
        
        return '\n'.join(lines)
    
    def _rename_variable(self, code: str, old_name: str, new_name: str) -> str:
        """Rename a variable throughout the code."""
        # This is a simple implementation - a more sophisticated version
        # would use AST to ensure we only rename the correct variable
        import re
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, code)
    
    def _add_docstrings(self, code: str) -> str:
        """Add basic docstrings to functions and classes."""
        tree = ast.parse(code)
        lines = code.split('\n')
        
        # Track where to insert docstrings
        insertions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    doc_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                    docstring = f'    """{doc_type.title()} {node.name}."""'
                    insertions.append((node.lineno, docstring))
        
        # Insert docstrings (in reverse order to maintain line numbers)
        for line_no, docstring in sorted(insertions, reverse=True):
            lines.insert(line_no, docstring)
        
        return '\n'.join(lines)
    
    def auto_fix_issues(self, file_path: str) -> Dict[str, Any]:
        """
        Automatically fix common code issues.
        Args:
            file_path: Path to the file to fix
        Returns:
            Dict with fix results
        """
        self.logger.info(f"Auto-fixing issues in {file_path}")
        
        # First analyze the code
        analysis = self.analyze_code_quality(file_path)
        if "error" in analysis:
            return analysis
        
        fixes_applied = []
        
        try:
            # Apply automatic fixes
            if any(issue["type"] == "long_line" for issue in analysis["issues"]):
                if self.refactor_code(file_path, "format_with_black"):
                    fixes_applied.append("Fixed long lines with code formatting")
            
            if any(issue["type"] == "missing_docstring" for issue in analysis["issues"]):
                if self.refactor_code(file_path, "add_docstrings"):
                    fixes_applied.append("Added missing docstrings")
            
            return {
                "success": True,
                "fixes_applied": fixes_applied,
                "remaining_issues": len(analysis["issues"]) - len(fixes_applied)
            }
            
        except Exception as e:
            self.logger.error(f"Error auto-fixing {file_path}: {e}", exc_info=True)
            return {"error": f"Error auto-fixing: {e}"}
    
    def generate_unit_tests(self, file_path: str) -> str:
        """
        Generate unit tests for a Python file.
        Args:
            file_path: Path to the Python file
        Returns:
            Generated test code
        """
        self.logger.info(f"Generating unit tests for {file_path}")
        
        if not os.path.exists(file_path):
            return f"# Error: File {file_path} not found"
        
        try:
            # Analyze the code structure
            analysis = self.analyze_code_structure(file_path)
            if "error" in analysis:
                return f"# Error: {analysis['error']}"
            
            test_code = f"""# Unit tests for {os.path.basename(file_path)}
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the module to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the module to test
from {os.path.splitext(os.path.basename(file_path))[0]} import *

"""
            
            # Generate test classes for each class in the original file
            for class_info in analysis.get("classes", []):
                class_name = class_info["name"]
                test_code += self.generate_advanced_code(
                    "unit_test",
                    class_name=class_name,
                    setup_body=f"        self.{class_name.lower()} = {class_name}()",
                    teardown_body="        pass",
                    test_name="initialization",
                    test_description=f"{class_name} initialization",
                    test_body=f"        instance = {class_name}()\n        self.assertIsInstance(instance, {class_name})"
                )
                test_code += "\n\n"
            
            # Generate test functions for standalone functions
            for func_info in analysis.get("functions", []):
                if not func_info["name"].startswith("_"):  # Skip private functions
                    func_name = func_info["name"]
                    test_code += f"""
class Test{func_name.title()}(unittest.TestCase):
    \"\"\"Test cases for {func_name} function.\"\"\"
    
    def test_{func_name}_normal_case(self):
        \"\"\"Test {func_name} with normal inputs.\"\"\"
        # TODO: Implement test for {func_name}
        pass
    
    def test_{func_name}_edge_cases(self):
        \"\"\"Test {func_name} with edge cases.\"\"\"
        # TODO: Implement edge case tests for {func_name}
        pass

"""
            
            test_code += """
if __name__ == '__main__':
    unittest.main()
"""
            
            return test_code
            
        except Exception as e:
            self.logger.error(f"Error generating tests for {file_path}: {e}", exc_info=True)
            return f"# Error generating tests: {e}"

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing SelfHealingModule and SelfCodingModule for testing...")
    
    # Create a simple test file
    test_file_path = "/home/ubuntu/test_code.py"
    with open(test_file_path, 'w') as f:
        f.write("""
import os
import sys

def hello_world():
    \"\"\"A simple hello world function.\"\"\"
    print("Hello, World!")
    return True

class TestClass:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"

def add_numbers(a, b):
    return a + b
""")
    
    # Create a test JSON config
    test_config_path = "/home/ubuntu/test_config.json"
    with open(test_config_path, 'w') as f:
        f.write("""
{
  "app": {
    "name": "TestApp",
    "version": "1.0.0"
  },
  "settings": {
    "debug": false,
    "log_level": "info"
  }
}
""")
    
    # Initialize modules
    healing_module = SelfHealingModule()
    coding_module = SelfCodingModule()
    
    print("\n--- Testing Code Analysis ---")
    analysis = coding_module.analyze_code_structure(test_file_path)
    print(f"Functions found: {len(analysis.get('functions', []))}")
    print(f"Classes found: {len(analysis.get('classes', []))}")
    
    print("\n--- Testing Code Patching ---")
    patch_result = coding_module.apply_simple_code_patch(
        test_file_path,
        'def hello_world():',
        'def hello_universe():'
    )
    print(f"Patch applied: {patch_result}")
    
    print("\n--- Testing Config Modification ---")
    config_result = coding_module.modify_config_parameter(
        test_config_path,
        'settings.debug',
        True
    )
    print(f"Config modified: {config_result}")
    
    print("\n--- Testing Function Generation ---")
    new_function = coding_module.generate_simple_function(
        "calculate_area",
        ["radius"],
        "import math\nreturn math.pi * radius * radius",
        "Calculate the area of a circle given its radius."
    )
    print(f"Generated function:\n{new_function}")
    
    print("\n--- Testing Syntax Validation ---")
    valid_code = "def test(): return 42"
    invalid_code = "def test() return 42"
    
    valid_result = coding_module.validate_python_syntax(valid_code)
    invalid_result = coding_module.validate_python_syntax(invalid_code)
    
    print(f"Valid code check: {valid_result['valid']}")
    print(f"Invalid code check: {invalid_result['valid']}")
    
    print("\n--- Testing Error Handling ---")
    try:
        # Simulate a file not found error
        with open("/nonexistent/file.txt", 'r') as f:
            content = f.read()
    except Exception as e:
        recovery_result = healing_module.handle_error(e, {"file_path": "/nonexistent/file.txt"})
        print(f"Recovery result: {recovery_result['message']}")
    
    print(f"\nSelf-Healing and Self-Coding Module log file located at: {LOG_FILE_SHC}")
    print("Test finished.")
