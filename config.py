# config.py
import os
from datetime import datetime

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE_FOLDER = os.path.join(BASE_DIR, 'uploads')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
OUTPUT_BASE_FOLDER = os.path.join(BASE_DIR, 'outputs')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'webm'}

HEIGHT_IMAGE = 3304     
HEIGHT_IMAGE_CUSTOM = 1652  
WIDTH_IMAGE = 4956       

ENABLE_IMAGE_OPTIMIZATION = True
MAX_INPUT_IMAGE_SIZE = 2048  # Giới hạn kích thước ảnh input

# Frame types and aspect ratios
FRAME_TYPES = {
    "1": {"name": "Khung hình 6 (1x1)", "columns": 1, "rows": 1, "isCustom": False, "isCircle": False},
    "2": {"name": "Khung hình tròn (1x1)", "columns": 1, "rows": 1, "isCustom": False, "isCircle": True},
    "3": {"name": "Khung hình 1x2 (6x2in)", "columns": 1, "rows": 2, "isCustom": True, "isCircle": False},
    "4": {"name": "Khung hình 2x1", "columns": 2, "rows": 1, "isCustom": False, "isCircle": False},
    "5": {"name": "Khung hình 2x2", "columns": 2, "rows": 2, "isCustom": False, "isCircle": False},
    "6": {"name": "Khung hình 1x4 (6x2in)", "columns": 1, "rows": 4, "isCustom": True, "isCircle": False},
    "7": {"name": "Khung hình 2x3", "columns": 2, "rows": 3, "isCustom": False, "isCircle": False},
    "8": {"name": "Khung hình 3x2", "columns": 3, "rows": 2, "isCustom": False, "isCircle": False}
}

ASPECT_RATIOS = {
    (1, 1, False): (16, 9), (1, 1, True): (1, 1), (2, 1, False): (1, 1),
    (2, 1, True): (3, 4), (2, 2, False): (4, 3), (3, 2, False): (5, 4),
    (2, 3, False): (13, 12), (1, 4, True): (4, 3), (1, 2, True): (3, 4)
}

# Frame margins and gaps

GAP_MIN = 80
GAP_DEFAULT = 160            
GAP_PROCESSING = 110    
MARGIN_DEFAULT = 80         
MARGIN_LARGE = 160     
FRAME_TYPE_DESCRIPTIONS = {key: value["name"] for key, value in FRAME_TYPES.items()}
FRAME_MARGINS = {
    "1": MARGIN_DEFAULT,   
    "2": MARGIN_DEFAULT,   
    "3": MARGIN_DEFAULT,    
    "4": MARGIN_DEFAULT,     
    "5": MARGIN_DEFAULT,     
    "6": MARGIN_LARGE,     
    "7": MARGIN_DEFAULT,   
    "8": MARGIN_DEFAULT,  
}
FRAME_GAPS = {
    "1": GAP_MIN,      # Frame 1x1 không cần gap
    "2": GAP_MIN,      # Frame 1x1 hoặc 2x1 
    "3": GAP_MIN,   # Frame custom
    "4": GAP_MIN,      # Frame 2x2
    "5": GAP_MIN,      # Frame 2x3
    "6": GAP_MIN,   # Frame custom
    "7": GAP_MIN,      # Frame 3x3
    "8": GAP_MIN,   # Frame custom
}
# Video settings
VIDEO_FPS = 30
FAST_VIDEO_DURATION = 2

# Threading settings
MAX_PROCESSING_WORKERS = 6  # Tăng số worker để xử lý song song
MAX_UPLOAD_WORKERS = 3      # Tăng upload workers
PROCESSING_TIMEOUT = 180    # Giảm timeout để fail fast
UPLOAD_TIMEOUT = 60
 
# URLs
URL_MAIN = "http://localhost:4000"
URL_FRONTEND = "https://s.mayphotobooth.com"
URL_PRINT = "http://localhost:5000/api/print"

# Print server settings
PRINT_SERVER_IP = "192.168.1.9"  # IP máy chủ in - thay đổi theo ip thực tế
PRINT_SERVER_PORT = 5000
PRINT_API_ENDPOINT = "/api/print"
PRINT_LIST_ENDPOINT = "/api/printers"
PRINTER_CACHE_TIMEOUT = 300  # 5 phút cache danh sách máy in

def get_daily_folder(base_folder):
    today = datetime.now().strftime('%Y-%m-%d')
    daily_folder = os.path.join(base_folder, today)
    os.makedirs(daily_folder, exist_ok=True)
    os.chmod(daily_folder, 0o755)
    return daily_folder

def get_frame_margin(frame_id):
    return FRAME_MARGINS.get(frame_id, MARGIN_DEFAULT)

def get_frame_gap(frame_id):
    return FRAME_GAPS.get(frame_id, GAP_DEFAULT)

def get_print_margin(orientation):
    return 0.02  # 2% margin for DNP printing