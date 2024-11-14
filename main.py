import os
import re
import cv2
import uvicorn
import secrets
from typing import List
from pathlib import Path
import pytesseract
from fastapi import FastAPI, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from config.constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SALT, UPLOAD_DIR
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import os
import json
from fastapi import FastAPI, File, APIRouter, Depends, HTTPException, Request, UploadFile, status
from classes import FileProperties, SelectValue, SelectValuesSubtitler, UserLogin, UserRegister
from database import add_user, verify_user, delete_user, change_email, change_passwordhash, change_username, validate_password, is_valid_email, hash_password, get_user_by_session, add_session_to_user
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from filter_functions import add_subtitles
from functions import file_exists, format_file_size
from classes import FileProperties
from colorgrading import color_grade_image
#model = whisper.load_model("medium")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  
    allow_headers=["*"],  
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
uploaded_files = {}
#app.include_router(app_routes)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, session_id: str = Cookie(None)):
    context = {"request": request}
    if session_id:
        print("session id")
        user = get_user_by_session(session_id)  
        if user:
            username = user[1]  
            context["username"] = username
            context["logged_in"] = True
    else:
        print("no session_id yet")
        context = {"request": request}
    
    return templates.TemplateResponse("index.html", context)

@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("login.html", context)

@app.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("register.html", context)

@app.get("/converter", response_class=HTMLResponse)
def read_converter(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("converter.html", context)

@app.get("/subtitler", response_class=HTMLResponse)
def read_subtitler(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("subtitler.html", context)

@app.get("/colorgrader", response_class=HTMLResponse)
def read_colorgrade(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("colorgrader.html", context)

@app.post("/login-post")
async def login_user(select_value: UserLogin, response: Response):
    if not verify_user(select_value.username, hash_password(select_value.password)):#tries to verify user in database, still lacking jwt-token or cookies
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    session_id = secrets.token_hex(16) 
    add_session_to_user(select_value.username, session_id)
    response.set_cookie(key="session_id", value=session_id)
    return RedirectResponse(url="/", status_code=303)
@app.post("/cookie/")
def create_cookie():
    content = {"message": "Come to the dark side, we have cookies"}
    response = JSONResponse(content=content)
    response.set_cookie(key="fakesession", value="fake-cookie-session-value")
    return response
@app.post("/register-post")
async def register_user(select_value: UserRegister):
    if not len(select_value.username) >= 5:
        return {"msg": "Username is too short"}
    if not len(select_value.username) <= 12:
        return {"msg": "Username is too long"}
    if not validate_password(select_value.password):
        return {"msg": "Password is not valid"}
    if not is_valid_email(select_value.email):
        return {"msg": "Invalid email"}
    if not len(select_value.password) >= 8:
        return {"msg": "Password is too short"}
    if not len(select_value.password) <= 20:
        return {"msg": "Password is too long"}
    if not select_value.password == select_value.confirmPassword:
        return {"msg": "Passwords not matching"}       
    if add_user(select_value.username, select_value.email, hash_password(select_value.password)): #hashes and stores in users.db
        return {"msg" : "User already registered"}
    return RedirectResponse(url="/", status_code=303)

@app.post("/converter-upload")
async def create_upload_file(files: UploadFile): #Can't upload multiple files, very weird with fastapi
    files = os.listdir(UPLOAD_DIR)
    for file_name in files:
            file_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path) #just makes sure that uploads directory is empty
    print("Has been deleted")

    for file in files:
        data = await file.read()
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, 'wb') as f:
            f.write(data)
            print("Finished uploading:", file.filename)
        file_hash = generate_session_id(file.filename)#generate random hash to access if has already been uploaded to save time and resources
        uploaded_files[file_hash] = str(file_path)
        print(uploaded_file.file_name, uploaded_file.file_type, uploaded_file.file_size, uploaded_file.file_access_time)
    with open('uploaded_files.json', 'w') as json_file:
        json.dump(uploaded_files, json_file, indent=4)
    return {"access-token": file.filename}

@app.post("/subtitle-upload")
async def create_upload(file: UploadFile):
    files = os.listdir(UPLOAD_DIR)
    for file_name in files:
            file_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.isfile(file_path): #removing existing file
                os.remove(file_path)
    print("Has been deleted")
    data = await file.read()
    global save_to
    save_to = UPLOAD_DIR / file.filename
    with open(save_to, 'wb') as f: #saving uploaded file into folder
        f.write(data)
        print("finished uploading")
    while True:
        if file_exists(save_to) and os.access(save_to, os.R_OK): #check if file exists and is readable
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
    original_file_path = save_to
    converted_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + "-converted." + filetype)
    #command for converting using ffmpeg
    command = convert(original_file_path, converted_file_name, vc = videocodec, ac = audiocodec, vb = videobitrate, ab = audiobitrate, resolution = resolution, framerate = framerate) #ogg should be converted with high vb
    #running command in powershell
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding = "utf-8")    
    try:       
        return FileResponse(path=converted_file_name, filename=f"converted_file.{filetype}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/give")
async def subtitle(select_value: SelectValuesSubtitler):
    language = select_value.language
    task = select_value.task
    model = select_value.model
    inputed_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + uploaded_file.file_type)
    converted_file_name = os.path.join(UPLOAD_DIR, uploaded_file.file_name + "-converted" + uploaded_file.file_type)
    command_1, command_2 = add_subtitles(inputed_file_name, converted_file_name, language = language, task = task, model = model)
    #first command creates subtitles
    result = subprocess.run(command_1, capture_output=True, text=True)
    #second command adds subtitles  
    result = subprocess.run(command_2, capture_output=True, text=True, encoding="utf-8") 
    try:       
        return FileResponse(path=converted_file_name, filename=f"converted_file.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/colorgrader/upload") 
async def upload_video(video: UploadFile = File(...)):
    video_path = f"uploads/{video.filename}"
    data = await video.read()
    with open(video_path,'wb') as f:
        f.write(data)
    global uploaded_file
    uploaded_file = FileProperties(video_path)
    return {"msg": "Uploaded video"} 

@app.post("/colorgrader/type") #not working yet
async def upload_type(data : dict):
    global filter_id
    filter_id = data.get("filter_id")
    print(f"Received filter: {filter_id}")
    return {"message": f"Filter '{filter_id}' received"}

@app.post("/colorgrader/confirmation")
async def return_colorgraded_media():
    image_path = f'uploads/{uploaded_file.file_name}{uploaded_file.file_type}'
    image = cv2.imread(image_path)
    color_graded_image = color_grade_image(image, filter_id)
    output_path = "uploads/color_graded_output.jpg"
    cv2.imwrite(output_path, color_graded_image)
    return FileResponse(output_path, media_type='image/jpeg', filename=f"processed_{uploaded_file.file_name}") 

@app.get("/create-session/")
async def create_session(response: Response):
    session_id = secrets.token_hex(16)
    response.set_cookie(key="session_id", value=session_id)
    return {"message": "Session created", "session_id": session_id}






if __name__ == "__main__":
    uvicorn.run("main:app", port=8000)


    

