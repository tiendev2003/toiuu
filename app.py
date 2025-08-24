# app.py
import datetime
import sys
import uuid
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, TimeoutError
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
from utils.upload import upload_image_to_host
from config import (
    PRINT_SERVER_IP, UPLOAD_FOLDER, OUTPUT_FOLDER, FRAME_TYPES, FRAME_MARGINS, FRAME_GAPS, 
    GAP_DEFAULT, GAP_PROCESSING, VIDEO_FPS, FAST_VIDEO_DURATION, 
    MAX_PROCESSING_WORKERS, MAX_UPLOAD_WORKERS, PROCESSING_TIMEOUT, 
    UPLOAD_TIMEOUT, URL_MAIN, URL_FRONTEND, FRAME_TYPE_DESCRIPTIONS, 
    get_frame_gap, get_frame_margin, get_print_margin, MAX_INPUT_IMAGE_SIZE,
    get_daily_folder, 
)
from utils.print_utils import print_image, get_local_ip, _download_and_save_image
def get_base_path():
    # Khi đóng gói bằng PyInstaller, dùng _MEIPASS làm base path
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

BASE_DIR = get_base_path()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("downloads", exist_ok=True)
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
            doubled_frame.save(image_output_file, "JPEG", quality=100, optimize=True, subsampling=0, progressive=False)
        else:
            # Frame thường, lưu trực tiếp
            frame.convert("RGB").save(image_output_file, "JPEG", quality=100, optimize=True, subsampling=0, progressive=False)
        
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
                    cleanup_files([image_output_file])  # Xoá file local sau khi upload thành công
                    logger.info(f"Media session updated with URL: {uploaded_url}")
                
                return uploaded_url
                
            except Exception as e:
                logger.warning(f"Failed to upload image to host: {e}")
        
        return uploaded_url
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
            crop_direction = "top" if frame_type and (
                (frame_type.get("columns") == 1 and frame_type.get("rows") == 1 and not frame_type.get("isCircle", False)) or
                (frame_type.get("columns") == 2 and frame_type.get("rows") == 2) or
                (frame_type.get("columns") == 1 and frame_type.get("rows") == 2 and not frame_type.get("isCustom", False))) else "center"
            background_img = fit_cover_image(background_img, (total_width, total_height), crop_direction)
        if overlay_path:
            overlay_img = Image.open(overlay_path).convert("RGBA")
            crop_direction = "top" if frame_type and (
                (frame_type.get("columns") == 1 and frame_type.get("rows") == 1 and not frame_type.get("isCircle", False)) or
                (frame_type.get("columns") == 2 and frame_type.get("rows") == 2) or
                (frame_type.get("columns") == 1 and frame_type.get("rows") == 2 and not frame_type.get("isCustom", False))) else "center"
            overlay_img = fit_cover_image(overlay_img, (total_width, total_height), crop_direction)
        
        
        response_data = {}
        unique_id = str(uuid.uuid4())
        with ThreadPoolExecutor(max_workers=MAX_PROCESSING_WORKERS) as executor:
            future = executor.submit(
                process_image_task, frame_type, image_files, positions, photo_width, photo_height,
                background_img, overlay_img, total_width, total_height, unique_id, media_session_code, filter_id
            )
            image_output_file = future.result(timeout=PROCESSING_TIMEOUT)
            print(f"Image output file: {image_output_file}")
            if image_output_file:
                response_data['image'] =  image_output_file
            else:
                cleanup_files(saved_files)
                return jsonify({"error": "Image processing failed"}), 500
            
        cleanup_files(saved_files)
        cleanup_files(image_files)
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
                
                # Chuẩn hóa video về h264+aac
                from utils.video_standardizer import standardize_video
                converted_path = standardize_video(converted_path, crf=23, preset="fast")
                
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
        
        logger.info(f"[VIDEO PROCESSING] Processing {len(video_files)} video files with frame type: {frame_type_choice}")
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
        
        # Chuẩn hóa tất cả video về h264+aac
        from utils.video_standardizer import standardize_videos_in_batch
        video_files = standardize_videos_in_batch(video_files, preset="fast", crf=23)
        
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
                try:
                    result = future.result(timeout=PROCESSING_TIMEOUT)
                    if result:
                        # Nếu result là URL (bắt đầu với http), sử dụng trực tiếp
                        # Nếu là file path, tạo URL local
                        if result.startswith('http'):
                            response_data[task_type] = result
                        else:
                            response_data[task_type] = f"/outputs/{os.path.basename(result)}"
                except TimeoutError:
                    logger.error(f"[VIDEO PROCESSING] Timeout error for {task_type} after {PROCESSING_TIMEOUT} seconds")
                    # Continue with other tasks instead of failing completely
                    continue
                except Exception as e:
                    logger.error(f"[VIDEO PROCESSING] Task error for {task_type}: {str(e)}")
                    continue
        
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
        filtered_img.save(output_path, "JPEG", quality=100)
        
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

@app.route('/api/print', methods=['POST'])
def download_image():
    data = request.get_json()
    image_url = data.get('filePath')
    printerName = data.get('printerName')
    quantity = data.get('quantity', 1)
    logger.info(f"Received print request for image: {image_url}, printer: {printerName}, quantity: {quantity}")
    
    if not image_url:
        return jsonify({"error": "URL is required"}), 400

    local_machine_ip = get_local_ip()
    print(f"Local Machine IP: {local_machine_ip}")

    try:
        if local_machine_ip == PRINT_SERVER_IP:
            print("This is the designated server. Performing local download.")
            result = _download_and_save_image(image_url)
            relative_path = result['image_path'].replace('/', os.sep).replace('\\', os.sep).lstrip(os.sep)
            full_path = os.path.join(os.getcwd(), relative_path)

            print(f"Image saved at: {full_path}")
            print_image(full_path, printerName, quantity)
            return jsonify({"message": "Image downloaded successfully", **result}), 200
        else:
            print(f"This is not the designated server. Forwarding request to {PRINT_SERVER_IP}.")
            forward_url = f"http://{PRINT_SERVER_IP}:4000/api/print"   
            forward_response = requests.post(forward_url, json={'filePath': image_url, 'printerName': printerName, 'quantity': quantity})
            forward_response.raise_for_status()  
            return jsonify(forward_response.json()), forward_response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding print request: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Flask application")
    # Tắt debug mode để tránh multiple processes và threading issues
    app.run(debug=True, host='0.0.0.0', port=8000, threaded=True, use_reloader=False)