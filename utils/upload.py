# utils/upload.py
import requests
import os
import tempfile
from typing import Optional

UPLOAD_VIDEO_URL = "https://upload.dananggo.com/api.php?action=upload_video"

def cleanup_local_video_file(file_path: str) -> bool:
    """
    Clean up local video file
    
    Args:
        file_path: Path to the video file to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.warning(f"Failed to cleanup local video file {file_path}: {e}")
        return False

def upload_video_to_host(video_file_path: str, cleanup_after_upload: bool = True) -> Optional[str]:
    """
    Upload video file to remote host
    
    Args:
        video_file_path: Path to the video file to upload
        cleanup_after_upload: Whether to delete local file after upload
        
    Returns:
        URL of uploaded video or None if failed
    """
    try:
        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"Video file not found: {video_file_path}")
        
        # Prepare form data
        with open(video_file_path, 'rb') as video_file:
            files = {'video': video_file}
            
            # Make upload request
            response = requests.post(
                UPLOAD_VIDEO_URL,
                files=files,
                timeout=120  # 2 minutes timeout
            )
            
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Parse response
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            # {'success': True, 'message': 'Upload video thành công', 'data': {'original_name': 'photobooth_result_f7a9c3ca-480b-4e3d-af69-e192981f234e.mp4', 'new_name': '688f8f0d88734_1754238733.mp4', 'size': '1.66 MB', 'type': 'video', 'url': 'videos/03_08_2025/688f8f0d88734_1754238733.mp4', 'upload_time': '2025-08-03 23:32:13', 'date_folder': '03_08_2025', 'applied_filter': 'none', 'quality': 85, 'enhancements': {'brightness': 100, 'contrast': 100, 'saturation': 100}}}
            result = result.get('data', {}) if isinstance(result, dict) else {}
            print(f"Upload response: {result.get('url', 'No URL found')}")
            # Extract video URL from response
            if isinstance(result, dict):
                # Assuming the API returns {"status": "success", "url": "video_url"}
                if result.get('status') == 'success' and 'url' in result:
                    return "https://upload.dananggo.com/"+result['url']
                elif 'url' in result:
                    return  "https://upload.dananggo.com/"+result['url']
            elif isinstance(result, str):
                # If response is just the URL as text
                if result.startswith('http'):
                    return result.strip()
            
            # Log response for debugging
            from utils.logging import setup_logging
            logger = setup_logging()
            logger.warning(f"Unexpected upload response: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.error(f"Upload request failed: {e}")
        return None
    except Exception as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.error(f"Upload error: {e}")
        return None
    finally:
        # Clean up local file after upload attempt (if requested)
        if cleanup_after_upload:
            try:
                if os.path.exists(video_file_path):
                    os.remove(video_file_path)
            except Exception as e:
                from utils.logging import setup_logging
                logger = setup_logging()
                logger.warning(f"Failed to cleanup local video file {video_file_path}: {e}")
