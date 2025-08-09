import logging
import logging.handlers
import os
import sys

def get_base_dir():
    """
    Lấy thư mục gốc tuỳ theo cách chạy (py hoặc exe)
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def setup_logging():
    base_dir = get_base_dir()
    logs_dir = os.path.join(base_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(logs_dir, 'photo_api.log')
    
    logger = logging.getLogger('photo_api')

    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Ghi log cho Flask (nếu có dùng Flask)
    app_logger = logging.getLogger('werkzeug')
    if not app_logger.handlers:
        app_logger.setLevel(logging.INFO)
        app_logger.addHandler(file_handler)
    
    return logger
