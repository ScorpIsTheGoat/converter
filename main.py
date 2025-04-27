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
from database import add_user, verify_user, delete_user, change_email, change_passwordhash, change_username, validate_password, is_valid_email, hash_password, get_user_by_session, add_session_to_user, get_user_by_username, remove_session_from_db, add_file, is_hash_in_table, get_file_path_by_hash, file_is_private, get_username_by_filehash, delete_file_from_table, get_hash_by_path, increase_amount_of_converted_files, get_file_properties, update_privacy_db, get_file_type_by_hash, get_attributes_by_filehash
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from filter_functions import add_subtitles, create_conversion_string, get_video_properties, create_new_filename, transcribe
from functions import file_exists, format_file_size, generate_file_hash, extract_thumbnail, is_video_file, is_image_file, is_audio_file, is_text_file, get_video_duration, get_audio_duration, image_to_bytes
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
def read_login(request: Request, session_id: str = Cookie(None)):
    if session_id:
        return RedirectResponse(url="/")
    context = {"request" : request}
    return templates.TemplateResponse("login.html", context)

@app.get("/register", response_class=HTMLResponse)
def read_register(request: Request, session_id: str = Cookie(None)):
    if session_id:
        return RedirectResponse(url="/")
    context = {"request" : request}
    return templates.TemplateResponse("register.html", context)

@app.get("/upload", response_class=HTMLResponse)
def read_upload(request: Request, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/login")
    context = {"request" : request}
    return templates.TemplateResponse("upload.html", context)

@app.get("/converter", response_class=HTMLResponse)
def read_converter(request: Request, session_id: str = Cookie(None)):
    if not session_id: 
        return RedirectResponse(url="/login")
    context = {"request" : request}
    return templates.TemplateResponse("converter.html", context)

@app.get("/subtitler", response_class=HTMLResponse)
def read_subtitler(request: Request, session_id: str = Cookie(None)):
    if not session_id: 
        return RedirectResponse(url="/login")
    context = {"request" : request}
    return templates.TemplateResponse("subtitler.html", context)

@app.get("/colorgrader", response_class=HTMLResponse)
def read_colorgrade(request: Request, session_id: str = Cookie(None)):
    if not session_id: 
        return RedirectResponse(url="/login")
    context = {"request" : request}
    return templates.TemplateResponse("colorgrader.html", context)

@app.get("/my-files", response_class=HTMLResponse)
def read_my_files(request: Request, session_id: str = Cookie(None)):
    context = {"request" : request}
    if not session_id:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("files.html", context)
@app.get("/metadata/{filehash}")
async def get_metadata(filehash: str, session_id: str = Cookie(None)):
    if session_id:
        username = get_user_by_session(session_id)[1]
    if file_is_private(filehash):
        if not session_id:
            raise HTTPException(status_code=400, detail="No access to this file")
        if not username == get_username_by_filehash(filehash):
            raise HTTPException(status_code=400, detail="No access to this file")
    metadata = get_attributes_by_filehash(filehash)
    return {"metadata" : metadata}
@app.get("/file/{filehash}", response_class=HTMLResponse)
def read_file(request: Request, filehash: str, session_id: str = Cookie(None)):
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
async def upload_files(request: Request, files: List[UploadFile] = File(...), session_id: str = Cookie(None)):

    if not session_id:
        return HTTPException(status_code=400, detail="not logged in")
    try:
        uploaded_files = []
        username = get_user_by_session(session_id)[1]
        for file in files:
            filename = file.filename
            filesize = file.size
            file_location = os.path.join(f"uploads/{username}/uploaded/", filename)
            filehash = generate_file_hash(filename, username, filesize)
            if is_hash_in_table(filehash):
                print("Files has already been uploaded")
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
                duration = "None"
            elif is_audio_file(filepath):
                thumbnail = image_to_bytes(r"C:\Users\jonas\OneDrive - Kantonsschule Romanshorn\converter-project\static\images\audiofile.png")
                duration = get_audio_duration(filepath)
            elif is_text_file(filepath):
                thumbnail = image_to_bytes(r"C:\Users\jonas\OneDrive - Kantonsschule Romanshorn\converter-project\static\images\textfile.png")
                duration = "None"
            else:
                thumbnail = image_to_bytes(r"C:\Users\jonas\OneDrive - Kantonsschule Romanshorn\converter-project\static\images\file.png")
                duration = "None"
            add_file("None", filehash, filepath, username, True, filename, filetype, file.size, thumbnail, duration)
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
async def read_profile(request: Request, username: str, session_id: str = Cookie(None)):
    user = get_user_by_username(username)
    if session_id is None or user is None or username != get_user_by_session(session_id)[1]:
        raise HTTPException(status_code=404, detail="User not found")

    context = {"request": request, "username": user[1], "email": user[2]} 
    return templates.TemplateResponse("user.html", context)

@app.post("/logout")
async def logout(request: Request, response: Response, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    remove_session_from_db(session_id)
    response.delete_cookie("session_id")
    return RedirectResponse(url="/")

@app.get("/my-files-information")
async def get_file_informations(request: Request, response: Response, session_id: str = Cookie(None)):
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
async def list_user_files(request: Request, session_id: str = Cookie(None)):
    user = get_user_by_session(session_id)
    username = user[1]
    user_dir = UPLOAD_DIR / username
    user_upload_dir = user_dir / "uploaded"
    user_converted_dir = user_dir / "converted"
    if not user_upload_dir.exists():
        return f"<h1>No files found for user: {username}</h1>"
    uploaded_files = []
    converted_files = []
    for file in user_upload_dir.iterdir():
        file_path = os.path.normpath(user_upload_dir) + "\\" + str(file.name)
        properties = get_file_properties(file_path, username)
        if properties:
            properties.pop("thumbnail")
            uploaded_files.append(properties)
    for file in user_converted_dir.iterdir():
        file_path = os.path.normpath(user_converted_dir) + "\\" + str(file.name)
        properties = get_file_properties(file_path, username)
        properties.pop("thumbnail")
        converted_files.append(properties)
    files = [uploaded_files, converted_files]
    return JSONResponse(content={"files": files})

@app.get("/thumbnail/{filehash}")
async def get_thumbnail(request: Request, filehash: str, session_id: str = Cookie(None)):
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

@app.get("/filetype/check/{combined_filehashes}", response_model=dict)
async def check_file_type(combined_filehashes: str):
    filehashes = combined_filehashes.split(",")
    unique_filetypes = set()
    for filehash in filehashes:
        filetype = get_file_type_by_hash(filehash).lower()
        unique_filetypes.add(filetype)
    if len(unique_filetypes) == 1:
        return {"all_same": True, "filetype": unique_filetypes.pop()}
    return {"all_same": False}

@app.get("/{service}/{options}/{filehash}")
async def convert(request: Request, service: str, options: str, filehash: str, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    username = get_user_by_session(session_id)[1]
    options = options.split("+")
    filehashes = filehash.split("+")

    if service == "convert": 
        unique_filetypes = set()
        file_paths = set()
        for filehash in filehashes:
            filetype = get_file_type_by_hash(filehash).lower()
            unique_filetypes.add(filetype)
            file_paths.add(get_file_path_by_hash(filehash))
        if len(unique_filetypes) != 1:
            return {"not all the same"}

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
            elif option.startswith("res-"):  
                parsed_options["resolution"] = option
            elif option.startswith("fps-"):  
                parsed_options["framerate"] = option.split("-")[1]
            elif option in ["mp4", "mov", "avi", "mkv", "jpg", "png"]:
                parsed_options["filetype"] = option
        

        for file_path in file_paths:
            filetype = Path(file_path).suffix.lstrip('.')
            filename = Path(file_path).stem
            inputpath = "C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\" + file_path
            outputpath_shortened = f"uploads\\{username}\\converted\\{create_new_filename(filename, parsed_options)}.{parsed_options["filetype"]}"
            outputpath = f"C:\\Users\\jonas\\OneDrive - Kantonsschule Romanshorn\\converter-project\\" + outputpath_shortened
            command = create_conversion_string(inputpath, outputpath, vc = parsed_options["videocodec"], ac = parsed_options["audiocodec"], vb = parsed_options["videobitrate"], ab = parsed_options["audiobitrate"], resolution = parsed_options["resolution"], framerate = parsed_options["framerate"])
            print(command)
            filehash_converted = generate_file_hash(create_new_filename(filename, parsed_options), username, get_hash_by_path(file_path))
            if is_hash_in_table(filehash_converted):
                return {"msg": "has already been converted"}
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding = "utf-8")    
            print("Return Code:", result.returncode)
            print("Standard Output:", result.stdout)
            print("Standard Error:", result.stderr)
            increase_amount_of_converted_files(session_id, 1)
            if is_video_file(outputpath):
                thumbnail = extract_thumbnail(outputpath)
                duration = get_video_duration(outputpath)
            elif is_image_file(outputpath):
                thumbnail = image_to_bytes(outputpath)
                duration = None
            else:
                thumbnail = None
                duration = None
            add_file(filehash, filehash_converted, outputpath_shortened, username, True, filename, parsed_options["filetype"], os.path.getsize(outputpath), thumbnail, duration)
        return {"msg": filehash_converted}
    if service == "stt":
        if len(filehashes) != 1:
            return "To many files selected"
        filehash = filehashes[0]
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
        subtitles_path = transcribe(filehash, language = language, task = task, model = model)
        add_subtitles(get_file_path_by_hash(filehash), subtitles_path)
        converted_file_hash = generate_file_hash(create_new_filename(filename, parsed_options), username, get_hash_by_path(file_path))
        add_file(filehash, filehash_converted, outputpath_shortened, username, True, file_name, file_type, os.path.getsize(outputpath), thumbnail, duration)
        file_path = get_file_path_by_hash(filehashes[0])
        file_name = Path(file_path).stem
        file_type = Path(file_path).suffix.lstrip('.')
        subtitle_path = os.path.join(UPLOAD_DIR, username, file_name + ".srt")
        thumbnail = extract_thumbnail(outputpath)
        duration = get_video_duration(outputpath)
        filehash_converted = generate_file_hash("output." + file_type, username, os.path.getsize(outputpath))
        add_file(filehash, filehash_converted, outputpath_shortened, username, True, file_name, file_type, os.path.getsize(outputpath), thumbnail, duration)
        return{"msg": f"sucessfully converted file with filehash: {filehash_converted}"}
    if service == "colorgrade":
        filter = options
        color_grade_image()
    if service == "upscale":
        pass
    return
@app.get("/file-information/{filehash}")
async def file_information_by_filehash(request: Request, response: Response, filehash: str, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    user = get_user_by_session(request.cookies.get("session_id"))
    username = user[1]
    file_path = get_file_path_by_hash(filehash)
    properties = get_file_properties(file_path, username)
    if properties:
        properties.pop("thumbnail")
    return JSONResponse(content = {"properties":properties})
    

@app.get("/download/{filehash}")
async def download_file(request: Request, filehash: str, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    if get_user_by_session(session_id)[1] != get_username_by_filehash(filehash):
        return RedirectResponse(url="/")
    file_path = get_file_path_by_hash(filehash)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=f"converted_file.mp4")
    else:
        delete_file_from_table(filehash)
        raise HTTPException(status_code=404, detail=f"File not found")
@app.get("/delete/{filehash}")
async def delete_file(request: Request, filehash: str, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    if get_user_by_session(session_id)[1] != get_username_by_filehash(filehash):
        return RedirectResponse(url="/")
    file_path = get_file_path_by_hash(filehash)
    try:
        delete_file_from_table(filehash)
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
async def update_privacy(request: Request, filehash: str, privacy: str, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    if get_user_by_session(session_id)[1] != get_username_by_filehash(filehash):
        return RedirectResponse(url="/")
    update_privacy_db(filehash, privacy)
    print("updated privacy settings")
    return{"msg":"successful"}

@app.get("/converter/{combined_filehashes}", response_class=HTMLResponse)
async def get_converter(request: Request, combined_filehashes: str, session_id: str = Cookie(None)):
    if not session_id:
        return RedirectResponse(url="/")
    filehashes = combined_filehashes.split("+")
    context = {"request": request}
    for filehash in filehashes:
        if get_user_by_session(session_id)[1]!= get_username_by_filehash(filehash):
            return RedirectResponse(url="/") 
    context["filehashes"] = filehashes
    return templates.TemplateResponse("converter.html", context)



if __name__ == "__main__":
    uvicorn.run("main:app", port=8000)


    

