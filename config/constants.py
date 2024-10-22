from pathlib import Path

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SALT = b'$2b$12$wDSmrpih/oSxFOEtUasove'
UPLOAD_DIR = Path() / 'uploads'