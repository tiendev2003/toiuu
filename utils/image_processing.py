# utils/image_processing.py
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
from config import FRAME_TYPES, ASPECT_RATIOS, HEIGHT_IMAGE, WIDTH_IMAGE, HEIGHT_IMAGE_CUSTOM
from .file_handling import save_file

def get_frame_type(choice):
    try:
        return FRAME_TYPES[str(choice)]
    except KeyError:
        raise ValueError("Invalid frame type!")

def get_frame_size(frame_type):
    if frame_type["isCustom"]:
        return HEIGHT_IMAGE_CUSTOM, WIDTH_IMAGE
    if frame_type["columns"] == 1 and frame_type["rows"] == 1 and not frame_type.get("isCircle", False):
        return WIDTH_IMAGE, HEIGHT_IMAGE
    if frame_type["columns"] == 2 and frame_type["rows"] == 2:
        return WIDTH_IMAGE, HEIGHT_IMAGE
    # Frame 1x2 ngang (giống như nửa frame 2x2)
    if frame_type["columns"] == 1 and frame_type["rows"] == 2 and not frame_type.get("isCustom", False):
        return WIDTH_IMAGE, HEIGHT_IMAGE
    return (WIDTH_IMAGE, HEIGHT_IMAGE) if frame_type["columns"] > frame_type["rows"] else (HEIGHT_IMAGE, WIDTH_IMAGE)

def calc_aspect_ratio(frame_type):
    return ASPECT_RATIOS.get((frame_type["columns"], frame_type["rows"], frame_type.get("isCustom", False)), (2, 3))

def calc_positions(frame_type, total_width, total_height, margin, gap):
    cols, rows = frame_type["columns"], frame_type["rows"]
    aspect_w, aspect_h = calc_aspect_ratio(frame_type)
    usable_width = total_width - margin * 2 - gap * (cols - 1)
    usable_height = total_height - margin * 2 - gap * (rows - 1)
    photo_width = usable_width // cols
    photo_height = int(photo_width * aspect_h / aspect_w)
    
    if photo_height * rows > usable_height:
        photo_height = usable_height // rows
        photo_width = int(photo_height * aspect_w / aspect_h)
    
    if frame_type.get("isCircle", False):
        max_size = min(usable_width // cols, usable_height // rows)
        photo_width = photo_height = max_size
        if cols == 1 and rows == 1:
            center_x = (total_width - photo_width) // 2
            center_y = (total_height - photo_height) // 2
            return photo_width, photo_height, [(center_x, center_y)]
    
    return photo_width, photo_height, [
        (margin + c * (photo_width + gap), margin + r * (photo_height + gap))
        for r in range(rows) for c in range(cols)
    ]

def fit_cover_image(image, output_size, crop_direction="center"):
    if image.size == output_size:
        return image
    
    img_w, img_h = image.size
    out_w, out_h = output_size
    aspect_img = img_w / img_h
    aspect_out = out_w / out_h
    
    if aspect_img > aspect_out:
        new_h = out_h
        new_w = int(new_h * aspect_img)
        left = 0 if crop_direction == "left" else (new_w - out_w) // 2
        crop_box = (left, 0, left + out_w, new_h)
    else:
        new_w = out_w
        new_h = int(new_w / aspect_img)
        top = 0 if crop_direction == "top" else (new_h - out_h) // 2
        crop_box = (0, top, new_w, top + out_h)
    
    image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    image = image.crop(crop_box)
    
    # Chỉ áp dụng sharpness khi cần thiết
    if max(new_w, new_h) > max(out_w, out_h) * 1.5:
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(1.1)  # Giảm sharpness để nhanh hơn
    return image

def paste_image(frame, img, pos, size, is_circle, frame_type=None):
    if is_circle:
        size = (min(size[0], size[1]), min(size[0], size[1]))
    
    scale_w = size[0] / img.width
    scale_h = size[1] / img.height
    scale = max(scale_w, scale_h)
    
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)

    crop_left = crop_top = False
    if frame_type:
        if frame_type.get("columns") == 1 and frame_type.get("rows") == 1 and not frame_type.get("isCircle", False):
            crop_top = True
        elif frame_type.get("columns") == 2 and frame_type.get("rows") == 2:
            crop_top = True
        # Frame 1x2 ngang cũng crop từ top như frame 2x2
        elif frame_type.get("columns") == 1 and frame_type.get("rows") == 2 and not frame_type.get("isCustom", False):
            crop_top = True
    
    left = 0 if crop_left else (img.width - size[0]) // 2
    top = 0 if crop_top else (img.height - size[1]) // 2
    left = max(0, min(left, img.width - size[0]))
    top = max(0, min(top, img.height - size[1]))
    
    img = img.crop((left, top, left + size[0], top + size[1]))
    if img.size != size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    
    if is_circle:
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size[0]-1, size[1]-1), fill=255)
        # Giảm blur radius để nhanh hơn
        mask = mask.filter(ImageFilter.GaussianBlur(radius=0.3))
        bg = Image.new('RGBA', size, (255, 255, 255, 0))
        bg.paste(img, (0, 0), mask)
        frame.paste(bg, pos, bg)
    else:
        frame.paste(img, pos, img)
    
    return frame