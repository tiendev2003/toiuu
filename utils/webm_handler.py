# utils/webm_handler.py
"""
Module xử lý đặc biệt cho WebM files từ browser
"""
import os
import subprocess
import shutil
import sys
from utils.logging import setup_logging
from utils.ffmpeg_utils import get_ffmpeg_command, get_ffprobe_command, check_ffmpeg_availability, check_ffprobe_availability

logger = setup_logging()

def get_ffmpeg_path():
    """Deprecated: Use ffmpeg_utils.get_ffmpeg_command() instead"""
    try:
        return get_ffmpeg_command()
    except FileNotFoundError:
        if getattr(sys, 'frozen', False):  # Running from .exe
            return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        else:
            # Tìm trong thư mục utils
            local_ffmpeg = os.path.join(os.path.dirname(__file__), '..', 'ffmpeg.exe')
            if os.path.exists(local_ffmpeg):
                return local_ffmpeg
            return 'ffmpeg'  # Fallback to system PATH

def get_ffprobe_path():
    """Deprecated: Use ffmpeg_utils.get_ffprobe_command() instead"""
    try:
        return get_ffprobe_command()
    except FileNotFoundError:
        if getattr(sys, 'frozen', False):  # Running from .exe
            return os.path.join(sys._MEIPASS, 'ffprobe.exe')
        else:
            # Tìm trong thư mục utils
            local_ffprobe = os.path.join(os.path.dirname(__file__), '..', 'ffprobe.exe')
            if os.path.exists(local_ffprobe):
                return local_ffprobe
            return 'ffprobe'  # Fallback to system PATH

def detect_webm_codec(webm_file):
    """
    Phát hiện codec của file WebM để xử lý tương thích
    """
    if not check_ffprobe_availability():
        return None
    
    try:
        ffprobe_cmd = get_ffprobe_command()
        
        cmd = [
            ffprobe_cmd, '-v', 'quiet', '-print_format', 'json',
            '-show_streams', webm_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        
        import json
        data = json.loads(result.stdout)
        
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        if video_stream:
            return {
                'codec_name': video_stream.get('codec_name'),
                'pix_fmt': video_stream.get('pix_fmt'),
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'fps': eval(video_stream.get('r_frame_rate', '30/1'))
            }
    except Exception as e:
        logger.warning(f"Failed to detect WebM codec: {e}")
    
    return None

def optimize_webm_for_opencv(input_file, output_file=None):
    """
    Tối ưu hóa WebM file để tương thích tốt nhất với OpenCV
    """
    if not check_ffmpeg_availability():
        logger.warning("FFmpeg not available for WebM optimization")
        return input_file
    
    if not output_file:
        file_dir = os.path.dirname(input_file)
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(file_dir, f"{file_name}_opencv.mp4")
    
    try:
        # Phát hiện codec hiện tại
        webm_info = detect_webm_codec(input_file)
        
        # Command tối ưu dựa trên codec phát hiện
        ffmpeg_cmd = get_ffmpeg_command()
        cmd = [
            ffmpeg_cmd, '-y', '-i', input_file,
            '-c:v', 'libx264',  # Force H.264 cho OpenCV
            '-preset', 'fast',
            '-crf', '25',
            '-pix_fmt', 'yuv420p',  # Pixel format tương thích
            '-an',  # Loại bỏ audio
        ]
        
        # Điều chỉnh FPS nếu cần
        if webm_info and webm_info.get('fps', 30) > 30:
            cmd.extend(['-r', '30'])
        
        # Điều chỉnh kích thước nếu quá lớn
        if webm_info and (webm_info.get('width', 0) > 1920 or webm_info.get('height', 0) > 1080):
            cmd.extend(['-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease'])
        
        cmd.append(output_file)
        
        logger.info(f"Optimizing WebM for OpenCV: {input_file} -> {output_file}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info(f"WebM optimization successful: {output_file}")
            return output_file
        else:
            logger.warning("WebM optimization failed - output file empty")
            return input_file
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg WebM optimization failed: {e.stderr}")
        return input_file
    except Exception as e:
        logger.error(f"WebM optimization error: {str(e)}")
        return input_file

def validate_webm_for_processing(webm_file):
    """
    Kiểm tra xem WebM file có thể được xử lý bởi OpenCV không
    """
    import cv2
    
    try:
        cap = cv2.VideoCapture(webm_file, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            return False
        
        # Thử đọc một frame
        ret, frame = cap.read()
        cap.release()
        
        return ret and frame is not None
    except Exception:
        return False

def prepare_webm_for_processing(webm_file):
    """
    Chuẩn bị WebM file để xử lý - convert nếu cần
    """
    logger.info(f"Preparing WebM file for processing: {webm_file}")
    
    # Kiểm tra xem có thể đọc trực tiếp không
    if validate_webm_for_processing(webm_file):
        logger.info("WebM file can be processed directly")
        return webm_file
    
    # Nếu không, optimize để tương thích
    logger.info("WebM file needs optimization for OpenCV")
    optimized_file = optimize_webm_for_opencv(webm_file)
    
    # Kiểm tra lại sau optimization
    if validate_webm_for_processing(optimized_file):
        logger.info("WebM optimization successful")
        return optimized_file
    else:
        logger.error("WebM optimization failed - OpenCV still cannot process")
        return webm_file
