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
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.aac import AAC
from moviepy.editor import VideoFileClip
sr = cv2.dnn_superres.DnnSuperResImpl_create()
path = "ai-models/EDSR_x2.pb"
sr.readModel(path)
sr.setModel('edsr', 2)

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"



def generate_file_hash(filename: str, username: str, extra: str):
    hash_input = f"{filename}|{username}|{extra}"
    hash_object = hashlib.sha256(hash_input.encode('utf-8'))
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
            if img.mode in ("LA", "P", "RGBA"):  # LA (grayscale + alpha) or P (palette-based)
                img = img.convert("RGB")
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

def is_audio_file(filepath):
    return filepath.lower().endswith(('.mp3', '.wav', '.aac', '.flac', '.ogg'))

def is_text_file(filepath):
    """
    Returns True if the file is a text file, based on its extension or content.
    """
    # Check file extension
    _, ext = os.path.splitext(filepath)
    if ext.lower() in [".txt", ".md", ".csv", ".json", ".html", ".css", ".js", ".xml", ".yaml", ".log"]:
        return True

    # Check file content for text-like data (non-binary content)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Try to read the first few lines to check for non-binary content
            first_bytes = f.read(1024)
            # If it succeeds and doesn't throw an exception, we assume it's a text file
            if any(ord(char) > 127 for char in first_bytes):  # Check if there's a non-ASCII character
                return False  # It has binary data, so it's not a text file
            return True
    except (UnicodeDecodeError, IOError):
        # If we can't read it as text, it's likely a binary file
        return False
        
def get_audio_duration(filepath):
    """Returns the duration of an audio file in seconds."""
    try:
        if filepath.lower().endswith(".mp3"):
            audio = MP3(filepath)
        elif filepath.lower().endswith(".wav"):
            audio = WavPack(filepath)
        elif filepath.lower().endswith(".flac"):
            audio = FLAC(filepath)
        elif filepath.lower().endswith(".ogg"):
            audio = OggVorbis(filepath)
        elif filepath.lower().endswith(".aac"):
            audio = AAC(filepath)
        else:
            return "Unknown"
        
        return round(audio.info.length, 2)  # Rounds to 2 decimal places
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return "Unknown"