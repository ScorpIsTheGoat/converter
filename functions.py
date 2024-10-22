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
sr = cv2.dnn_superres.DnnSuperResImpl_create()
path = "ai-models/EDSR_x2.pb"
sr.readModel(path)
sr.setModel('edsr', 2)

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"


def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), SALT)
    return hashed_password.decode('utf-8')

def is_valid_email(email):
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
    if re.match(regex, email):
        return True
    else:
        return False

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