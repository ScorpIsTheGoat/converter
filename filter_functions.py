import random
from config.constants import UPLOAD_DIR
import cv2
import os
from classes import FileProperties
from pathlib import Path
import numpy as np
import re
import pytesseract
import hashlib
import bcrypt
from database import *
from pdf2image import convert_from_path
sr = cv2.dnn_superres.DnnSuperResImpl_create()
path = "ai-models/EDSR_x2.pb"
sr.readModel(path)
sr.setModel('edsr', 2)
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"



def convert(input_file, output_file, **args):
    command = f'ffmpeg -i "{input_file}" '
    print(args)
    if 'vc' in args and args['vc'] != "None":
        command += f'-c:v {args["vc"]} '
    if 'ac' in args and args['ac'] != "None":
        command += f'-c:a {args["ac"]} '
    if 'vb' in args and args['vb'] != "None":
        command += f'-b:v {args["vb"]} '
    if 'ab' in args and args['ab'] != "None":
        command += f'-b:a {args["ab"]} '
    if 'resolution' in args and args['resolution'] != "None":
        command += f'-vf scale={args["resolution"]} '
    if 'framerate' in args and args['framerate'] != "None":
        command += f'-r {args["framerate"]} '
    command += f'"{output_file}"'
    return command

def add_subtitles(input_file, output_file, **args):
    input = FileProperties(input_file)
    subtitle_path = os.path.join(UPLOAD_DIR, input.file_name + ".srt")
    command_create_subtitles = f'whisper "{input_file}" --language {args["language"]} --task {args["task"]} --model {args["model"]} --output_dir uploads --output_format srt'
    command_add_subtitles = f'ffmpeg -i "{input_file}" -vf subtitles="{subtitle_path}" "{output_file}"'
    command_create_subtitles = command_create_subtitles.replace('\\', "/")
    command_add_subtitles = command_add_subtitles.replace('\\', "/")
    return command_create_subtitles, command_add_subtitles

def apply_brightness_contrast(frame, brightness=0, contrast=1.0):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] += brightness
    lab[..., 0] = np.clip(lab[..., 0], 0, 100)
    lab[..., 0] *= contrast
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def apply_saturation(frame, saturation_factor):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[..., 2] *= saturation_factor
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def apply_hue_shift(frame, hue_offset):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[..., 0] = (hsv[..., 0] + hue_offset) % 180
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def apply_black_and_white(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.merge([gray, gray, gray])

def cinematic_style(frame):
    frame = apply_brightness_contrast(frame, brightness=-30, contrast=1.1)
    frame = apply_saturation(frame, saturation_factor=1.2)
    frame = apply_hue_shift(frame, hue_offset=20)
    return frame

def black_and_white_style(frame):
    return apply_black_and_white(frame)

def happy_style(frame):
    frame = apply_brightness_contrast(frame, brightness=20, contrast=1.1)
    frame = apply_saturation(frame, saturation_factor=1.2)
    return frame

def sad_style(frame):
    frame = apply_brightness_contrast(frame, brightness=-20, contrast=0.9)
    frame = apply_saturation(frame, saturation_factor=0.9)
    return frame

def contrast_style(frame):
    frame = apply_brightness_contrast(frame, brightness=0, contrast=1.5)
    return frame

def color_grade_video(input_path, output_path, style=None):
    cap = cv2.VideoCapture(input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if style == 'cinematic':
        style_func = cinematic_style
    elif style == 'black_and_white':
        style_func = black_and_white_style
    elif style == 'happy':
        style_func = happy_style
    elif style == 'sad':
        style_func = sad_style
    elif style == 'contrast':
        style_func = contrast_style
    else:
        style_func = lambda x: x 
    if not out.isOpened():
        print("Failed to open video writer")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        styled_frame = style_func(frame)

        out.write(styled_frame)

    cap.release()
    out.release()
    
def upscale_image(image_path):
    image = cv2.imread(image_path)
    upscaled = sr.upsample(image)
    cv2.imwrite('upscaled.png', upscaled)

def recognize_text_to_txt(file_path, output_path):
    txt_to_txt_File = FileProperties(file_path)
    all_text = ""
    if not txt_to_txt_File.file_type == '.pdf':
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
    else:
        images = convert_from_path(file_path)
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            all_text += f"--- Page {i+1} ---\n"
            all_text += text + "\n"

    with open(output_path, 'w') as file:
        file.write(text)
    
    print(f"Recognized text saved to {output_path}")
     
    