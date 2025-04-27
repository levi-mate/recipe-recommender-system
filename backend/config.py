from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
SETUP_DIR = BASE_DIR / "setup"
DATASET_DIR = BASE_DIR / "dataset"


DB_PATH = DB_DIR / "app_database.db"
DATASET_PATH = DATASET_DIR / "recipes.csv"


FLASK_DEBUG = True
FLASK_PORT = 5077
ALLOWED_ORIGINS = ["http://localhost:5173"]
SECRET_KEY = "super_secret_key"


DEFAULT_TARGET_CALORIES = 2000
MAX_RESULTS = 5
CONTENT_WEIGHT = 0.6