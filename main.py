import os
import re
import cv2
import uvicorn
import secrets
import mimetypes
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
from database import add_user, verify_user, delete_user, change_email, change_passwordhash, change_username, validate_password, is_valid_email, hash_password, get_user_by_session, add_session_to_user, get_user_by_username, remove_session_from_db, add_file, is_hash_in_table, get_file_path_by_hash, file_is_private, get_username_by_filehash
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from filter_functions import add_subtitles
from functions import file_exists, format_file_size, create_unique_file_hash
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
    if request.cookies.get("session_id"):
        return RedirectResponse(url="/")
    context = {"request" : request}
    return templates.TemplateResponse("login.html", context)

@app.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    if request.cookies.get("session_id"):
        return RedirectResponse(url="/")
    context = {"request" : request}
    return templates.TemplateResponse("register.html", context)

@app.get("/upload", response_class=HTMLResponse)
def read_upload(request: Request):
    if not request.cookies.get("session_id"):
        return RedirectResponse(url="/")
    context = {"request" : request}
    return templates.TemplateResponse("upload.html", context)

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

@app.get("/my-files", response_class=HTMLResponse)
def read_my_files(request: Request):
    context = {"request" : request}
    return templates.TemplateResponse("files.html", context)

@app.get("/file/{filehash}", response_class=HTMLResponse)
def read_file(request: Request, filehash: str):
    session_id = request.cookies.get("session_id")
    if session_id:
        username = get_user_by_session(session_id)[1]
    if file_is_private(filehash):
        if not session_id:
            raise HTTPException(status_code=400, detail="No access to this file")
        if not username == get_username_by_filehash(filehash):
            raise HTTPException(status_code=400, detail="No access to this file")
    context = {"request" : request}
    return templates.TemplateResponse("specific_file.html", context)

@app.post("/login-post")
async def login_user(select_value: UserLogin, response: Response):
    session_id = secrets.token_hex(16) 
    if not verify_user(select_value.username, hash_password(select_value.password)):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    add_session_to_user(select_value.username, session_id)
    response.set_cookie(key="session_id", value=session_id)
    return {"message": "Session created", "session_id": session_id}

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

@app.post("/upload-post")
async def upload_file(request: Request, file: UploadFile):
    session_id = request.cookies.get("session_id")
    if not session_id:
        print("not logged in")
        return RedirectResponse("/", status_code=303)
    user = get_user_by_session(session_id)
    username = user[1]
    user_dir = UPLOAD_DIR / username
    file_hash = create_unique_file_hash(username, file.filename, file.size)

    if is_hash_in_table(file_hash):
        return {"access-token": file_hash}
    file_path = user_dir / "uploaded" / file.filename
    data = await file.read()
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    with open(file_path, 'wb') as f:
        f.write(data)
        print("Finished uploading:", file.filename)
        add_file(file_hash, os.path.normpath(file_path), username, True)
    return {"access-token": file_hash}

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


@app.get("/get-username-by-session")
async def get_username_by_session(session_id: str = Cookie(None)):
    if session_id:
        user = get_user_by_session(session_id)
        if user:
            return JSONResponse(content={"username": user[1]})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=400, detail="No session ID found")

@app.get("/profile/{username}")
async def read_profile(request: Request, username: str):
    user = get_user_by_username(username)
    session_id = request.cookies.get("session_id")
    if session_id is None or user is None or username != get_user_by_session(session_id)[1]:
        raise HTTPException(status_code=404, detail="User not found")

    context = {"request": request, "username": user[1], "email": user[2]} 
    return templates.TemplateResponse("user.html", context)

@app.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    remove_session_from_db(session_id)
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}

@app.get("/files", response_class=HTMLResponse)
async def list_user_files(request: Request):
    user = get_user_by_session(request.cookies.get("session_id"))
    username = user[1]
    user_dir = UPLOAD_DIR / username
    user_upload_dir = user_dir / "uploaded"
    if not user_upload_dir.exists():
        return f"<h1>No files found for user: {username}</h1>"

    files = [str(file.name) for file in user_upload_dir.iterdir() if file.is_file()]
    return JSONResponse(content={"files": files})

@app.get("/file/content/{filehash}")
async def serve_file_page(filehash: str):
    file_path = get_file_path_by_hash(filehash)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    try:
        return FileResponse(file_path, media_type="video")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="HTML page not found")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000)


    

