# setup.py - File cấu hình để build exe với PyInstaller
import os
import sys

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import các module cần thiết để PyInstaller detect được
try:
    import flask
    import flask_cors
    import PIL
    import cv2
    import numpy
    import requests
    import qrcode
    import uuid
    import datetime
    import concurrent.futures
    import time
    import json
    
    # Import các module local
    from utils import logging, file_handling, image_processing, video_processing
    from utils import filters, performance, printer, upload
    import config
    
    print("All modules imported successfully!")
    
except ImportError as e:
    print(f"Error importing module: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("Setup completed successfully!")
