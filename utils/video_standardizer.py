"""
Module để chuẩn hóa video về định dạng h264+aac sử dụng ffmpeg
"""
import os
import subprocess
import sys
from pathlib import Path
import time
from utils.logging import setup_logging
from utils.ffmpeg_utils import get_ffmpeg_command, check_ffmpeg_availability

logger = setup_logging()

def standardize_video(input_file, output_file=None, crf=23, preset="fast"):
    """
    Chuẩn hóa video về định dạng h264+aac sử dụng ffmpeg.
    
    Args:
        input_file (str): Đường dẫn đến file video đầu vào
        output_file (str, optional): Đường dẫn đến file output. Nếu None, sẽ tự tạo.
        crf (int, optional): Constant Rate Factor cho h264 (18-28). Mặc định: 23.
        preset (str, optional): Preset của ffmpeg. Mặc định: "fast".
        
    Returns:
        str: Đường dẫn đến file đã chuẩn hóa, hoặc file gốc nếu có lỗi
    """
    if not check_ffmpeg_availability():
        logger.warning("FFmpeg không khả dụng để chuẩn hóa video")
        return input_file
    
    if not os.path.exists(input_file):
        logger.error(f"File input không tồn tại: {input_file}")
        return input_file
    
    # Tạo output file path nếu không được cung cấp
    if not output_file:
        file_dir = os.path.dirname(input_file)
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(file_dir, f"{file_name}_h264_aac.mp4")
    
    try:
        # Sử dụng ffmpeg để chuẩn hóa
        ffmpeg_cmd = get_ffmpeg_command()
        cmd = [
            ffmpeg_cmd, '-y', '-i', input_file,
            '-c:v', 'libx264',     # Video codec h264
            '-preset', preset,     # Preset cho cân bằng tốc độ và chất lượng
            '-crf', str(crf),      # Constant Rate Factor (18-28, thấp hơn = chất lượng cao hơn)
            '-pix_fmt', 'yuv420p', # Pixel format phổ biến nhất cho h264
            '-profile:v', 'high',  # Profile chất lượng cao
            '-level', '4.0',       # Level tương thích rộng
            '-movflags', '+faststart',  # Tối ưu cho web streaming
            '-c:a', 'aac',         # Audio codec AAC
            '-b:a', '192k',        # Bitrate audio hợp lý
            '-ac', '2',            # 2 audio channels (stereo)
            '-ar', '44100',        # Sample rate audio phổ biến
            output_file
        ]
        
        logger.info(f"Chuẩn hóa video h264+aac: {input_file} -> {output_file}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Kiểm tra file output
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info(f"Chuẩn hóa video thành công: {output_file}")
            # Xóa file video gốc nếu khác với output và không phải file gốc từ user
            if input_file != output_file and ("webm_" in os.path.basename(input_file) or "temp_" in os.path.basename(input_file) or "_opencv" in os.path.basename(input_file)):
                try:
                    os.remove(input_file)
                    logger.info(f"Đã xóa file tạm: {input_file}")
                except Exception as e:
                    logger.warning(f"Không thể xóa file tạm {input_file}: {e}")
            # Đảm bảo video output ổn định
            time.sleep(0.5)  # Đợi hệ thống file cập nhật
            return output_file
        else:
            logger.warning("Chuẩn hóa video thất bại - file output trống")
            return input_file
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi FFmpeg khi chuẩn hóa video: {e.stderr}")
        return input_file
    except Exception as e:
        logger.error(f"Lỗi khi chuẩn hóa video: {str(e)}")
        return input_file

def standardize_videos_in_batch(video_files, preset="fast", crf=23):
    """
    Chuẩn hóa nhiều video cùng lúc
    
    Args:
        video_files (list): Danh sách các đường dẫn video
        preset (str, optional): Preset của ffmpeg. Mặc định: "fast"
        crf (int, optional): Constant Rate Factor. Mặc định: 23
        
    Returns:
        list: Danh sách các đường dẫn video đã chuẩn hóa
    """
    standardized_files = []
    
    for video_file in video_files:
        standardized_file = standardize_video(video_file, preset=preset, crf=crf)
        standardized_files.append(standardized_file)
    
    return standardized_files

def verify_video_codec(video_file):
    """
    Kiểm tra xem video đã có codec h264+aac chưa
    
    Args:
        video_file (str): Đường dẫn đến file video
        
    Returns:
        bool: True nếu video đã chuẩn hóa, False nếu chưa
    """
    from utils.ffmpeg_utils import get_ffprobe_command, check_ffprobe_availability
    
    if not check_ffprobe_availability():
        logger.warning("FFprobe không khả dụng để kiểm tra codec")
        return False
    
    try:
        ffprobe_cmd = get_ffprobe_command()
        cmd = [
            ffprobe_cmd, '-v', 'quiet', '-print_format', 'json',
            '-show_streams', video_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        # Kiểm tra codec video
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        has_h264 = video_stream and video_stream.get('codec_name') == 'h264'
        
        # Kiểm tra codec audio
        audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
        has_aac = audio_stream and audio_stream.get('codec_name') == 'aac'
        
        return has_h264 and has_aac
    
    except Exception as e:
        logger.warning(f"Lỗi khi kiểm tra codec: {str(e)}")
        return False
