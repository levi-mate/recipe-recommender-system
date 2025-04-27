import sys
import subprocess
from flask import Flask
from flask_cors import CORS
import logging
import os

from config import BASE_DIR, SETUP_DIR, DB_PATH, DATASET_PATH, FLASK_PORT, FLASK_DEBUG, ALLOWED_ORIGINS, SECRET_KEY
from setup.setup_db import initialise_database

from components.auth import auth_bp
from components.ingredients import ingredients_bp
from components.recommendations import recommendations_bp
from components.nutrition import nutrition_bp
from components.autocomplete import autocomplete_bp


sys.path.append(str(BASE_DIR))


logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def setup_database():
    logging.info("Database not found. Creating new database...")
    
    os.environ["DB_PATH"] = str(DB_PATH)
    os.environ["DATASET_PATH"] = str(DATASET_PATH)
    
    logging.info("\n[Step 1] Creating database tables...")
    initialise_database()
    logging.info("Database created successfully")
    
    logging.info("\n[Step 2] Loading recipes data from dataset...")
    setup_script = SETUP_DIR / "load_recipes.py"
    subprocess.run([sys.executable, str(setup_script)], check = True)
    
    logging.info("\n[Step 3] Extracting and loading ingredients from dataset...")
    setup_script = SETUP_DIR / "extract_ingredients.py"
    subprocess.run([sys.executable, str(setup_script)], check = True)
    
    logging.info("\n[Step 4] Generating fake user data...")
    setup_script = SETUP_DIR / "generate_fake_data.py"
    subprocess.run([sys.executable, str(setup_script)], check = True)
    
    logging.info("\nDatabase setup complete, the system is ready to use.")


if not DB_PATH.exists():
    setup_database()


app = Flask(__name__)
CORS(app, supports_credentials = True, origins = ALLOWED_ORIGINS)
app.secret_key = SECRET_KEY


app.register_blueprint(auth_bp)
app.register_blueprint(ingredients_bp)
app.register_blueprint(recommendations_bp)
app.register_blueprint(nutrition_bp)
app.register_blueprint(autocomplete_bp)


if __name__ == "__main__":
    app.run(port = FLASK_PORT, debug = FLASK_DEBUG)