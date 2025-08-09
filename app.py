# app.py
import datetime
import sys
import uuid
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import time
import os
import requests
import qrcode
from PIL import Image, ImageDraw, ImageEnhance
from utils.logging import setup_logging
from utils.file_handling import save_uploaded_files, cleanup_files, allowed_file, save_file
from utils.image_processing import get_frame_type, get_frame_size, calc_positions, paste_image, fit_cover_image
from utils.video_processing import process_video_task, process_fast_video_task
from utils.filters import apply_filter_to_image
from utils.performance import performance_monitor, log_system_stats
from utils.printer import get_printers_list, send_print_job, get_print_status, is_print_server, send_print_job_to_server
from utils.upload import upload_image_to_host
from config import (
    UPLOAD_FOLDER, OUTPUT_FOLDER, FRAME_TYPES, FRAME_MARGINS, FRAME_GAPS, 
    GAP_DEFAULT, GAP_PROCESSING, VIDEO_FPS, FAST_VIDEO_DURATION, 
    MAX_PROCESSING_WORKERS, MAX_UPLOAD_WORKERS, PROCESSING_TIMEOUT, 
    UPLOAD_TIMEOUT, URL_MAIN, URL_FRONTEND, FRAME_TYPE_DESCRIPTIONS, 
    get_frame_gap, get_frame_margin, get_print_margin, MAX_INPUT_IMAGE_SIZE,
    get_daily_folder, PRINT_SERVER_IP, PRINT_SERVER_PORT
)
def get_base_path():
    # Khi đóng gói bằng PyInstaller, dùng _MEIPASS làm base path
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

BASE_DIR = get_base_path()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
logger = setup_logging()

@app.before_request
def log_request_info():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    logger.info(f"[REQUEST] {request.method} {request.url} from IP: {client_ip}")

@app.after_request
def log_response_info(response):
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    logger.info(f"[RESPONSE] {request.method} {request.url} - Status: {response.status_code} - IP: {client_ip}")
    return response

# Thêm cache cho QR code
qr_cache = {}

# Cache cho upload để tránh upload cùng file nhiều lần
upload_cache = {}

def cleanup_old_cache():
    """Cleanup cache entries older than 1 hour"""
    import time
    current_time = time.time()
    keys_to_remove = []
    
    for key in upload_cache:
        # Extract timestamp from cache key
        try:
            timestamp = float(key.split('_')[-1])
            if current_time - timestamp > 3600:  # 1 hour
                keys_to_remove.append(key)
        except (ValueError, IndexError):
            continue
    
    for key in keys_to_remove:
        del upload_cache[key]
    
    # Cleanup QR cache if it gets too large
    if len(qr_cache) > 100:
        qr_cache.clear()

def get_qr_code(url, size=(200, 200)):
    """Cache QR codes để tránh tạo lại nhiều lần"""
    if url in qr_cache:
        return qr_cache[url]
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize(size, Image.Resampling.BICUBIC)
    qr_cache[url] = qr_img
    return qr_img

def prepare_for_dnp_printing(img, orientation="4x6"):
    current_width, current_height = img.size
    safe_width = int(current_width * 0.96)
    safe_height = int(current_height * 0.96)
    safe_img = Image.new("RGB", (current_width, current_height), (255, 255, 255))
    x_offset = (current_width - safe_width) // 2
    y_offset = (current_height - safe_height) // 2
    resized_img = img.resize((safe_width, safe_height), Image.Resampling.LANCZOS)
    safe_img.paste(resized_img, (x_offset, y_offset))
    enhancer = ImageEnhance.Sharpness(safe_img)
    return enhancer.enhance(1.1)

def update_media_session(media_session_code, image_url=None, video_url=None, fast_video_url=None):
    if not media_session_code:
        logger.warning("No media session code provided")
        return False
    
    update_url = f"{URL_FRONTEND}/api/media-session"
    update_data = {"sessionCode": media_session_code}
    if image_url:
        update_data["imageUrl"] = image_url
    if video_url:
        update_data["videoUrl"] = video_url
    if fast_video_url:
        update_data["gifUrl"] = fast_video_url
    
    try:
        response = requests.put(update_url, json=update_data)
        if response.status_code == 200:
            logger.info(f"Media session updated: {response.json()}")
            return True
        logger.error(f"Failed to update media session: {response.status_code}, {response.text}")
        return False
    except Exception as e:
        logger.error(f"Error updating media session: {str(e)}")
        return False

@performance_monitor
def process_image_task(frame_type, image_files, positions, photo_width, photo_height, background_img, overlay_img, total_width, total_height, unique_id, media_session_code=None, filter_id=None):
    try:
        # Cleanup old cache entries periodically
        cleanup_old_cache()
        
        # Sử dụng daily folder để lưu file
        daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
        image_output_file = os.path.join(daily_output_folder, f"photobooth_result_{unique_id}.jpg")
        total_slots = frame_type["columns"] * frame_type["rows"]
        output_width = total_width * 2 if frame_type["isCustom"] and frame_type["columns"] == 1 else total_width
        output_height = total_height

        frame = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 255))
        if background_img:
            frame.paste(background_img, (0, 0))
        
        # Xử lý ảnh song song thay vì tuần tự
        processed_images = []
        for file in image_files[:total_slots]:
            img = Image.open(file).convert("RGBA")
            # Giảm kích thước ảnh trước khi apply filter để tăng tốc
            if img.width > MAX_INPUT_IMAGE_SIZE or img.height > MAX_INPUT_IMAGE_SIZE:
                img.thumbnail((MAX_INPUT_IMAGE_SIZE, MAX_INPUT_IMAGE_SIZE), Image.Resampling.BICUBIC)
            
            if filter_id and filter_id != 'none':
                img = apply_filter_to_image(img, filter_id)
            processed_images.append(img)
        
        for img, pos in zip(processed_images, positions):
            frame = paste_image(frame, img, pos, (photo_width, photo_height), frame_type.get("isCircle", False), frame_type)
        
        if overlay_img:
            frame.paste(overlay_img, (0, 0), overlay_img)
        
        # Thêm QR code trước khi tạo ảnh kép cho frame isCustom
        if media_session_code:
            qr_url = f"{URL_FRONTEND}/session/{media_session_code}"
            qr_img = get_qr_code(qr_url, (180, 180))  # Giảm kích thước QR
            margin = 160 if frame_type["isCustom"] and frame_type["rows"] == 4 else 80
            
            # Với frame isCustom, thêm QR vào frame gốc trước khi ghép đôi
            if frame_type["isCustom"] and frame_type["columns"] == 1:
                x_pos = total_width - 180 - margin
                y_pos = total_height - 180 - margin
                frame.paste(qr_img, (x_pos, y_pos))
            else:
                # Frame thường, sử dụng output_width
                x_pos = output_width - 180 - margin
                y_pos = output_height - 180 - margin
                frame.paste(qr_img, (x_pos, y_pos))
        
        # Tạo ảnh kép cho frame isCustom sau khi đã thêm QR code
        if frame_type["isCustom"] and frame_type["columns"] == 1:
            # Tạo ảnh kép với kích thước gấp đôi chiều rộng
            doubled_frame = Image.new("RGB", (output_width, output_height), (255, 255, 255))
            frame_rgb = frame.convert("RGB")
            doubled_frame.paste(frame_rgb, (0, 0))
            doubled_frame.paste(frame_rgb, (total_width, 0))
            doubled_frame.save(image_output_file, "JPEG", quality=92, optimize=True, subsampling=0, progressive=False)
        else:
            # Frame thường, lưu trực tiếp
            frame.convert("RGB").save(image_output_file, "JPEG", quality=92, optimize=True, subsampling=0, progressive=False)
        
        # Upload ảnh lên host để lưu trữ
        if os.path.exists(image_output_file):
            try:
                # Sử dụng cache để tránh upload cùng file nhiều lần
                file_hash = f"{os.path.basename(image_output_file)}_{os.path.getmtime(image_output_file)}"
                if file_hash not in upload_cache:
                    uploaded_url = upload_image_to_host(image_output_file)
                    if uploaded_url:
                        upload_cache[file_hash] = uploaded_url
                        logger.info(f"Image uploaded and cached: {uploaded_url}")
                else:
                    uploaded_url = upload_cache[file_hash]
                    logger.info(f"Using cached upload URL: {uploaded_url}")
                
                if uploaded_url and media_session_code:
                    # Cập nhật media session với URL đã upload
                    update_media_session(media_session_code, image_url=uploaded_url)
                    logger.info(f"Media session updated with URL: {uploaded_url}")
            except Exception as e:
                logger.warning(f"Failed to upload image to host: {e}")
        
        # Tự động gọi hàm in ngay sau khi tạo ảnh
        try:
            # Xác định máy in dựa vào frame type
            printer_name = "DS-RX1-Cut" if frame_type.get("isCustom", False) else "DS-RX1"
            
            # Kiểm tra xem máy hiện tại có phải máy chủ in không
            if is_print_server():
                # Nếu là máy chủ in, in trực tiếp từ file local
                logger.info(f"Auto printing locally: {os.path.basename(image_output_file)} to {printer_name}")
                send_print_job(image_output_file, printer_name, copies=1, paper_size="4x6")
            else:
                # Nếu không phải máy chủ in, gửi file đến máy chủ in qua API
                logger.info(f"Auto sending print job to server: {os.path.basename(image_output_file)} to {printer_name}")
                send_print_job_to_server(image_output_file, printer_name, copies=1, paper_size="4x6")
            
            logger.info(f"Print job sent to {printer_name} (fire and forget)")
                
        except Exception as e:
            logger.warning(f"Failed to auto print: {e}")
        
        return image_output_file
    except Exception as e:
        logger.error(f"Error in image processing: {str(e)}")
        return None

@app.route('/api/process-image', methods=['POST'])
def process_image():
    log_system_stats()  # Log system stats trước khi xử lý
    saved_files = []  # Initialize saved_files to avoid UnboundLocalError
    try:
        frame_type_choice = request.form.get('frame_type')
        if not frame_type_choice:
            return jsonify({"error": "Missing frame_type parameter"}), 400
        
        frame_type = get_frame_type(frame_type_choice)
        total_width, total_height = get_frame_size(frame_type)
        media_session_code = request.form.get('mediaSessionCode')
        filter_id = request.form.get('filter_id', 'none')
        files = request.files.getlist('files')
        background_file = request.files.get('background')
        overlay_file = request.files.get('overlay')
        
        # Save files and update saved_files
        image_files, background_path, overlay_path, saved_files = save_uploaded_files(files, background_file, overlay_file)
        if not image_files:
            cleanup_files(saved_files)
            return jsonify({"error": "No valid image files"}), 400
        
        margin = get_frame_margin(frame_type_choice)
        gap = get_frame_gap(frame_type_choice)
        photo_width, photo_height, positions = calc_positions(frame_type, total_width, total_height, margin, gap)
        
        background_img = None
        overlay_img = None
        if background_path:
            background_img = Image.open(background_path).convert("RGB")
            crop_direction = "top" if frame_type.get("columns") in [1, 2] and frame_type.get("rows") in [1, 2] else "center"
            background_img = fit_cover_image(background_img, (total_width, total_height), crop_direction)
        if overlay_path:
            overlay_img = Image.open(overlay_path).convert("RGBA")
            crop_direction = "top" if frame_type.get("columns") in [1, 2] and frame_type.get("rows") in [1, 2] else "center"
            overlay_img = fit_cover_image(overlay_img, (total_width, total_height), crop_direction)
        
        response_data = {}
        unique_id = str(uuid.uuid4())
        with ThreadPoolExecutor(max_workers=MAX_PROCESSING_WORKERS) as executor:
            future = executor.submit(
                process_image_task, frame_type, image_files, positions, photo_width, photo_height,
                background_img, overlay_img, total_width, total_height, unique_id, media_session_code, filter_id
            )
            image_output_file = future.result(timeout=PROCESSING_TIMEOUT)
            if image_output_file:
                response_data['image'] = f"/outputs/{os.path.basename(image_output_file)}"
            else:
                cleanup_files(saved_files)
                return jsonify({"error": "Image processing failed"}), 500
        
        if 'image' in response_data and request.form.get('prepare_for_printing', 'false').lower() == 'true':
            print_orientation = request.form.get('print_orientation', '4x6')
            # Sử dụng daily folder để tìm file
            daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
            image_path = os.path.join(daily_output_folder, os.path.basename(response_data['image']))
            if os.path.exists(image_path):
                img = Image.open(image_path)
                print_img = prepare_for_dnp_printing(img, print_orientation)
                
                # Không cần tạo ảnh kép nữa vì đã được xử lý trong process_image_task
                print_path = os.path.join(daily_output_folder, f"print_{unique_id}.jpg")
                print_img.save(print_path, "JPEG", quality=95)
                response_data['print_image'] = f"/outputs/print_{unique_id}.jpg"
        
        cleanup_files(saved_files)
        return jsonify(response_data), 200
    except Exception as e:
        cleanup_files(saved_files)
        logger.error(f"[IMAGE PROCESSING] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/convert-video', methods=['POST'])
def convert_video():
    """
    Endpoint để convert video WebM từ client sang MP4 trước khi xử lý chính
    """
    saved_files = []
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files provided"}), 400
        
        converted_results = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Save file tạm thời
                temp_path = save_file(file, UPLOAD_FOLDER, "temp_")
                saved_files.append(temp_path)
                
                # Convert nếu là WebM
                from utils.video_processing import convert_webm_to_mp4
                converted_path = convert_webm_to_mp4(temp_path)
                
                if converted_path != temp_path:
                    saved_files.append(converted_path)
                
                # Tạo response với info video
                file_info = {
                    "original_name": file.filename,
                    "converted_path": os.path.basename(converted_path),
                    "size": os.path.getsize(converted_path),
                    "format": "mp4" if converted_path.endswith('.mp4') else os.path.splitext(converted_path)[1][1:]
                }
                
                converted_results.append(file_info)
        
        return jsonify({
            "success": True,
            "converted_files": converted_results,
            "message": f"Converted {len(converted_results)} files successfully"
        }), 200
        
    except Exception as e:
        cleanup_files(saved_files)
        logger.error(f"[VIDEO CONVERT API] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/process-video', methods=['POST'])
def process_video():
    saved_files = []  # Initialize saved_files to avoid UnboundLocalError
    try:
        frame_type_choice = request.form.get('frame_type')
        if not frame_type_choice:
            return jsonify({"error": "Missing frame_type parameter"}), 400
        
        frame_type = get_frame_type(frame_type_choice)
        total_width, total_height = get_frame_size(frame_type)
        media_session_code = request.form.get('mediaSessionCode')
        duration = int(request.form.get('duration', 2))
        upload_to_host = request.form.get('upload_to_host', 'true').lower() == 'true'  # Tùy chọn upload
        if duration not in [2, 10]:
            return jsonify({"error": "Duration must be 2 or 10 seconds"}), 400
        
        files = request.files.getlist('files')
        background_file = request.files.get('background')
        overlay_file = request.files.get('overlay')
        
        # Save files and update saved_files
        video_files, background_path, overlay_path, saved_files = save_uploaded_files(files, background_file, overlay_file)
        if not video_files:
            cleanup_files(saved_files)
            return jsonify({"error": "No valid video files"}), 400
        
        # Convert WebM files to MP4 for better compatibility
        from utils.video_processing import convert_webm_to_mp4
        converted_files = []
        for video_file in video_files:
            converted_file = convert_webm_to_mp4(video_file)
            if converted_file:
                converted_files.append(converted_file)
                saved_files.append(converted_file)
            else:
                converted_files.append(video_file)  # Keep original if conversion fails
        video_files = converted_files
        
        margin = get_frame_margin(frame_type_choice)
        gap = get_frame_gap(frame_type_choice)
        photo_width, photo_height, positions = calc_positions(frame_type, total_width, total_height, margin, gap)
        
        response_data = {}
        with ThreadPoolExecutor(max_workers=MAX_PROCESSING_WORKERS) as executor:
            # Sử dụng OpenCV - đã được optimize và nhanh nhất trong benchmark
            tasks = [('video', executor.submit(
                process_video_task, frame_type, video_files, background_path, overlay_path, total_width, total_height, duration, upload_to_host
            ))]
            if duration > 2:
                tasks.append(('fast_video', executor.submit(
                    process_fast_video_task, frame_type, video_files, background_path, overlay_path, total_width, total_height, duration, upload_to_host
                )))
            
            for task_type, future in tasks:
                result = future.result(timeout=PROCESSING_TIMEOUT)
                if result:
                    # Nếu result là URL (bắt đầu với http), sử dụng trực tiếp
                    # Nếu là file path, tạo URL local
                    if result.startswith('http'):
                        response_data[task_type] = result
                    else:
                        response_data[task_type] = f"/outputs/{os.path.basename(result)}"
        
        if not response_data:
            cleanup_files(saved_files)
            return jsonify({"error": "Video processing failed"}), 500
        
        if media_session_code:
            # Xử lý video URL
            video_url = None
            if 'video' in response_data:
                video_response = response_data.get('video')
                if video_response.startswith('http'):
                    video_url = video_response
                else:
                    video_url = f"{URL_MAIN}{video_response}"
            
            # Xử lý fast video URL
            fast_video_url = None
            if 'fast_video' in response_data:
                fast_video_response = response_data.get('fast_video')
                if fast_video_response.startswith('http'):
                    fast_video_url = fast_video_response
                else:
                    fast_video_url = f"{URL_MAIN}{fast_video_response}"
            
            update_media_session(media_session_code, video_url=video_url, fast_video_url=fast_video_url)
        
        cleanup_files(saved_files)
        return jsonify(response_data), 200
    except Exception as e:
        cleanup_files(saved_files)
        logger.error(f"[VIDEO PROCESSING] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/frame-types', methods=['GET'])
def get_frame_types():
    return jsonify(FRAME_TYPES)

@app.route('/api/frame-constants', methods=['GET'])
def get_frame_constants():
    return jsonify({
        "margins": FRAME_MARGINS,
        "gaps": {
            "default": GAP_DEFAULT,
            "processing": GAP_PROCESSING,
            "frame_specific": FRAME_GAPS
        },
        "video_settings": {
            "fps": VIDEO_FPS,
            "fast_video_duration": FAST_VIDEO_DURATION
        },
        "threading_settings": {
            "max_processing_workers": MAX_PROCESSING_WORKERS,
            "max_upload_workers": MAX_UPLOAD_WORKERS,
            "processing_timeout": PROCESSING_TIMEOUT,
            "upload_timeout": UPLOAD_TIMEOUT
        },
        "frame_descriptions": FRAME_TYPE_DESCRIPTIONS
    })

@app.route('/api/performance-info', methods=['GET'])
def get_performance_info():
    return jsonify({
        "threading_enabled": True,
        "max_workers": {
            "processing": MAX_PROCESSING_WORKERS,
            "upload": MAX_UPLOAD_WORKERS
        },
        "timeouts": {
            "processing": f"{PROCESSING_TIMEOUT}s",
            "upload": f"{UPLOAD_TIMEOUT}s"
        },
        "parallel_features": [
            "Image processing",
            "Video processing",
            "Fast video processing",
            "File uploads"
        ],
        "performance_benefits": [
            "Reduced total processing time",
            "Parallel image and video generation",
            "Concurrent uploads",
            "Better resource utilization"
        ]
    })

@app.route('/api/apply-filter', methods=['POST'])
def apply_filter():
    try:
        image_file = request.files.get('image')
        filter_id = request.form.get('filter_id', 'none')
        
        if not image_file or not allowed_file(image_file.filename):
            return jsonify({"error": "Invalid image file"}), 400
        
        img = Image.open(image_file)
        filtered_img = apply_filter_to_image(img, filter_id)
        
        output_filename = f"filtered_{uuid.uuid4()}.jpg"
        # Sử dụng daily folder để lưu file
        daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
        output_path = os.path.join(daily_output_folder, output_filename)
        filtered_img.save(output_path, "JPEG", quality=95)
        
        return jsonify({"success": True, "filtered_image_url": f"/outputs/{output_filename}"}), 200
    except Exception as e:
        logger.error(f"[FILTER] Error: {str(e)}")
        return jsonify({"error": f"Filter application failed: {str(e)}"}), 500

 

@app.route('/api/cleanup-local-video', methods=['POST'])
def cleanup_local_video():
    """Delete local video file"""
    try:
        filename = request.form.get('filename')
        if not filename:
            return jsonify({"error": "Missing filename parameter"}), 400
        
        # Tìm file trong daily folders
        daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
        file_path = os.path.join(daily_output_folder, filename)
        
        if not os.path.exists(file_path):
            # Tìm trong các folder khác
            for folder in os.listdir(OUTPUT_FOLDER):
                folder_path = os.path.join(OUTPUT_FOLDER, folder)
                if os.path.isdir(folder_path):
                    test_path = os.path.join(folder_path, filename)
                    if os.path.exists(test_path):
                        file_path = test_path
                        break
            else:
                return jsonify({"error": "File not found"}), 404
        
        from utils.upload import cleanup_local_video_file
        success = cleanup_local_video_file(file_path)
        
        if success:
            return jsonify({"success": True, "message": "File deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete file"}), 500
    except Exception as e:
        logger.error(f"[LOCAL VIDEO CLEANUP] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        daily_folder = os.path.join(OUTPUT_FOLDER, today)
        file_path = os.path.join(daily_folder, filename)
        
        mime_type = None
        if filename.lower().endswith('.mp4'):
            mime_type = 'video/mp4'
        elif filename.lower().endswith('.webm'):
            mime_type = 'video/webm'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            mime_type = 'image/png'
        
        if os.path.exists(file_path):
            return send_from_directory(daily_folder, filename, mimetype=mime_type)
        
        for folder in os.listdir(OUTPUT_FOLDER):
            folder_path = os.path.join(OUTPUT_FOLDER, folder)
            if os.path.isdir(folder_path) and os.path.exists(os.path.join(folder_path, filename)):
                return send_from_directory(folder_path, filename, mimetype=mime_type)
        
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"[FILE SERVE] Error: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print')
def print_page():
    return render_template('print.html')

@app.route('/api/printers', methods=['GET'])
def get_printers():
    """Lấy danh sách máy in có sẵn"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if not is_print_server():
            return jsonify({
                "success": False,
                "error": "not_print_server",
                "message": "Current machine is not configured as print server",
                "printers": []
            }), 200
        
        printers = get_printers_list(force_refresh=force_refresh)
        
        return jsonify({
            "success": True,
            "printers": printers,
            "is_print_server": True,
            "message": f"Found {len(printers)} printers"
        }), 200
        
    except Exception as e:
        logger.error(f"[GET PRINTERS] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "unexpected_error",
            "message": str(e)
        }), 500

@app.route('/api/print', methods=['POST'])
def print_image():
    """Gửi lệnh in ảnh tới máy in"""
    saved_files = []
    try:
        # Lấy parameters từ request
        image_filename = request.form.get('image_filename') 
        printer_name = request.form.get("printer_name", "DS-RX1")
        copies = int(request.form.get('copies', 1))
        paper_size = request.form.get('paper_size', '4x6')
        
        # Kiểm tra xem có file được upload không
        uploaded_file = request.files.get('image_file')
        
        if uploaded_file and uploaded_file.filename:
            # Nếu có file upload, save file tạm thời để in
            from utils.file_handling import save_file
            temp_image_path = save_file(uploaded_file, UPLOAD_FOLDER, "temp_print_")
            saved_files.append(temp_image_path)
            image_path = temp_image_path
            logger.info(f"Received uploaded file for printing: {uploaded_file.filename}")
        else:
            # Nếu không có file upload, tìm file local theo tên
            if not image_filename:
                image_filename = "photobooth_result.jpg" + f"?{uuid.uuid4()}"  # Thêm UUID để tránh cache

            if not printer_name:
                return jsonify({
                    "success": False,
                    "error": "missing_printer",
                    "message": "Printer name is required"
                }), 400
            
            # Tìm file ảnh trong daily folders
            daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
            image_path = os.path.join(daily_output_folder, image_filename)
            
            if not os.path.exists(image_path):
                # Tìm trong các folder khác
                for folder in os.listdir(OUTPUT_FOLDER):
                    folder_path = os.path.join(OUTPUT_FOLDER, folder)
                    if os.path.isdir(folder_path):
                        test_path = os.path.join(folder_path, image_filename)
                        if os.path.exists(test_path):
                            image_path = test_path
                            break
                else:
                    return jsonify({
                        "success": False,
                        "error": "file_not_found",
                        "message": f"Image file '{image_filename}' not found"
                    }), 404

        if not printer_name:
            return jsonify({
                "success": False,
                "error": "missing_printer", 
                "message": "Printer name is required"
            }), 400
        
        # Kiểm tra xem máy hiện tại có phải máy chủ in không
        if is_print_server():
            # Nếu là máy chủ in, in trực tiếp từ file local
            logger.info(f"Printing locally on print server: {image_filename}")
            result = send_print_job(image_path, printer_name, copies, paper_size)
        else:
            # Nếu không phải máy chủ in, gửi file đến máy chủ in qua API
            logger.info(f"Sending print job to print server: {image_filename}")
            result = send_print_job_to_server(image_path, printer_name, copies, paper_size)
        
        if result["success"]:
            logger.info(f"Print job processed: {image_filename} to {printer_name} ({copies} copies)")
            # Cleanup uploaded files
            cleanup_files(saved_files)
            return jsonify(result), 200
        else:
            # Cleanup uploaded files
            cleanup_files(saved_files)
            return jsonify(result), 500
        
    except ValueError as e:
        cleanup_files(saved_files)
        return jsonify({
            "success": False,
            "error": "invalid_copies",
            "message": "Copies must be a valid number"
        }), 400
    
    except Exception as e:
        cleanup_files(saved_files)
        logger.error(f"[PRINT IMAGE] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "unexpected_error",
            "message": str(e)
        }), 500

@app.route('/api/print-status/<job_id>', methods=['GET'])
def check_print_status(job_id):
    """Kiểm tra trạng thái công việc in"""
    try:
        if not is_print_server():
            return jsonify({
                "success": False,
                "error": "not_print_server",
                "message": "Current machine is not configured as print server"
            }), 400
        
        result = get_print_status(job_id)
        return jsonify(result), 200 if result.get("success") else 500
        
    except Exception as e:
        logger.error(f"[PRINT STATUS] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "unexpected_error",
            "message": str(e)
        }), 500

@app.route('/api/print-server-info', methods=['GET'])
def get_print_server_info():
    """Lấy thông tin về máy chủ in"""
    try:
        from utils.printer import get_local_ip
        
        local_ip = get_local_ip()
        is_server = is_print_server()
        
        return jsonify({
            "local_ip": local_ip,
            "print_server_ip": PRINT_SERVER_IP,
            "is_print_server": is_server,
            "print_server_port": PRINT_SERVER_PORT,
            "message": "Print server ready" if is_server else "Not a print server"
        }), 200
        
    except Exception as e:
        logger.error(f"[PRINT SERVER INFO] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "unexpected_error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    # Tắt debug mode để tránh multiple processes và threading issues
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)