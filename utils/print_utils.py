import requests
import os
import uuid
import time
import socket  # Import socket module
import win32ui
import subprocess

import sys, os
try:
    import win32print
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to a public server to get local IP
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost if unable to get actual IP
def resource_path(relative_path):
    """Lấy đường dẫn thực khi chạy cả file .py và .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def _download_and_save_image(image_url):
    """Helper function to download and save an image."""
    start_time = time.time()
    response = requests.get(image_url)
    response.raise_for_status()

    file_extension = image_url.split('.')[-1]
    if '?' in file_extension:
        file_extension = file_extension.split('?')[0]
    if not file_extension or len(file_extension) > 5:
        file_extension = 'jpg'

    filename = f"{uuid.uuid4()}.{file_extension}"
    filepath = os.path.join('downloads', filename)

    with open(filepath, 'wb') as f:
        f.write(response.content)

    end_time = time.time()
    download_time = round(end_time - start_time, 2)
    return {"image_path": f"/downloads/{filename}", "download_time": download_time}


def print_image(image_path: str, printer_name: str = None, copies: int = 1) -> bool:
    """
    In ảnh bằng lệnh rundll32 shimgvw.dll,ImageView_PrintTo
    Hỗ trợ in nhiều bản (copies).
    """
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy ảnh: {image_path}")
        return False

    # Nếu không truyền printer_name thì lấy máy in mặc định
    if not printer_name:
        printer_name = win32print.GetDefaultPrinter()
        print(f"📌 Sử dụng máy in mặc định: {printer_name}")

    success_count = 0
    fail_count = 0

    for i in range(1, copies + 1):
        try:
            cmd = f"rundll32.exe C:\\Windows\\System32\\shimgvw.dll,ImageView_PrintTo /pt \"{image_path}\" \"{printer_name}\""

            completed = subprocess.run(cmd, shell=False)

            if completed.returncode == 0:
                print(f"✅ Lần {i}: In thành công.")
                success_count += 1
            else:
                print(f"❌ Lần {i}: Lỗi khi in (mã {completed.returncode}).")
                fail_count += 1

        except Exception as e:
            print(f"❌ Lần {i}: Lỗi khi in ảnh: {e}")
            fail_count += 1

    print(f"\n📊 Kết quả: {success_count}/{copies} bản in thành công, {fail_count} thất bại.")
    return success_count == copies
