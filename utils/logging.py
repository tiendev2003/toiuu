# utils/logging.py
import logging
import logging.handlers
import os

def setup_logging():
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger('photo_api')
    
    # Tránh thêm handlers nhiều lần khi Flask restart
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/photo_api.log', maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    app_logger = logging.getLogger('werkzeug')
    if not app_logger.handlers:
        app_logger.setLevel(logging.INFO)
        app_logger.addHandler(file_handler)
    
    return logger