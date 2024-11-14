import cv2
import os
import numpy as np

def teal_orange_look(image):
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img_hsv)
    h = h.astype(np.uint8)
    mask = np.where(h < 100, True, False)
    h[mask] = np.clip(h[mask] + 50, 0, 179)
    mask = np.where(h > 150, True, False)
    h[mask] = np.clip(h[mask] - 50, 0, 179)
    s = s.astype(np.float32)
    s[v > 128] *= 1.2
    s[s > 255] = 255
    s = np.clip(s, 0, 255).astype(np.uint8)
    img_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)

def apply_monochrome_blend(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    blended_image = cv2.addWeighted(colored_img, 0.4, gray_bgr, 0.6, 0)
    return blended_image



def bleach_bypass_look(image):
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)

    y = np.uint8(np.clip(y * 1.3, 0, 255))  

    cr = np.uint8(np.clip(cr * 0.5 + 128 * 0.5, 0, 255))  
    cb = np.uint8(np.clip(cb * 0.5 + 128 * 0.5, 0, 255))  

    ycrcb = cv2.merge([y, cr, cb])
    result = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def black_and_white(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def film_stock_emulation(image):
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img_hsv)
    
    h = np.clip(h.astype(int) + 10, 0, 179)  

    h = np.where(h > 100, np.clip(h - 10, 0, 179), h)  

    s = np.clip(s * 1.1, 0, 255)  
    
    noise = np.random.normal(0, 10, image.shape[:2]) 
    v = np.clip(v.astype(int) + noise.astype(int), 0, 255) 
    
    img_hsv = cv2.merge([h.astype(np.uint8), s.astype(np.uint8), v.astype(np.uint8)])
    
    result = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
    return cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)


def hdr_simulation(image):
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    
    y = np.uint8(np.clip(y * 1.3, 0, 255))  
    
    cr = np.uint8(np.clip(cr * 1.2, 0, 255))  
    cb = np.uint8(np.clip(cb * 1.2, 0, 255))  
    
    ycrcb = cv2.merge([y, cr, cb])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

def color_scripting(image, scene_type):
    if scene_type == "day":
        return day_scene_color(image)
    elif scene_type == "night":
        return night_scene_color(image)
    else:
        return default_color(image)

def day_scene_color(image):
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img_hsv)
    h = np.clip(h.astype(int) + 10, 0, 179) 
    h = np.where(h > 179, h - 20, h)  
    s = np.clip(s * 1.1, 0, 255)  
    h = h.astype(np.uint8)
    s = s.astype(np.uint8)
    v = v.astype(np.uint8)
    img_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)

def night_scene_color(image):
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img_hsv)
    h = np.clip(h.astype(int) - 10, 0, 179) 
    h = np.where(h < 0, h + 180, h) 
    s = np.clip(s * 0.9, 0, 255) 
    h = h.astype(np.uint8)
    s = s.astype(np.uint8)
    v = v.astype(np.uint8)
    img_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)

def default_color(image):
    return image


def day_for_night(image):
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)  

    y = np.uint8(np.clip(y * 0.5, 0, 255))  

    cr = np.uint8(np.clip(cr - 30, 0, 255))  
    cb = np.uint8(np.clip(cb + 30, 0, 255))  
    cr = np.uint8(np.clip(cr + 10, 0, 255))  

    ycrcb = cv2.merge([y, cr, cb])

    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)






def color_grade_image(image, filter_id):
    if filter_id == "teal_orange":
        return teal_orange_look(image)
    elif filter_id == "monochrome_blend":
        return apply_monochrome_blend(image)
    elif filter_id == "bypass_bleach":
        return bleach_bypass_look(image)
    elif filter_id == "bnw":
        return black_and_white(image)
    elif filter_id == "film_stock":
        return film_stock_emulation(image)
    elif filter_id == "hdr":
        return hdr_simulation(image)
    elif filter_id == "day_scene":
        return day_scene_color(image)
    elif filter_id == "night_scene":
        return night_scene_color(image)
    elif filter_id == "dfn":
        return day_for_night(image)
    else:
        return image  # Default, unprocessed image