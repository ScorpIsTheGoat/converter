import random
from config.constants import UPLOAD_DIR
import cv2
import ffmpeg
import os
from PIL import Image
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



def create_conversion_string(input_file, output_file, **args):
    command = f'ffmpeg -i "{input_file}" '
    print(args)
    if 'vc' in args and args['vc']:
        command += f'-c:v {args["vc"]} '
    if 'ac' in args and args['ac']:
        command += f'-c:a {args["ac"]} '
    if 'vb' in args and args['vb']:
        command += f'-b:v {args["vb"]} '
    if 'ab' in args and args['ab']:
        command += f'-b:a {args["ab"]} '
    if 'resolution' in args and args['resolution']:
        command += f'-vf scale={args["resolution"]}'
    if 'framerate' in args and args['framerate']:
        command += f'-r {args["framerate"]} '
    command += f'"{output_file}"'
    return command

def add_subtitles(input_file, output_file, username, **args):
    file_name = Path(input_file).stem
    subtitle_path = os.path.join(UPLOAD_DIR, username, file_name + ".srt")
    command_create_subtitles = f'whisper "{input_file}" --language {args["language"]} --task {args["task"]} --model {args["model"]} --output_dir uploads/{username} --output_format srt'
    command_add_subtitles = f'ffmpeg -i "{input_file}" -vf subtitles="{subtitle_path}" "{output_file}"'
    command_create_subtitles = command_create_subtitles.replace('\\', "/")
    command_add_subtitles = command_add_subtitles.replace('\\', "/")
    return command_create_subtitles, command_add_subtitles
def get_video_properties(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        properties = {
            "videocodec": video_stream['codec_name'] if video_stream else None,
            "videobitrate": video_stream['bit_rate'] if video_stream else None,
            "resolution": f"{video_stream['width']}x{video_stream['height']}" if video_stream else None,
            "framerate": eval(video_stream['avg_frame_rate']) if video_stream else None,  # Convert "30/1" to 30.0
            "audiocodec": audio_stream['codec_name'] if audio_stream else None,
            "audiobitrate": audio_stream['bit_rate'] if audio_stream else None,
            "filetype": file_path.split('.')[-1]
        }

        return properties
    except ffmpeg.Error as e:
        print(f"Error processing file: {e}")
        return None

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
    
     
    