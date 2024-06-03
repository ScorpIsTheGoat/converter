from fastapi import FastAPI, File, Form, UploadFile, Request, HTTPException
import uvicorn
from enum import Enum
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from pydantic import BaseModel
import os
import subprocess
#import whisper
import shutil
import time
import ffmpeg 

def convert(input_file, output_file, **args):
    command = f'ffmpeg -i {input_file} '
    
    if 'vc' in args:
        command += f'-c:v {args["vc"]} '
    if 'ac' in args:
        command += f'-c:a {args["ac"]} '
    if 'vb' in args:
        command += f'-b:v {args["vb"]} '
    if 'ab' in args:
        command += f'-b:a {args["ab"]} '
    if 'framerate' in args:
        command += f'-r {args["framerate"]} '
    if 'resolution' in args:
        command += f'-s {args["resolution"]} '

    command += f'{output_file}'

    return command

class FileProperties:
    def __init__(self, file_path):
        self.file_name = Path(file_path).stem
        self.file_type = Path(file_path).suffix
        self.file_size = format_file_size(os.path.getsize(file_path))
        self.file_access_time = time.ctime(os.path.getatime(file_path))
class SelectValue(BaseModel):
    filetype: str
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
#create instance
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

@app.post("/convert")
async def convert_file(select_value: SelectValue):
    filetype = select_value.filetype
    original_file_path = save_to
    converted_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + "-converted." + filetype)
    command = convert(original_file_path, converted_file_name, vb="1000M") #ogg should be converted with high vb
    print(command)
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)    
    try:       
        
        return FileResponse(path=converted_file_name, filename=f"converted_file.{filetype}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
