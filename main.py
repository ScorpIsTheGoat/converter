import os
import re
import cv2
import uvicorn
import ffmpeg
import secrets
import base64
import shutil
import mimetypes
from typing import List
import io
from PIL import Image
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
from database import add_user, verify_user, delete_user, change_email, change_passwordhash, change_username, validate_password, is_valid_email, hash_password, get_user_by_session, add_session_to_user, get_user_by_username, remove_session_from_db, add_file, is_hash_in_table, get_file_path_by_hash, file_is_private, get_username_by_filehash, delete_hash, add_converted_file, get_hash_by_path, increase_amount_of_converted_files, get_file_properties, update_privacy_db, get_file_type_by_hash
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from filter_functions import add_subtitles, create_conversion_string, get_video_properties
from functions import file_exists, format_file_size, create_unique_file_hash, generate_file_hash, extract_thumbnail, is_video_file, is_image_file, get_video_duration, image_to_bytes
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
        return RedirectResponse(url="/login")
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
    if not request.cookies.get("session_id"):
        return RedirectResponse(url="/login")
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
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return HTTPException(status_code=400, detail="not logged in")
    try:
        uploaded_files = []
        username = get_user_by_session(session_id)[1]
        for file in files:
            file_location = os.path.join(f"uploads/{username}/uploaded/", file.filename)
            filehash = create_unique_file_hash(username, file.filename, file.size)
            if is_hash_in_table(filehash):
                continue
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            filepath = os.path.normpath(file_location)
            filename = file.filename
            uploaded_files.append({
                "filename": file.filename,
                "message": f"Upload successful: {filename}"
            })
            filename, filetype = os.path.splitext(filename)
            filetype = filetype.lstrip(".")
            if is_video_file(filepath):
                thumbnail = extract_thumbnail(filepath)
                duration = get_video_duration(filepath)
            elif is_image_file(filepath):
                thumbnail = image_to_bytes(filepath)
                duration = None
            else:
                thumbnail = None
                duration = None
            add_file(filehash, filepath, username, True, filename, filetype, file.size, thumbnail, duration)
        return {"files": uploaded_files}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/colorgrader/type") 
async def upload_type(data : dict):
    global filter_id
    filter_id = data.get("filter_id")
    print(f"Received filter: {filter_id}")
    return {"message": f"Filter '{filter_id}' received"}


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

@app.get("/my-files-information")
async def get_file_informations(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    file_list = []
    user = get_user_by_session(request.cookies.get("session_id"))
    username = user[1]
    user_dir = UPLOAD_DIR / username
    user_upload_dir = user_dir / "uploaded"
    if not user_upload_dir.exists():
        return f"<h1>No files found for user: {username}</h1>"
    for file in user_upload_dir.iterdir():
        file_path = str(user_upload_dir / file.name)
        file_list.append([file.name, get_hash_by_path(file_path), file.stat().st_size])
    return JSONResponse(content={"files": file_list})

@app.get("/files", response_class=HTMLResponse)
async def list_user_files(request: Request):
    user = get_user_by_session(request.cookies.get("session_id"))
    username = user[1]
    user_dir = UPLOAD_DIR / username
    user_upload_dir = user_dir / "uploaded"
    if not user_upload_dir.exists():
        return f"<h1>No files found for user: {username}</h1>"
    files = []
    for file in user_upload_dir.iterdir():
        file_path = os.path.normpath(user_upload_dir) + "\\" + str(file.name)
        properties = get_file_properties(file_path, username)
        properties.pop("thumbnail")
        files.append(properties)
    return JSONResponse(content={"files": files})

@app.get("/thumbnail/{filehash}")
async def get_thumbnail(request: Request, filehash: str):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")         
    file_path = get_file_path_by_hash(filehash)
    username = get_user_by_session(session_id)[1]
    thumbnail = get_file_properties(file_path, username)["thumbnail"]
    thumbnail = Image.open(io.BytesIO(thumbnail))
    thumbnail_stream = io.BytesIO()
    thumbnail.save(thumbnail_stream, format="PNG")
    thumbnail_stream.seek(0)
    return StreamingResponse(thumbnail_stream, media_type="image/png")
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
        return FileResponse(file_path, media_type=mime_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="HTML page not found")

@app.get("/{service}/{options}/{filehash}")
async def convert(request: Request, service: str, options: str, filehash: str,):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    username = get_user_by_session(session_id)[1]
    options = options.split("+")
    file_path = get_file_path_by_hash(filehash)
    file_name = Path(file_path).stem
    properties = get_video_properties(f"C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\uploads\\{username}\\converted\\{file_name}_subtitled{file_extension}")
    new_file_hash = generate_file_hash(filehash, properties["videobitrate"], properties["audiobitrate"], properties["videocodec"], properties["audiocodec"], properties["resolution"], properties["framerate"], properties["filetype"])
    if service == "convert":
        filetype = options[0]
        parsed_options = {
            "videobitrate": None,
            "audiobitrate": None,
            "videocodec": None,
            "audiocodec": None,
            "resolution": None,
            "framerate": None,
            "filetype": None
        }
        for option in options:
            if option.startswith("vb-"):  # Video bitrate
                parsed_options["videobitrate"] = option.split("-")[1]
            elif option.startswith("ab-"):  # Audio bitrate
                parsed_options["audiobitrate"] = option.split("-")[1]
            elif option.startswith("vc-"):  # Video codec
                parsed_options["videocodec"] = option.split("-")[1]
            elif option.startswith("ac-"):  # Audio codec
                parsed_options["audiocodec"] = option.split("-")[1]
            elif option.startswith("res-"):  # Resolution (e.g., 1080p)
                parsed_options["resolution"] = option
            elif option.startswith("fps-"):  # Framerate (e.g., fr:30)
                parsed_options["framerate"] = option.split("-")[1]
            elif option in ["mp4", "avi", "mkv"]:  # Filetype check
                parsed_options["filetype"] = option
        command = create_conversion_string("C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\" + file_path, f"C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\uploads\\{username}\\converted\\output.{filetype}", vc = parsed_options["videocodec"], ac = parsed_options["audiocodec"], vb = parsed_options["videobitrate"], ab = parsed_options["audiobitrate"], resolution = parsed_options["resolution"], framerate = parsed_options["framerate"])
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding = "utf-8")    
        print("Return Code:", result.returncode)
        print("Standard Output:", result.stdout)
        print("Standard Error:", result.stderr)
        increase_amount_of_converted_files(session_id, 1)
        return {"msg": create_unique_file_hash(get_user_by_session(session_id)[1],)}#create entry in db with count for converted data
    if service == "stt":
        _, file_extension = os.path.splitext(file_path)
        language = None
        task = None
        model = None
        for option in options:
            if option == "transcribe":
                task = "transcribe"
            elif option == "translate":
                task = "translate"
            elif option.startswith("lang-"):
                language = option.split("-")[1]
            elif option.startswith("model-"):
                model = option.split("-")[1]
        command_1, command_2 = add_subtitles("C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\" + file_path, f"C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\uploads\\{username}\\converted\\{file_name}_subtitled{file_extension}", username, language = language, task = task, model = model)
        print(command_1)
        print(command_2)
        result = subprocess.run(command_1, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)    
        result = subprocess.run(command_2, capture_output=True, text=True, encoding="utf-8")
        print(result.stdout)
        print(result.stderr)
        add_converted_file(filehash, new_file_hash, file_path, username)
        return{"msg": f"sucessfully converted file with filehash: {new_file_hash}"}
    if service == "colorgrade":
        pass
    if service == "upscale":
        pass
    return


@app.get("/download/{filehash}")
async def download_file(request: Request, filehash: str):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    if get_user_by_session(session_id)[1] != get_username_by_filehash(filehash):
        return RedirectResponse(url="/")
    file_path = get_file_path_by_hash(filehash)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=f"converted_file.mp4")
    else:
        delete_hash(filehash)
        raise HTTPException(status_code=404, detail=f"File not found")
@app.get("/delete/{filehash}")
async def delete_file(request: Request, filehash: str):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    if get_user_by_session(session_id)[1] != get_username_by_filehash(filehash):
        return RedirectResponse(url="/")
    file_path = get_file_path_by_hash(filehash)
    try:
        delete_hash(filehash)
        if os.path.isfile(file_path):
            os.remove(file_path)  
            print(f"File deleted: {file_path}")
            return{"msg":"successful"}
        else:
            print("File not found")
            return{"msg": "file not found"}
    except Exception as e:
        print(f"An error occurred while deleting the file: {e}")
        raise HTTPException(status_code=404, detail=f"File not found")
    
@app.post("/update-privacy/{filehash}/{privacy}")
async def update_privacy(request: Request, filehash: str, privacy: str):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    if get_user_by_session(session_id)[1] != get_username_by_filehash(filehash):
        return RedirectResponse(url="/")
    update_privacy_db(filehash, privacy)
    print("updated privacy settings")
    return{"msg":"successful"}
@app.get("/converter/{combined_filehashes}", response_class=HTMLResponse)
async def get_converter(request: Request, combined_filehashes: str):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    filehashes = combined_filehashes.split("+")
    context = {"request": request}
    for filehash in filehashes:
        if get_user_by_session(session_id)[1]!= get_username_by_filehash(filehash):
            return RedirectResponse(url="/") 
    context["filehashes"] = filehashes
    return templates.TemplateResponse("converter.html", context)

@app.get("/filetype/check/{combined_filehashes}", response_model=dict)
async def check_file_type(combined_filehashes: str):
    filehashes = combined_filehashes.split("+")
    filetypes = [get_file_type_by_hash(filehash) for filehash in filehashes]
    unique_filetypes = set(filetypes)
    if len(unique_filetypes) == 1:
        return {"all_same": True, "filetype": unique_filetypes.pop()}
    return {"all_same": False}
if __name__ == "__main__":
    uvicorn.run("main:app", port=8000)


    

