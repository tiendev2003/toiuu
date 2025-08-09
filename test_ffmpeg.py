#!/usr/bin/env python3
"""
Test script để kiểm tra FFmpeg có hoạt động không
"""
import sys
import os

# Thêm thư mục hiện tại vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.ffmpeg_utils import (
    get_ffmpeg_path, 
    get_ffprobe_path, 
    check_ffmpeg_availability, 
    check_ffprobe_availability,
    get_ffmpeg_command,
    get_ffprobe_command
)

def test_ffmpeg():
    print("=== FFmpeg Test ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {current_dir}")
    
    # Test FFmpeg path
    print("\n--- FFmpeg Path Test ---")
    ffmpeg_path = get_ffmpeg_path()
    print(f"FFmpeg path: {ffmpeg_path}")
    
    if ffmpeg_path:
        print(f"FFmpeg exists: {os.path.exists(ffmpeg_path) if ffmpeg_path != 'ffmpeg' else 'Using system PATH'}")
    
    # Test FFprobe path  
    print("\n--- FFprobe Path Test ---")
    ffprobe_path = get_ffprobe_path()
    print(f"FFprobe path: {ffprobe_path}")
    
    if ffprobe_path:
        print(f"FFprobe exists: {os.path.exists(ffprobe_path) if ffprobe_path != 'ffprobe' else 'Using system PATH'}")
    
    # Test availability
    print("\n--- Availability Test ---")
    print(f"FFmpeg available: {check_ffmpeg_availability()}")
    print(f"FFprobe available: {check_ffprobe_availability()}")
    
    # Test commands
    print("\n--- Command Test ---")
    try:
        ffmpeg_cmd = get_ffmpeg_command()
        print(f"FFmpeg command: {ffmpeg_cmd}")
    except Exception as e:
        print(f"FFmpeg command error: {e}")
    
    try:
        ffprobe_cmd = get_ffprobe_command()
        print(f"FFprobe command: {ffprobe_cmd}")
    except Exception as e:
        print(f"FFprobe command error: {e}")
    
    # Test actual execution
    print("\n--- Execution Test ---")
    try:
        import subprocess
        ffmpeg_cmd = get_ffmpeg_command()
        result = subprocess.run([ffmpeg_cmd, '-version'], capture_output=True, text=True, timeout=10)
        print(f"FFmpeg version test - Return code: {result.returncode}")
        if result.returncode == 0:
            lines = result.stdout.split('\n')[:3]  # First 3 lines
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"FFmpeg execution error: {e}")

if __name__ == "__main__":
    test_ffmpeg()
