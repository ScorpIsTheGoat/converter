from pydantic import BaseModel
from pathlib import Path
import time
import os
from functions import format_file_size

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
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    confirmPassword: str
class UserLogin(BaseModel):
    username: str
    password: str
