# utils/file_handling.py
import os
import uuid
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder, prefix=""):
    if not file or not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    unique_filename = f"{prefix}{uuid.uuid4()}_{filename}"
    file_path = os.path.join(folder, unique_filename)
    file.save(file_path)
    return file_path

def cleanup_files(file_paths):
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {e}")

def save_uploaded_files(files, background_file, overlay_file, folder=UPLOAD_FOLDER):
    saved_files = []
    image_files = []
    background_path = None
    overlay_path = None
    
    if background_file and allowed_file(background_file.filename):
        background_path = save_file(background_file, folder, "bg_")
        saved_files.append(background_path)
    
    if overlay_file and allowed_file(overlay_file.filename):
        overlay_path = save_file(overlay_file, folder, "ov_")
        saved_files.append(overlay_path)
    
    for file in files:
        if file and allowed_file(file.filename):
            # Xử lý đặc biệt cho WebM files từ browser
            prefix = ""
            if file.filename.lower().endswith('.webm'):
                prefix = "webm_"
                print(f"[FILE HANDLING] Detected WebM file: {file.filename}")
            
            file_path = save_file(file, folder, prefix)
            if file_path:
                saved_files.append(file_path)
                image_files.append(file_path)
    
    return image_files, background_path, overlay_path, saved_files