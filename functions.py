import random
import pytesseract
from config.constants import UPLOAD_DIR
import cv2
import os
from pathlib import Path
import numpy as np
import re
import hashlib
import bcrypt
from database import *
from PIL import Image
import io
from moviepy.editor import VideoFileClip
sr = cv2.dnn_superres.DnnSuperResImpl_create()
path = "ai-models/EDSR_x2.pb"
sr.readModel(path)
sr.setModel('edsr', 2)

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"



def create_unique_file_hash(username: str, filesize: str, filetype: str) -> str:
    hash_input = f"{username}{filesize}{filetype}"
    file_hash = hashlib.sha256()
    file_hash.update(hash_input.encode('utf-8'))
    return file_hash.hexdigest()

def generate_file_hash(file_hash, videobitrate, audiobitrate, videocodec, audiocodec, resolution, framerate, filetype):
    hash_input = f"{file_hash}|{videobitrate}|{audiobitrate}|{videocodec}|{audiocodec}|{resolution}|{framerate}|{filetype}"
    hash_object = hashlib.sha256(hash_input.encode())
    return hash_object.hexdigest()

def validate_password(password: str) -> bool:
    has_uppercase = re.search(r"[A-Z]", password)
    has_lowercase = re.search(r"[a-z]", password)
    has_number = re.search(r"\d", password)
    has_special_char = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    
    return (
        has_uppercase
        and has_lowercase
        and has_number
        and has_special_char
    )   

def generate_session_id():
    return hashlib.sha256(f"{random.random()}".encode()).hexdigest()

def file_exists(path: str):
    file = Path(path)
    if file.exists():
        return True
    else:
        return False

def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

def extract_thumbnail(video_path: str) -> bytes:
    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise Exception("Unable to open video file.")

        # Read the first frame
        ret, frame = cap.read()

        if not ret:
            raise Exception("Failed to read the first frame from the video.")

        # Convert the frame from BGR to RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to a PIL Image
        image = Image.fromarray(frame_rgb)

        # Save the image to a byte stream
        img_byte_array = io.BytesIO()
        image.save(img_byte_array, format="JPEG", quality=85)  # Save as JPEG with good quality
        img_byte_array.seek(0)

        # Release the video capture
        cap.release()

        return img_byte_array.read()

    except Exception as e:
        print(f"Error: {e}")
        return None
        

def is_video_file(file_path):
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.wmv']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in video_extensions

def get_video_duration(file_path):
    try:
        clip = VideoFileClip(file_path)
        return clip.duration  
    except Exception as e:
        print(f"Error: {e}")
        return None

def image_to_bytes(image_path):
    try:
        with Image.open(image_path) as img:
            byte_io = io.BytesIO()
            img.save(byte_io, format="JPEG")
            byte_io.seek(0)
            return byte_io.read()
    except Exception as e:
        print(f"Error: {e}")
        return None

def is_image_file(filepath):
    try:
        # Try opening the file with Pillow
        with Image.open(filepath) as img:
            # If the file is a valid image, return True
            return True
    except IOError:
        # If IOError is raised, it means the file is not a valid image
        return False