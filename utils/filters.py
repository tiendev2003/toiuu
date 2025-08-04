# utils/filters.py
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw
import numpy as np

FILTERS = {
    "none": {},
    "soft": {"brightness": 1.05, "contrast": 0.95, "saturation": 0.95},
    "bright": {"brightness": 1.10, "contrast": 0.90, "saturation": 1.05},
    "glow": {"brightness": 1.10, "contrast": 1.10, "saturation": 1.10},
    "smooth": {"brightness": 1.05, "contrast": 0.90, "saturation": 0.95, "blur": 0.2},
    "vintage": {"sepia": 0.8, "brightness": 0.65, "contrast": 1.5, "saturation": 0.55},
    "hdr": {"brightness": 1.05, "contrast": 1.3, "saturation": 1.15, "hue_rotate": 5},
    "clarity": {"brightness": 1.05, "contrast": 1.2, "saturation": 1.0, "sharpness": 1.5},
    "vivid": {"brightness": 1.1, "contrast": 1.15, "saturation": 1.4, "hue_rotate": 2},
    "noir": {"grayscale": 0.8, "brightness": 1.05, "contrast": 1.4},
    "dreamy": {"brightness": 1.05, "contrast": 0.95, "saturation": 0.9, "blur": 0.5, "hue_rotate": 5},
}

def apply_filter_to_image(img, filter_id):
    if filter_id not in FILTERS:
        return img
    
    filter_params = FILTERS[filter_id]
    has_alpha = img.mode == 'RGBA'
    alpha_channel = img.split()[3] if has_alpha else None
    img = img.convert("RGB")
    
    # Cache các enhancer objects để tránh tạo lại
    if "sepia" in filter_params:
        img = apply_sepia(img, filter_params["sepia"])
    
    # Áp dụng các enhancement một cách tuần tự và hiệu quả
    enhancements = []
    if "brightness" in filter_params:
        enhancements.append(('brightness', filter_params["brightness"]))
    if "contrast" in filter_params:
        enhancements.append(('contrast', filter_params["contrast"]))
    if "saturation" in filter_params:
        enhancements.append(('saturation', filter_params["saturation"]))
    if "sharpness" in filter_params:
        enhancements.append(('sharpness', filter_params["sharpness"]))
    
    # Áp dụng tất cả enhancement cùng lúc
    for enhancement_type, value in enhancements:
        if enhancement_type == 'brightness':
            img = ImageEnhance.Brightness(img).enhance(value)
        elif enhancement_type == 'contrast':
            img = ImageEnhance.Contrast(img).enhance(value)
        elif enhancement_type == 'saturation':
            img = ImageEnhance.Color(img).enhance(value)
        elif enhancement_type == 'sharpness':
            img = ImageEnhance.Sharpness(img).enhance(value)
    
    # Blur được áp dụng cuối cùng để tránh làm mờ các enhancement khác
    if "blur" in filter_params:
        img = img.filter(ImageFilter.GaussianBlur(radius=filter_params["blur"]))
    
    if has_alpha:
        img = Image.merge("RGBA", (*img.split(), alpha_channel))
    
    return img

def apply_sepia(img, intensity=1.0):
    img_array = np.array(img)
    sepia_matrix = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    sepia_img = np.dot(img_array[..., :3], sepia_matrix.T)
    sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
    return Image.fromarray(sepia_img)