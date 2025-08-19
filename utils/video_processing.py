# utils/video_processing.py
import sys
import cv2
import numpy as np
from PIL import Image
import uuid
import shutil
import subprocess
import os
import tempfile
import json
from pathlib import Path
from config import VIDEO_FPS, FAST_VIDEO_DURATION, OUTPUT_FOLDER, get_frame_margin, get_frame_gap, FRAME_TYPES, get_daily_folder
from .image_processing import fit_cover_image, calc_positions
from .ffmpeg_utils import get_ffmpeg_command, get_ffprobe_command, check_ffmpeg_availability, check_ffprobe_availability

def get_ffmpeg_path():
    """Deprecated: Use ffmpeg_utils.get_ffmpeg_command() instead"""
    try:
        return get_ffmpeg_command()
    except FileNotFoundError:
        if getattr(sys, 'frozen', False):  # Running from .exe
            return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        else:
            return os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')

def get_ffprobe_path():
    """Deprecated: Use ffmpeg_utils.get_ffprobe_command() instead"""
    try:
        return get_ffprobe_command()
    except FileNotFoundError:
        if getattr(sys, 'frozen', False):  # Running from .exe
            return os.path.join(sys._MEIPASS, 'ffprobe.exe')
        else:
            return os.path.join(os.path.dirname(__file__), 'ffprobe.exe')

def create_video_writer(output_file, fps, width, height):
    """
    Tạo VideoWriter với codec h264 (avc1) cho OpenCV
    """
    # Ưu tiên codec h264 (avc1) cho web compatibility tốt nhất
    # Chú ý: OpenCV chỉ tạo container, chuẩn hóa codec sẽ được thực hiện với ffmpeg sau
    codecs = ['avc1', 'h264', 'H264', 'mp4v', 'XVID', 'MJPG']
    
    for codec in codecs:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            if out.isOpened():
                print(f"[VIDEO] Successfully created VideoWriter with codec: {codec}")
                return out, codec
            else:
                out.release()
                print(f"[VIDEO] Failed to open VideoWriter with codec: {codec}")
        except Exception as e:
            print(f"[VIDEO] Exception with codec {codec}: {str(e)}")
            continue
    
    raise ValueError(f"Cannot create video output with any available codec. Tried: {codecs}")

def optimize_video_for_opencv(input_file):
    """
    Tối ưu hóa video đặc biệt cho OpenCV processing
    """
    if not check_ffmpeg_availability():
        return input_file
    
    try:
        # Kiểm tra info video trước
        video_info = get_video_info(input_file)
        if not video_info:
            return input_file
        
        file_dir = os.path.dirname(input_file)
        file_name = os.path.basename(input_file)
        file_name_no_ext = os.path.splitext(file_name)[0]
        optimized_file = os.path.join(file_dir, f"opencv_optimized_{file_name_no_ext}.mp4")
        
        # Command tối ưu cho OpenCV
        ffmpeg_cmd = get_ffmpeg_command()
        cmd = [
            ffmpeg_cmd, '-y', '-i', input_file,
            '-c:v', 'libx264',  # H.264 for best OpenCV compatibility
            '-preset', 'ultrafast',  # Faster encoding
            '-crf', '28',  # Balanced quality for processing
            '-pix_fmt', 'yuv420p',  # Pixel format OpenCV handles well
            '-r', str(min(video_info.get('fps', 30), 30)),  # Cap FPS at 30
            '-an',  # Remove audio for video processing
            optimized_file
        ]
        
        print(f"[VIDEO OPTIMIZE] Optimizing {input_file} for OpenCV...")
        subprocess.run(cmd, check=True, capture_output=True)
        
        if os.path.exists(optimized_file) and os.path.getsize(optimized_file) > 0:
            print(f"[VIDEO OPTIMIZE] Successfully optimized: {optimized_file}")
            return optimized_file
        
    except subprocess.CalledProcessError as e:
        print(f"[VIDEO OPTIMIZE] FFmpeg optimization failed: {e}")
        
    return input_file

def apply_background_and_overlay_video(frame, background_path, overlay_path, output_size, frame_type=None):
    scale_factor = min(1500 / max(output_size), 1.0) if max(output_size) > 2000 else 1.0
    working_size = (int(output_size[0] * scale_factor) & ~1, int(output_size[1] * scale_factor) & ~1)
    
    if scale_factor != 1.0:
        frame = cv2.resize(frame, working_size, interpolation=cv2.INTER_AREA)
    
    result = np.ones((working_size[1], working_size[0], 3), dtype=np.uint8) * 255
    
    if background_path and os.path.exists(background_path):
        bg = Image.open(background_path).convert("RGB")
        crop_direction = "top" if frame_type and (
            (frame_type.get("columns") == 1 and frame_type.get("rows") == 1 and not frame_type.get("isCircle", False)) or
            (frame_type.get("columns") == 2 and frame_type.get("rows") == 2)) else "center"
        bg = fit_cover_image(bg, working_size if scale_factor != 1.0 else output_size, crop_direction)
        result = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
    
    if frame.shape[2] == 4:
        frame_bgr = frame[:, :, :3]
        frame_alpha = frame[:, :, 3] / 255.0
        alpha_mask = np.repeat(frame_alpha[:, :, np.newaxis], 3, axis=2)
        result = ((1.0 - alpha_mask) * result + alpha_mask * frame_bgr).astype(np.uint8)
    else:
        result = frame.copy()
    
    if overlay_path and os.path.exists(overlay_path):
        overlay = Image.open(overlay_path).convert("RGBA")
        crop_direction = "top" if frame_type and (
            (frame_type.get("columns") == 1 and frame_type.get("rows") == 1 and not frame_type.get("isCircle", False)) or
            (frame_type.get("columns") == 2 and frame_type.get("rows") == 2)) else "center"
        overlay = fit_cover_image(overlay, working_size if scale_factor != 1.0 else output_size, crop_direction)
        overlay_np = np.array(overlay)
        if overlay_np.shape[2] == 4:
            overlay_rgb = overlay_np[:, :, :3]
            overlay_alpha = overlay_np[:, :, 3] / 255.0
            alpha_mask = np.repeat(overlay_alpha[:, :, np.newaxis], 3, axis=2)
            overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)
            result = ((1.0 - alpha_mask) * result + alpha_mask * overlay_bgr).astype(np.uint8)
    
    if scale_factor != 1.0:
        result = cv2.resize(result, output_size, interpolation=cv2.INTER_LINEAR)
    
    return result

def process_video_frame(frame, media, pos, size, is_circle, frame_type=None):
    scale_factor = min(1500 / max(media.shape[:2][::-1]), 1.0) if max(media.shape[:2]) > 2000 else 1.0
    if scale_factor != 1.0:
        media = cv2.resize(media, (int(media.shape[1] * scale_factor), int(media.shape[0] * scale_factor)), interpolation=cv2.INTER_AREA)
    
    scale_w = size[0] / media.shape[1]
    scale_h = size[1] / media.shape[0]
    scale = max(scale_w, scale_h)
    
    if scale != 1.0:
        new_size = (int(media.shape[1] * scale), int(media.shape[0] * scale))
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        media = cv2.resize(media, new_size, interpolation=interpolation)
    
    crop_left = crop_top = False
    if frame_type:
        if frame_type.get("columns") == 1 and frame_type.get("rows") == 1 and not frame_type.get("isCircle", False):
            crop_top = True
        elif frame_type.get("columns") == 2 and frame_type.get("rows") == 2:
            crop_top = True
    
    left = 0 if crop_left else (media.shape[1] - size[0]) // 2 if media.shape[1] > size[0] else 0
    top = 0 if crop_top else (media.shape[0] - size[1]) // 2 if media.shape[0] > size[1] else 0
    left = max(0, min(left, media.shape[1] - size[0]))
    top = max(0, min(top, media.shape[0] - size[1]))
    
    media = media[top:top + size[1], left:left + size[0]]
    if media.shape[:2] != (size[1], size[0]):
        media = cv2.resize(media, size, interpolation=cv2.INTER_LINEAR)
    
    if is_circle:
        mask = np.zeros((size[1], size[0]), dtype=np.uint8)
        cv2.circle(mask, (size[0]//2, size[1]//2), min(size)//2, 255, -1)
        alpha = np.zeros_like(mask)
        alpha[mask > 0] = 255
        rgba = cv2.cvtColor(media, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = alpha
        
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA) if frame.shape[2] == 3 else frame
        roi = frame_rgba[pos[1]:pos[1]+size[1], pos[0]:pos[0]+size[0]]
        for c in range(3):
            roi[:, :, c] = roi[:, :, c] * (1 - rgba[:, :, 3]/255.0) + rgba[:, :, c] * (rgba[:, :, 3]/255.0)
        roi[:, :, 3] = np.maximum(roi[:, :, 3], rgba[:, :, 3])
        return cv2.cvtColor(frame_rgba, cv2.COLOR_BGRA2BGR)
    
    frame[pos[1]:pos[1]+size[1], pos[0]:pos[0]+size[0]] = media
    return frame

def convert_webm_to_mp4(input_file):
    """
    Chuyển đổi file WebM sang MP4 để tăng tương thích với OpenCV
    và chuẩn hóa về định dạng h264+aac
    """
    if not input_file.lower().endswith('.webm'):
        # Nếu không phải WebM, vẫn chuẩn hóa về h264+aac
        from utils.video_standardizer import standardize_video
        return standardize_video(input_file)
    
    # Sử dụng WebM handler chuyên dụng trước
    from utils.webm_handler import prepare_webm_for_processing
    converted_file = prepare_webm_for_processing(input_file)
    
    # Sau đó chuẩn hóa thành h264+aac
    if converted_file != input_file:
        from utils.video_standardizer import standardize_video
        return standardize_video(converted_file)
    
    return converted_file

def get_video_info(video_path):
    """Lấy thông tin video bằng ffprobe"""
    if not check_ffprobe_availability():
        return None
        
    try:
        ffprobe_cmd = get_ffprobe_command()
        
        cmd = [
            ffprobe_cmd, '-v', 'quiet', '-print_format', 'json', 
            '-show_format', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        if not video_stream:
            return None
            
        return {
            'duration': float(video_stream.get('duration', data['format'].get('duration', 0))),
            'fps': eval(video_stream.get('r_frame_rate', '30/1')),
            'width': int(video_stream['width']),
            'height': int(video_stream['height'])
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None
 
def optimize_video(video_file):
    """Tối ưu hóa video với FFmpeg hoặc basic optimization nếu không có FFmpeg"""
    
    try:
        
        return video_file
        
    except Exception as e:
        print(f"Lỗi khi chuẩn hóa video: {str(e)}")
        return basic_video_optimization(video_file)

def basic_video_optimization(video_file):
    """
    Basic video optimization without FFmpeg
    Recreate video with more compatible settings
    """
    try:
        file_dir = os.path.dirname(video_file)
        file_name = os.path.basename(video_file)
        optimized_file = os.path.join(file_dir, f"basic_opt_{file_name}")
        
        print(f"Applying basic optimization: {video_file}")
        
        # Open original video
        cap = cv2.VideoCapture(video_file, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"Cannot open video for basic optimization: {video_file}")
            return video_file
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Ensure even dimensions for better codec compatibility
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1
        
        # Create output with web-compatible codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Most compatible
        out = cv2.VideoWriter(optimized_file, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print(f"Cannot create optimized video writer")
            cap.release()
            return video_file
        
        print(f"Processing {total_frames} frames for basic optimization...")
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Resize if needed
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
            
            out.write(frame)
            frame_count += 1
            
            if frame_count % 30 == 0:  # Progress every second at 30fps
                print(f"Processed {frame_count}/{total_frames} frames")
        
        cap.release()
        out.release()
        
        # Check if optimization was successful
        if os.path.exists(optimized_file) and os.path.getsize(optimized_file) > 0:
            if verify_video_file_integrity(optimized_file):
                print(f"Basic optimization successful: {optimized_file}")
                try:
                    os.replace(optimized_file, video_file)
                    print(f"Replaced original with basic optimized: {video_file}")
                    return video_file
                except OSError as e:
                    print(f"Failed to replace original file: {e}")
                    return optimized_file
            else:
                print(f"Basic optimized video failed integrity check")
                if os.path.exists(optimized_file):
                    os.remove(optimized_file)
        
        print(f"Basic optimization failed, using original: {video_file}")
        return video_file
        
    except Exception as e:
        print(f"Basic optimization error: {str(e)}")
        return video_file

def create_video_output(frame_type, video_files, background_path, overlay_path, total_width, total_height, duration=2, upload_to_host=True):
    frame_id = next((key for key, value in FRAME_TYPES.items() if
                     value["columns"] == frame_type["columns"] and
                     value["rows"] == frame_type["rows"] and
                     value.get("isCustom", False) == frame_type.get("isCustom", False)), None)
    
    margin = get_frame_margin(frame_id)
    gap = get_frame_gap(frame_id)
    photo_width, photo_height, positions = calc_positions(frame_type, total_width, total_height, margin, gap)
    
    scale_factor = min(1500 / max(total_width, total_height), 1.0) if max(total_width, total_height) > 2000 else 1.0
    output_width = int(total_width * scale_factor) & ~1
    output_height = int(total_height * scale_factor) & ~1
    scaled_positions = [(int(pos[0] * scale_factor), int(pos[1] * scale_factor)) for pos in positions]
    photo_width = int(photo_width * scale_factor)
    photo_height = int(photo_height * scale_factor)
    
    caps = [cv2.VideoCapture(video_file, cv2.CAP_FFMPEG) for video_file in video_files]
    
    # Optimize files for OpenCV if needed
    optimized_files = []
    for i, video_file in enumerate(video_files):
        if not caps[i].isOpened():
            print(f"[VIDEO] Failed to open {video_file}, trying optimization...")
            optimized_file = optimize_video_for_opencv(video_file)
            caps[i].release()
            caps[i] = cv2.VideoCapture(optimized_file, cv2.CAP_FFMPEG)
            optimized_files.append(optimized_file)
        else:
            optimized_files.append(video_file)
    
    if not all(cap.isOpened() for cap in caps):
        for cap in caps:
            cap.release()
        raise ValueError("Cannot open video files even after optimization!")
    
    fps = min([cap.get(cv2.CAP_PROP_FPS) or VIDEO_FPS for cap in caps])
    total_frames = int(duration * fps)
    # Tạo file trong daily folder trước khi upload
    daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
    temp_output_file = os.path.join(daily_output_folder, f"photobooth_result_{uuid.uuid4()}.mp4")
    
    # Sử dụng helper function để tạo VideoWriter với fallback codec
    try:
        out, used_codec = create_video_writer(temp_output_file, fps, output_width, output_height)
    except ValueError as e:
        for cap in caps:
            cap.release()
        raise e
    
    background_frame = None
    if background_path:
        bg = Image.open(background_path).convert("RGB")
        crop_direction = "top" if frame_type.get("columns") in [1, 2] and frame_type.get("rows") in [1, 2] else "center"
        bg = fit_cover_image(bg, (total_width, total_height), crop_direction)
        if scale_factor != 1.0:
            bg = bg.resize((output_width, output_height), Image.Resampling.LANCZOS)
        background_frame = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
    
    overlay_pil = None
    if overlay_path:
        overlay_pil = Image.open(overlay_path).convert("RGBA")
        crop_direction = "top" if frame_type.get("columns") in [1, 2] and frame_type.get("rows") in [1, 2] else "center"
        overlay_pil = fit_cover_image(overlay_pil, (total_width, total_height), crop_direction)
        if scale_factor != 1.0:
            overlay_pil = overlay_pil.resize((output_width, output_height), Image.Resampling.LANCZOS)
    
    last_valid_frames = [None] * len(caps)
    try:
        for _ in range(total_frames):
            frame = background_frame.copy() if background_frame is not None else np.ones((output_height, output_width, 3), dtype=np.uint8) * 255
            for idx, (cap, pos) in enumerate(zip(caps, scaled_positions)):
                ret, video_frame = cap.read()
                if not ret or video_frame is None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, video_frame = cap.read()
                if ret and video_frame is not None:
                    last_valid_frames[idx] = video_frame.copy()
                elif last_valid_frames[idx] is not None:
                    video_frame = last_valid_frames[idx]
                else:
                    continue
                frame = process_video_frame(frame, video_frame, pos, (photo_width, photo_height), frame_type.get("isCircle", False), frame_type)
            
            if overlay_pil:
                overlay_np = np.array(overlay_pil)
                if overlay_np.shape[2] == 4:
                    overlay_rgb = overlay_np[:, :, :3]
                    overlay_alpha = overlay_np[:, :, 3] / 255.0
                    overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)
                    for c in range(3):
                        frame[:, :, c] = frame[:, :, c] * (1 - overlay_alpha) + overlay_bgr[:, :, c] * overlay_alpha
            out.write(frame)
    finally:
        for cap in caps:
            cap.release()
        out.release()
        cv2.destroyAllWindows()  # Clean up any OpenCV windows
    
    # Đảm bảo file hoàn tất trước khi tối ưu và upload
    import time
    time.sleep(0.5)  # Wait for file to be completely written
    
    optimized_file = temp_output_file
    
    # Upload to host if requested
    if upload_to_host:
        # Kiểm tra tính toàn vẹn của file trước khi upload
        if not verify_video_file_integrity(optimized_file):
            print(f"Video file integrity check failed: {optimized_file}")
            return optimized_file  # Trả về local file nếu có vấn đề
        
        from utils.upload import upload_video_to_host
        uploaded_url = upload_video_to_host(optimized_file, cleanup_after_upload=True)  # Không xóa file local
        if uploaded_url:
            print(f"Video uploaded successfully: {uploaded_url}")
            return uploaded_url
        else:
            # Nếu upload thất bại, trả về đường dẫn local
            print(f"Upload failed, using local file: {optimized_file}")
            return optimized_file
    else:
        # Trả về đường dẫn local file
        return optimized_file

def create_fast_video_output(frame_type, video_files, background_path, overlay_path, total_width, total_height, original_duration=10, upload_to_host=True):
    frame_id = next((key for key, value in FRAME_TYPES.items() if
                     value["columns"] == frame_type["columns"] and
                     value["rows"] == frame_type["rows"] and
                     value.get("isCustom", False) == frame_type.get("isCustom", False)), None)
    
    margin = get_frame_margin(frame_id)
    gap = get_frame_gap(frame_id)
    photo_width, photo_height, positions = calc_positions(frame_type, total_width, total_height, margin, gap)
    
    scale_factor = min(1500 / max(total_width, total_height), 1.0) if max(total_width, total_height) > 2000 else 1.0
    output_width = int(total_width * scale_factor) & ~1
    output_height = int(total_height * scale_factor) & ~1
    scaled_positions = [(int(pos[0] * scale_factor), int(pos[1] * scale_factor)) for pos in positions]
    photo_width = int(photo_width * scale_factor)
    photo_height = int(photo_height * scale_factor)
    
    caps = [cv2.VideoCapture(video_file, cv2.CAP_FFMPEG) for video_file in video_files]
    
    # Optimize files for OpenCV if needed (fast video processing)
    optimized_files = []
    for i, video_file in enumerate(video_files):
        if not caps[i].isOpened():
            print(f"[FAST VIDEO] Failed to open {video_file}, trying optimization...")
            optimized_file = optimize_video_for_opencv(video_file)
            caps[i].release()
            caps[i] = cv2.VideoCapture(optimized_file, cv2.CAP_FFMPEG)
            optimized_files.append(optimized_file)
        else:
            optimized_files.append(video_file)
    
    if not all(cap.isOpened() for cap in caps):
        for cap in caps:
            cap.release()
        raise ValueError("Cannot open video files even after optimization!")
    
    fps = min([cap.get(cv2.CAP_PROP_FPS) or VIDEO_FPS for cap in caps])
    fast_duration = FAST_VIDEO_DURATION
    total_frames = int(fast_duration * fps)
    speed_multiplier = original_duration / fast_duration
    original_total_frames = int(original_duration * fps)
    
    # Tạo file trong daily folder trước khi upload
    daily_output_folder = get_daily_folder(OUTPUT_FOLDER)
    temp_output_file = os.path.join(daily_output_folder, f"photobooth_fast_{uuid.uuid4()}.mp4")
    
    # Sử dụng helper function để tạo VideoWriter với fallback codec
    try:
        out, used_codec = create_video_writer(temp_output_file, fps, output_width, output_height)
    except ValueError as e:
        for cap in caps:
            cap.release()
        raise e
    
    background_frame = None
    if background_path:
        bg = Image.open(background_path).convert("RGB")
        crop_direction = "top" if frame_type.get("columns") in [1, 2] and frame_type.get("rows") in [1, 2] else "center"
        bg = fit_cover_image(bg, (total_width, total_height), crop_direction)
        if scale_factor != 1.0:
            bg = bg.resize((output_width, output_height), Image.Resampling.LANCZOS)
        background_frame = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
    
    overlay_pil = None
    if overlay_path:
        overlay_pil = Image.open(overlay_path).convert("RGBA")
        crop_direction = "top" if frame_type.get("columns") in [1, 2] and frame_type.get("rows") in [1, 2] else "center"
        overlay_pil = fit_cover_image(overlay_pil, (total_width, total_height), crop_direction)
        if scale_factor != 1.0:
            overlay_pil = overlay_pil.resize((output_width, output_height), Image.Resampling.LANCZOS)
    
    last_valid_frames = [None] * len(caps)
    original_frame_indices = [min(int(frame_idx * speed_multiplier), original_total_frames - 1) for frame_idx in range(total_frames)]
    
    try:
        for frame_idx in original_frame_indices:
            frame = background_frame.copy() if background_frame is not None else np.ones((output_height, output_width, 3), dtype=np.uint8) * 255
            for idx, (cap, pos) in enumerate(zip(caps, scaled_positions)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, video_frame = cap.read()
                if not ret or video_frame is None:
                    if frame_idx > 0:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1)
                        ret, video_frame = cap.read()
                    if not ret or video_frame is None:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, video_frame = cap.read()
                    if not ret and last_valid_frames[idx] is not None:
                        video_frame = last_valid_frames[idx]
                    elif not ret:
                        continue
                last_valid_frames[idx] = video_frame.copy()
                frame = process_video_frame(frame, video_frame, pos, (photo_width, photo_height), frame_type.get("isCircle", False), frame_type)
            
            if overlay_pil:
                overlay_np = np.array(overlay_pil)
                if overlay_np.shape[2] == 4:
                    overlay_rgb = overlay_np[:, :, :3]
                    overlay_alpha = overlay_np[:, :, 3] / 255.0
                    overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)
                    for c in range(3):
                        frame[:, :, c] = frame[:, :, c] * (1 - overlay_alpha) + overlay_bgr[:, :, c] * overlay_alpha
            out.write(frame)
    finally:
        for cap in caps:
            cap.release()
        out.release()
        cv2.destroyAllWindows()  # Clean up any OpenCV windows
    
    # Đảm bảo file hoàn tất trước khi tối ưu và upload  
    import time
    time.sleep(0.5)  # Wait for file to be completely written
    
    optimized_file = temp_output_file
    
    # Upload to host if requested
    if upload_to_host:
        # Kiểm tra tính toàn vẹn của file trước khi upload
        if not verify_video_file_integrity(optimized_file):
            print(f"Fast video file integrity check failed: {optimized_file}")
            return optimized_file  # Trả về local file nếu có vấn đề
        
        from utils.upload import upload_video_to_host
        uploaded_url = upload_video_to_host(optimized_file, cleanup_after_upload=True)  # Không xóa file local
        if uploaded_url:
            print(f"Fast video uploaded successfully: {uploaded_url}")
            return uploaded_url
        else:
            # Nếu upload thất bại, trả về đường dẫn local
            print(f"Fast video upload failed, using local file: {optimized_file}")
            return optimized_file
    else:
        # Trả về đường dẫn local file
        print(f"Local fast video created: {optimized_file}")
        return optimized_file

def verify_video_file_integrity(video_file_path):
    """
    Kiểm tra tính toàn vẹn của file video trước khi upload
    """
    try:
        import cv2
        
        if not os.path.exists(video_file_path):
            return False
        
        # Kiểm tra kích thước file
        if os.path.getsize(video_file_path) == 0:
            return False
        
        # Thử mở video với OpenCV
        cap = cv2.VideoCapture(video_file_path, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap.release()
            return False
        
        # Thử đọc vài frame đầu
        frame_count = 0
        for _ in range(5):  # Kiểm tra 5 frame đầu
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_count += 1
            else:
                break
        
        cap.release()
        
        # Video hợp lệ nếu có ít nhất 1 frame
        return frame_count > 0
        
    except Exception as e:
        print(f"Video integrity check failed: {e}")
        return False

def process_video_task(frame_type, video_files, background_path, overlay_path, total_width, total_height, duration=2, upload_to_host=True):
    try:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.info(f"Starting video processing task - duration: {duration}s, upload: {upload_to_host}")
        
        result = create_video_output(frame_type, video_files, background_path, overlay_path, total_width, total_height, duration, upload_to_host)
        
        if result:
            logger.info(f"Video processing completed successfully: {result}")
        else:
            logger.error("Video processing returned None result")
        
        return result
    except Exception as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.error(f"[VIDEO PROCESSING TASK] Error: {str(e)}")
        return None

def process_fast_video_task(frame_type, video_files, background_path, overlay_path, total_width, total_height, original_duration=10, upload_to_host=True):
    try:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.info(f"Starting fast video processing task - original duration: {original_duration}s, upload: {upload_to_host}")
        
        result = create_fast_video_output(frame_type, video_files, background_path, overlay_path, total_width, total_height, original_duration, upload_to_host)
        
        if result:
            logger.info(f"Fast video processing completed successfully: {result}")
        else:
            logger.error("Fast video processing returned None result")
            
        return result
    except Exception as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.error(f"[FAST VIDEO PROCESSING TASK] Error: {str(e)}")
        return None