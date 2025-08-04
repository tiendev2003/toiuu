# utils/performance.py
import time
import psutil
import os
from functools import wraps
from utils.logging import setup_logging

logger = setup_logging()

def performance_monitor(func):
    """Decorator để monitor performance của các function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            logger.info(f"[PERFORMANCE] {func.__name__}: {execution_time:.2f}s, Memory: {memory_used:.1f}MB")
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"[PERFORMANCE] {func.__name__} FAILED after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper

def get_system_stats():
    """Lấy thông tin hệ thống hiện tại"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_mb": memory.available / 1024 / 1024,
        "disk_free_gb": disk.free / 1024 / 1024 / 1024
    }

def log_system_stats():
    """Log thông tin hệ thống"""
    stats = get_system_stats()
    logger.info(f"[SYSTEM] CPU: {stats['cpu_percent']:.1f}%, "
                f"Memory: {stats['memory_percent']:.1f}% "
                f"({stats['memory_available_mb']:.0f}MB free), "
                f"Disk: {stats['disk_free_gb']:.1f}GB free")
