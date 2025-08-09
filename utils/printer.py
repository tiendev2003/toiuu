# utils/printer.py
import requests
import socket
import time
import base64
import subprocess
import json
import platform
from typing import List, Dict, Optional, Any
from utils.logging import setup_logging
from config import PRINT_SERVER_IP, PRINT_SERVER_PORT, PRINT_API_ENDPOINT, PRINT_LIST_ENDPOINT, PRINTER_CACHE_TIMEOUT

logger = setup_logging()

# Cache cho danh sách máy in
_printer_cache = {
    'printers': [],
    'last_updated': 0
}

import win32print
import win32ui
from PIL import Image, ImageWin
import os

def print_image(image_path: str, printer_name: str = None):
    """In ảnh với tên máy in cụ thể. Tự động xoay và canh giữa ảnh."""

    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy ảnh: {image_path}")
        return False

    try:
        # Mở ảnh và lấy kích thước
        img = Image.open(image_path)
        img_width, img_height = img.size

        print(f"🖼️ Ảnh: {image_path} ({img_width}x{img_height}px)")

        # Nếu không có tên máy in, dùng mặc định
        if not printer_name:
            printer_name = win32print.GetDefaultPrinter()

        print(f"🖨️ Máy in: {printer_name}")

        # Tạo DC (Device Context)
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)

        # Kích thước giấy in thực tế
        printable_width = hDC.GetDeviceCaps(8)   # HORZRES
        printable_height = hDC.GetDeviceCaps(10) # VERTRES
        print(f"📄 Vùng in: {printable_width}x{printable_height}px")

        # --- Xoay ảnh nếu cần ---
        img_is_portrait = img_height > img_width
        paper_is_portrait = printable_height > printable_width
        if img_is_portrait != paper_is_portrait:
            print("🔄 Đang xoay ảnh 90 độ...")
            img = img.rotate(90, expand=True)
            img_width, img_height = img.size
            print(f"🔁 Ảnh sau khi xoay: {img_width}x{img_height}px")

        # --- Tính kích thước phù hợp để không bị méo ---
        img_aspect = img_width / img_height
        paper_aspect = printable_width / printable_height

        if img_aspect > paper_aspect:
            new_width = printable_width
            new_height = int(new_width / img_aspect)
        else:
            new_height = printable_height
            new_width = int(new_height * img_aspect)

        # Căn giữa ảnh
        x_offset = (printable_width - new_width) // 2
        y_offset = (printable_height - new_height) // 2

        print(f"📐 Kích thước in: {new_width}x{new_height}px | Căn giữa: ({x_offset}, {y_offset})")

        # In
        hDC.StartDoc(image_path)
        hDC.StartPage()
        dib = ImageWin.Dib(img)
        draw_rect = (x_offset, y_offset, x_offset + new_width, y_offset + new_height)
        dib.draw(hDC.GetHandleOutput(), draw_rect)
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()

        print("✅ In thành công.")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi in ảnh: {e}")
        return False



def get_local_ip() -> str:
    """Lấy IP hiện tại của máy"""
    try:
        # Kết nối đến một địa chỉ bên ngoài để lấy IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.error(f"Cannot get local IP: {str(e)}")
        return "127.0.0.1"

def is_print_server() -> bool:
    """Kiểm tra xem máy hiện tại có phải là máy chủ in không"""
    local_ip = get_local_ip()
    is_server = local_ip == PRINT_SERVER_IP
    logger.info(f"Local IP: {local_ip}, Print Server IP: {PRINT_SERVER_IP}, Is Print Server: {is_server}")
    return is_server

def get_system_printers() -> List[Dict[str, Any]]:
    """
    Lấy danh sách máy in từ hệ thống sử dụng commands
    Hỗ trợ Windows (PowerShell), macOS và Linux
    """
    system = platform.system().lower()
    printers = []
    
    try:
        if system == "windows":
            # Sử dụng PowerShell Get-Printer
            cmd = ["powershell", "-Command", "Get-Printer | ConvertTo-Json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    printer_data = json.loads(result.stdout)
                    # Xử lý trường hợp chỉ có 1 máy in (không phải array)
                    if isinstance(printer_data, dict):
                        printer_data = [printer_data]
                    
                    for printer in printer_data:
                        status = "ready" if printer.get("PrinterStatus") == 0 else "busy"
                        printers.append({
                            "name": printer.get("Name", "Unknown"),
                            "id": printer.get("Name", "unknown").lower().replace(" ", "_"),
                            "status": status,
                            "type": printer.get("DriverName", "unknown"),
                            "paper_size": "4x6",  # Default
                            "location": printer.get("Location", ""),
                            "comment": printer.get("Comment", ""),
                            "shared": printer.get("Shared", False)
                        })
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse PowerShell printer data: {e}")
                    
        elif system == "darwin":  # macOS
            # Sử dụng lpstat để lấy danh sách máy in
            cmd = ["lpstat", "-p"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith("printer"):
                        parts = line.split()
                        if len(parts) >= 2:
                            printer_name = parts[1]
                            status = "ready" if "idle" in line.lower() else "busy"
                            printers.append({
                                "name": printer_name,
                                "id": printer_name.lower().replace(" ", "_"),
                                "status": status,
                                "type": "cups",
                                "paper_size": "4x6"
                            })
                            
        elif system == "linux":
            # Sử dụng lpstat cho Linux
            cmd = ["lpstat", "-p"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith("printer"):
                        parts = line.split()
                        if len(parts) >= 2:
                            printer_name = parts[1]
                            status = "ready" if "idle" in line.lower() else "busy"
                            printers.append({
                                "name": printer_name,
                                "id": printer_name.lower().replace(" ", "_"),
                                "status": status,
                                "type": "cups",
                                "paper_size": "4x6"
                            })
        
        logger.info(f"Found {len(printers)} system printers using {system} commands")
        return printers
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout getting system printers")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running printer command: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting system printers: {e}")
        return []

def get_printers_list(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Lấy danh sách máy in từ cache hoặc từ hệ thống
    Args:
        force_refresh: Bắt buộc refresh cache
    Returns:
        List of printer dictionaries
    """
    current_time = time.time()
    
    # Kiểm tra cache
    if not force_refresh and _printer_cache['printers'] and (current_time - _printer_cache['last_updated']) < PRINTER_CACHE_TIMEOUT:
        logger.info("Using cached printer list")
        return _printer_cache['printers']
    
    # Nếu không phải máy chủ in, trả về danh sách rỗng
    if not is_print_server():
        logger.warning("Not a print server, cannot get printer list")
        return []
    
    # Thử lấy từ hệ thống trước
    printers = get_system_printers()
    
    # Nếu không lấy được từ hệ thống, thử API
    if not printers:
        try:
            logger.info("Trying to get printers from API...")
            response = requests.get(f"http://localhost:{PRINT_SERVER_PORT}{PRINT_LIST_ENDPOINT}", timeout=5)
            if response.status_code == 200:
                api_printers = response.json().get('printers', [])
                if api_printers:
                    printers = api_printers
                    logger.info(f"Retrieved {len(printers)} printers from API")
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed: {e}")
    
    # Nếu vẫn không có, sử dụng fallback
    if not printers:
        logger.info("Using fallback printer list")
        printers = [
            {
                "name": "DNP DS620A",
                "id": "dnp_ds620a",
                "status": "ready",
                "type": "thermal",
                "paper_size": "4x6"
            },
            {
                "name": "Canon Selphy CP1500", 
                "id": "canon_cp1500",
                "status": "ready",
                "type": "dye_sublimation",
                "paper_size": "4x6"
            }
        ]
    
    # Cập nhật cache
    _printer_cache['printers'] = printers
    _printer_cache['last_updated'] = current_time
    
    return printers

def send_print_job_system(image_path: str, printer_name: str, copies: int = 1, paper_size: str = "4x6") -> Dict[str, Any]:
    """
    Gửi lệnh in trực tiếp qua hệ thống (PowerShell trên Windows, lp trên Unix)
    Args:
        image_path: Đường dẫn đến file ảnh cần in
        printer_name: Tên máy in
        copies: Số bản in
        paper_size: Kích thước giấy
    Returns:
        Dict chứa kết quả in
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Sử dụng rundll32 để in trên Windows
            result = print_image(image_path, printer_name)
            if result:
                return {
                    "success": True,
                    "job_id": f"win_print_{int(time.time())}",
                    "message": "Print job sent via Windows command",
                    "printer": printer_name,
                    "copies": copies
                }
            else:
                return {
                    "success": False,
                    "error": "windows_print_failed",
                    "message": "Failed to print image on Windows"
                }
            
            
                
        elif system in ["darwin", "linux"]:  # macOS và Linux
            # Sử dụng lp command
            cmd = ["lp", "-d", printer_name, "-n", str(copies), image_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # lp trả về job ID trong stdout
                output = result.stdout.strip()
                job_id = output.split()[-1] if output else f"unix_print_{int(time.time())}"
                logger.info(f"Unix print job sent successfully: {output}")
                return {
                    "success": True,
                    "job_id": job_id,
                    "message": "Print job sent via CUPS",
                    "printer": printer_name,
                    "copies": copies,
                    "system_output": output
                }
            else:
                error_msg = result.stderr.strip() or "Unknown Unix print error"
                logger.error(f"Unix print failed: {error_msg}")
                return {
                    "success": False,
                    "error": "unix_print_failed",
                    "message": error_msg
                }
        else:
            return {
                "success": False,
                "error": "unsupported_system",
                "message": f"System {system} not supported for direct printing"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "print_timeout",
            "message": "Print command timed out"
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": "print_command_failed",
            "message": f"Print command failed: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": "unexpected_error",
            "message": f"Unexpected error: {e}"
        }

def send_print_job_to_server(image_path: str, printer_name: str="DS-RX1", copies: int = 1, paper_size: str = "4x6") -> Dict[str, Any]:
    """
    Gửi lệnh in đến máy chủ in qua API (gửi file thay vì URL)
    Args:
        image_path: Đường dẫn đến file ảnh cần in
        printer_name: Tên máy in
        copies: Số bản in
        paper_size: Kích thước giấy
    Returns:
        Dict chứa kết quả in
    """
    try:
        import os
        image_filename = os.path.basename(image_path)
        # Kiểm tra file tồn tại trước khi gửi
        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "file_not_found",
                "message": error_msg
            }
        # Luôn gửi file thực tế qua API
        form_data = {
            "printer_name": printer_name if printer_name else "DS-RX1",
            "copies": str(copies),
            "paper_size": paper_size
        }
        with open(image_path, 'rb') as image_file:
            files = {'image_file': (image_filename, image_file, 'image/jpeg')}
            logger.info(f"Sending print request to server with file: {image_filename}, printer: {printer_name}")
            response = requests.post(
                f"http://{PRINT_SERVER_IP}:{PRINT_SERVER_PORT}{PRINT_API_ENDPOINT}",
                data=form_data,
                files=files,
                timeout=30
            )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Print job sent to server successfully: {result}")
            return {
                "success": True,
                "job_id": result.get("job_id"),
                "message": "Print job sent to print server",
                "printer": printer_name,
                "copies": copies,
                "server_response": result
            }
        else:
            error_msg = f"Print server API failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "print_server_api_failed",
                "message": error_msg
            }
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error sending print job to server: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": "network_error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error sending print job to server: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": "unexpected_error",
            "message": error_msg
        }

def send_print_job(image_path: str, printer_name: str, copies: int = 1, paper_size: str = "4x6") -> Dict[str, Any]:
    """
    Gửi lệnh in tới máy in
    Thử system command trước, nếu thất bại thì dùng API
    Args:
        image_path: Đường dẫn đến file ảnh cần in
        printer_name: Tên máy in
        copies: Số bản in
        paper_size: Kích thước giấy
    Returns:
        Dict chứa kết quả in
    """
    if not is_print_server():
        return {
            "success": False,
            "error": "not_print_server",
            "message": "Current machine is not configured as print server"
        }
    
    # Thử in qua system command trước
    logger.info(f"Attempting system print: {image_path} to {printer_name}")
    result = send_print_job_system(image_path, printer_name, copies, paper_size)
    
    if result["success"]:
        logger.info("System print successful")
        return result
    
    # Nếu system print thất bại, thử API
    logger.warning(f"System print failed: {result.get('message')}, trying API...")
    
    try:
        # Đọc file ảnh và encode base64
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Chuẩn bị payload
        print_payload = {
            "printer_name": printer_name,
            "image_data": image_data,
            "copies": copies,
            "paper_size": paper_size,
            "color_mode": "color",
            "quality": "high"
        }
        
        # Gửi lệnh in qua API
        response = requests.post(
            f"http://localhost:{PRINT_SERVER_PORT}{PRINT_API_ENDPOINT}",
            json=print_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"API print job sent successfully: {result}")
            return {
                "success": True,
                "job_id": result.get("job_id"),
                "message": "Print job sent via API",
                "printer": printer_name,
                "copies": copies
            }
        else:
            error_msg = f"API print job failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "api_print_failed",
                "message": error_msg
            }
    
    except FileNotFoundError:
        error_msg = f"Image file not found: {image_path}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": "file_not_found",
            "message": error_msg
        }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error sending print job: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": "network_error",
            "message": error_msg
        }
    
    except Exception as e:
        error_msg = f"Unexpected error sending print job: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": "unexpected_error",
            "message": error_msg
        }

def get_print_status(job_id: str) -> Dict[str, Any]:
    """
    Kiểm tra trạng thái công việc in
    Args:
        job_id: ID của công việc in
    Returns:
        Dict chứa trạng thái in
    """
    if not is_print_server():
        return {
            "success": False,
            "error": "not_print_server"
        }
    
    try:
        response = requests.get(
            f"http://localhost:{PRINT_SERVER_PORT}/api/print-status/{job_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"Status check failed: {response.status_code}"
            }
    
    except Exception as e:
        logger.error(f"Error checking print status: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
