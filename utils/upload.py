# utils/upload.py
import requests
import os
import tempfile
from typing import Optional

UPLOAD_VIDEO_URL = "https://upload.dananggo.com/api.php?action=upload_video"
UPLOAD_IMAGE_URL = "https://upload.dananggo.com/api.php?action=upload_image"

def wait_for_file_completion(file_path: str, max_wait: int = 5) -> bool:
    """
    Wait for file to be completely written and available for reading
    
    Args:
        file_path: Path to the file to check
        max_wait: Maximum seconds to wait
        
    Returns:
        True if file is ready, False if timeout
    """
    import time
    
    for _ in range(max_wait * 2):  # Check every 0.5 seconds
        try:
            # Try to open file exclusively to check if it's still being written
            with open(file_path, 'rb') as f:
                # Try to read a small chunk to ensure file is readable
                f.read(1024)
            # If we get here, file is complete and readable
            return True
        except (IOError, OSError):
            # File is still being written or not accessible
            time.sleep(0.5)
            continue
    
    return False

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
        
        # Wait for file to be completely written
        if not wait_for_file_completion(video_file_path):
            from utils.logging import setup_logging
            logger = setup_logging()
            logger.warning(f"File may not be completely written: {video_file_path}")
        
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
            
            from utils.logging import setup_logging
            logger = setup_logging()
            logger.info(f"Upload video response: {result}")
            
            # Handle new API response format: {'success': True, 'data': {'url': '...'}}
            if isinstance(result, dict):
                if result.get('success') and 'data' in result:
                    # New format
                    data = result['data']
                    if 'url' in data:
                        video_url = "https://upload.dananggo.com/" + data['url']
                        logger.info(f"Video uploaded successfully: {video_url}")
                        return video_url
                elif result.get('status') == 'success' and 'url' in result:
                    # Old format
                    video_url = "https://upload.dananggo.com/" + result['url']
                    logger.info(f"Video uploaded successfully (old format): {video_url}")
                    return video_url
                elif 'url' in result:
                    # Direct URL in result
                    video_url = "https://upload.dananggo.com/" + result['url']
                    logger.info(f"Video uploaded successfully (direct URL): {video_url}")
                    return video_url
            elif isinstance(result, str):
                # If response is just the URL as text
                if result.startswith('http'):
                    logger.info(f"Video uploaded successfully (URL string): {result}")
                    return result.strip()
            
            # Log response for debugging
            logger.error(f"Unexpected upload response format: {result}")
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

def upload_image_to_host(image_file_path: str, cleanup_after_upload: bool = False) -> Optional[str]:
    """
    Upload image file to remote host
    
    Args:
        image_file_path: Path to the image file to upload
        cleanup_after_upload: Whether to delete local file after upload
        
    Returns:
        URL of uploaded image or None if failed
    """
    try:
        if not os.path.exists(image_file_path):
            raise FileNotFoundError(f"Image file not found: {image_file_path}")
        
        # Prepare form data
        with open(image_file_path, 'rb') as image_file:
            files = {'image': image_file}
            
            # Make upload request
            response = requests.post(
                UPLOAD_IMAGE_URL,
                files=files,
                timeout=60  # 1 minute timeout for images
            )
            
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Parse response
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            # Expecting similar format as video upload
            result = result.get('data', {}) if isinstance(result, dict) else {}
            
            from utils.logging import setup_logging
            logger = setup_logging()
            logger.info(f"Image upload response: {result.get('url', 'No URL found')}")
            
            # Extract image URL from response
            if isinstance(result, dict):
                if result.get('status') == 'success' and 'url' in result:
                    return "https://upload.dananggo.com/"+result['url']
                elif 'url' in result:
                    return "https://upload.dananggo.com/"+result['url']
            elif isinstance(result, str):
                # If response is just the URL as text
                if result.startswith('http'):
                    return result.strip()
            
            # Log response for debugging
            logger.warning(f"Unexpected image upload response: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.error(f"Image upload request failed: {e}")
        return None
    except Exception as e:
        from utils.logging import setup_logging
        logger = setup_logging()
        logger.error(f"Image upload error: {e}")
        return None
    finally:
        # Clean up local file after upload attempt (if requested)
        if cleanup_after_upload:
            try:
                if os.path.exists(image_file_path):
                    os.remove(image_file_path)
            except Exception as e:
                from utils.logging import setup_logging
                logger = setup_logging()
                logger.warning(f"Failed to cleanup local image file {image_file_path}: {e}")
