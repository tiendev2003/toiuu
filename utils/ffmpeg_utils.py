"""
Utility functions for managing FFmpeg/FFprobe paths across the application
"""

import os
import sys
import shutil

def get_ffmpeg_bin_dir():
    """
    Lấy đường dẫn thư mục ffmpeg/bin tùy theo môi trường.
    """
    if getattr(sys, 'frozen', False):
        # Nếu chạy từ .exe (PyInstaller), file nhúng nằm trong _MEIPASS
        return os.path.join(sys._MEIPASS, 'ffmpeg', 'bin')
    
    # Nếu chạy từ source
    project_root = os.path.dirname(os.path.dirname(__file__))  # ../
    bin_path = os.path.join(project_root, 'ffmpeg', 'bin')
    if os.path.isdir(bin_path):
        return bin_path

    # Tìm trong thư mục utils/ffmpeg/bin
    utils_dir = os.path.dirname(__file__)  # utils/
    bin_path = os.path.join(utils_dir, 'ffmpeg', 'bin')
    if os.path.isdir(bin_path):
        return bin_path
        
    # Trên Linux, thử tìm ở các thư mục hệ thống phổ biến
    if sys.platform != 'win32':
        for path in ['/usr/bin', '/usr/local/bin', '/opt/homebrew/bin']:
            if os.path.exists(os.path.join(path, 'ffmpeg')):
                return path

    return None

def get_ffmpeg_path():
    """
    Lấy đường dẫn đến ffmpeg (Windows: ffmpeg.exe, Linux/Mac: ffmpeg)
    """
    bin_dir = get_ffmpeg_bin_dir()
    if bin_dir:
        # Check platform and use appropriate executable name
        executable_name = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'
        ffmpeg_path = os.path.join(bin_dir, executable_name)
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path

    # Nếu không tìm thấy thì fallback system PATH
    return shutil.which('ffmpeg')

def get_ffprobe_path():
    """
    Lấy đường dẫn đến ffprobe (Windows: ffprobe.exe, Linux/Mac: ffprobe)
    """
    bin_dir = get_ffmpeg_bin_dir()
    if bin_dir:
        # Check platform and use appropriate executable name
        executable_name = 'ffprobe.exe' if sys.platform == 'win32' else 'ffprobe'
        ffprobe_path = os.path.join(bin_dir, executable_name)
        if os.path.exists(ffprobe_path):
            return ffprobe_path

    # Nếu không tìm thấy thì fallback system PATH
    return shutil.which('ffprobe')

def check_ffmpeg_availability():
    """
    Kiểm tra ffmpeg có khả dụng không
    """
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        # Kiểm tra quyền thực thi trên Linux/Mac
        if sys.platform != 'win32':
            try:
                ensure_executable(ffmpeg_path)
            except Exception as e:
                print(f"Không thể đặt quyền thực thi cho ffmpeg: {e}")
        return True
    return False

def check_ffprobe_availability():
    """
    Kiểm tra ffprobe có khả dụng không
    """
    ffprobe_path = get_ffprobe_path()
    if ffprobe_path and os.path.exists(ffprobe_path):
        # Kiểm tra quyền thực thi trên Linux/Mac
        if sys.platform != 'win32':
            try:
                ensure_executable(ffprobe_path)
            except Exception as e:
                print(f"Không thể đặt quyền thực thi cho ffprobe: {e}")
        return True
    return False

def ensure_executable(file_path):
    """
    Đảm bảo file có quyền thực thi trên Linux/Mac
    """
    if sys.platform != 'win32' and os.path.exists(file_path):
        current_mode = os.stat(file_path).st_mode
        executable_mode = current_mode | 0o111  # Thêm quyền thực thi cho user, group, other
        if current_mode != executable_mode:
            try:
                os.chmod(file_path, executable_mode)
                print(f"Đã đặt quyền thực thi cho {file_path}")
            except PermissionError:
                print(f"Không đủ quyền để đặt quyền thực thi cho {file_path}")
                print(f"Vui lòng chạy: chmod +x {file_path}")
                # Không raise lỗi ở đây, nó sẽ được xử lý ở caller

def get_ffmpeg_command():
    """
    Trả về command ffmpeg để gọi subprocess
    """
    cmd = get_ffmpeg_path()
    if cmd is None:
        # Trên Linux, thử tìm trực tiếp trong PATH
        if sys.platform != 'win32':
            cmd = shutil.which('ffmpeg')
            if cmd:
                return cmd
        raise FileNotFoundError("FFmpeg not found. Please install or add to 'ffmpeg/bin' folder.")
    return cmd

def get_ffprobe_command():
    """
    Trả về command ffprobe để gọi subprocess
    """
    cmd = get_ffprobe_path()
    if cmd is None:
        # Trên Linux, thử tìm trực tiếp trong PATH
        if sys.platform != 'win32':
            cmd = shutil.which('ffprobe')
            if cmd:
                return cmd
        raise FileNotFoundError("FFprobe not found. Please install or add to 'ffmpeg/bin' folder.")
    return cmd
