import os

# import whisper
import shutil
import subprocess
import time
from enum import Enum
from pathlib import Path

import cv2
import ffmpeg
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

"""
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

class FileProperties:
    def __init__(self, file_path):
        self.file_name = Path(file_path).stem
        self.file_type = Path(file_path).suffix
        self.file_size = format_file_size(os.path.getsize(file_path))
        self.file_access_time = time.ctime(os.path.getatime(file_path))
class SelectValue(BaseModel):
    filetype: str
    videocodec: str
    audiocodec: str
    videobitrate: str
    audiobitrate: str
    resolution: str
    framerate: str
class SelectValuesSubtitler(BaseModel):
    language: str
    model: str
    task: str


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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  
    allow_headers=["*"],  
)
#model = whisper.load_model("medium")
UPLOAD_DIR = Path() / 'uploads'


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("index.html", context)

@app.get("/converter.html", response_class=HTMLResponse)
def read_converter(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("converter.html", context)

@app.get("/subtitler.html", response_class=HTMLResponse)
def read_subtitler(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("subtitler.html", context)

@app.post("/upload")
async def create_upload_file(file: UploadFile):
    files = os.listdir(UPLOAD_DIR)
    for file_name in files:
            file_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
    print("Has been deleted")
    data = await file.read()
    global save_to
    save_to = UPLOAD_DIR / file.filename
    with open(save_to, 'wb') as f:
        f.write(data)
        print("finished uploading")
    while True:
        if file_exists(save_to) and os.access(save_to, os.R_OK):
            break
    global uploaded_file
    uploaded_file = FileProperties(save_to)
    print(uploaded_file.file_name, uploaded_file.file_type, uploaded_file.file_size, uploaded_file.file_access_time)

    return {"filename": file.filename}
@app.post("/subtitle-upload")
async def create_upload(file: UploadFile):
    files = os.listdir(UPLOAD_DIR)
    for file_name in files:
            file_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
    print("Has been deleted")
    data = await file.read()
    global save_to
    save_to = UPLOAD_DIR / file.filename
    with open(save_to, 'wb') as f:
        f.write(data)
        print("finished uploading")
    while True:
        if file_exists(save_to) and os.access(save_to, os.R_OK):
            break
    global uploaded_file
    uploaded_file = FileProperties(save_to)
    print(uploaded_file.file_name, uploaded_file.file_type, uploaded_file.file_size, uploaded_file.file_access_time)

    return {"filename": file.filename}

@app.post("/convert")
async def convert_file(select_value: SelectValue):
    filetype = select_value.filetype
    videocodec = select_value.videocodec
    audiocodec = select_value.audiocodec
    videobitrate = select_value.videobitrate
    audiobitrate = select_value.audiobitrate
    resolution = select_value.resolution
    framerate = select_value.framerate
    print(save_to)
    original_file_path = save_to
    print(uploaded_file.file_name)
    converted_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + "-converted." + filetype)
    command = convert(original_file_path, converted_file_name, vc = videocodec, ac = audiocodec, vb = videobitrate, ab = audiobitrate, resolution = resolution, framerate = framerate) #ogg should be converted with high vb
    print(command)
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding = "utf-8")
    print(result.stdout)
    print(result.stderr)    
    try:       
        
        return FileResponse(path=converted_file_name, filename=f"converted_file.{filetype}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/give")
async def subtitle(select_value: SelectValuesSubtitler):
    language = select_value.language
    task = select_value.task
    model = select_value.model
    print(uploaded_file)
    inputed_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + uploaded_file.file_type)
    converted_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + "-converted" + uploaded_file.file_type)
    command_1, command_2 = add_subtitles(inputed_file_name, converted_file_name, language = language, task = task, model = model)
    print(command_1)
    print(command_2)
    result = subprocess.run(command_1, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)    
    result = subprocess.run(command_2, capture_output=True, text=True, encoding="utf-8")
    print(result.stdout)
    print(result.stderr)    
    try:       
        return FileResponse(path=converted_file_name, filename=f"converted_file.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

if __name__ == "__main__":
    uvicorn.run("sql_app.app:app", port=8000)
