from pathlib import Path
import os
UPLOAD_DIR = Path() / 'uploads'
files = os.listdir(UPLOAD_DIR)

for file_name in files:
        file_path = os.path.join(UPLOAD_DIR, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)