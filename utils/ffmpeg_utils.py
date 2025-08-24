"""
Utility functions for managing FFmpeg/FFprobe paths across the application
"""

import os
import sys
import shutil
import platform

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

    return None


def _binary_name(name: str) -> str:
    """
    Trả về tên file nhị phân tuỳ theo OS.
    - Windows: ffmpeg.exe
    - Linux/Mac: ffmpeg
    """
    if platform.system().lower().startswith("win"):
        return f"{name}.exe"
    return name


def get_ffmpeg_path():
    """
    Lấy đường dẫn đến ffmpeg
    """
    bin_dir = get_ffmpeg_bin_dir()
    if bin_dir:
        ffmpeg_path = os.path.join(bin_dir, _binary_name("ffmpeg"))
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path

    # Nếu không tìm thấy thì fallback system PATH
    return shutil.which("ffmpeg")


def get_ffprobe_path():
    """
    Lấy đường dẫn đến ffprobe
    """
    bin_dir = get_ffmpeg_bin_dir()
    if bin_dir:
        ffprobe_path = os.path.join(bin_dir, _binary_name("ffprobe"))
        if os.path.exists(ffprobe_path):
            return ffprobe_path

    # Nếu không tìm thấy thì fallback system PATH
    return shutil.which("ffprobe")


def check_ffmpeg_availability():
    """Kiểm tra ffmpeg có khả dụng không"""
    return get_ffmpeg_path() is not None


def check_ffprobe_availability():
    """Kiểm tra ffprobe có khả dụng không"""
    return get_ffprobe_path() is not None


def get_ffmpeg_command():
    """Trả về command ffmpeg để gọi subprocess"""
    cmd = get_ffmpeg_path()
    if cmd is None:
        raise FileNotFoundError(
            "FFmpeg not found. Please install globally or add to 'ffmpeg/bin' folder."
        )
    return cmd


def get_ffprobe_command():
    """Trả về command ffprobe để gọi subprocess"""
    cmd = get_ffprobe_path()
    if cmd is None:
        raise FileNotFoundError(
            "FFprobe not found. Please install globally or add to 'ffmpeg/bin' folder."
        )
    return cmd
