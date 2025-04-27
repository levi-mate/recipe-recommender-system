import os
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "database" / "app_database.db")))


def db_connection():
    return sqlite3.connect(str(DB_PATH))


def initialise_database():
    DB_PATH.parent.mkdir(parents = True, exist_ok = True)
    
    print(f"Creating database at {DB_PATH}")

    with db_connection() as connection:
        cursor = connection.cursor()


        # Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preferred_categories TEXT,
            excluded_categories TEXT
        )
        """)


        # User Ingredients Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_ingredients (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            category TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, ingredient_name)
        )
        """)


        # Shopping List Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            shopping_list_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity TEXT,
            unit TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)


        # User Meal Plans Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_meal_plans (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            meal_date DATE NOT NULL,
            breakfast_id INTEGER,
            lunch_id INTEGER,
            dinner_id INTEGER,
            breakfast_finished INTEGER DEFAULT 0,
            lunch_finished INTEGER DEFAULT 0,
            dinner_finished INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (breakfast_id) REFERENCES recipes(recipe_id),
            FOREIGN KEY (lunch_id) REFERENCES recipes(recipe_id),
            FOREIGN KEY (dinner_id) REFERENCES recipes(recipe_id)
        )
        """)


        # User Interactions Table (Upvotes, Downvotes)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            interaction_type TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
        )
        """)


        # User Nutrition Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_nutrition (
            nutrition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            nutri_state BOOLEAN NOT NULL DEFAULT 0,
            sex TEXT,
            age INTEGER,
            height REAL,
            weight REAL,
            bmi REAL,
            goal TEXT DEFAULT 'maintain',
            activity_level TEXT DEFAULT 'low',
            target_calories INTEGER DEFAULT 2000,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)


        # Recipes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_name TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT,
            instructions TEXT NOT NULL,
            category TEXT NOT NULL,
            keywords TEXT NOT NULL,
            cook_time TEXT NOT NULL,
            prep_time TEXT NOT NULL,
            total_time TEXT NOT NULL,
            ingredient_quantity TEXT NOT NULL,
            ingredient_parts TEXT NOT NULL,
            calories REAL NOT NULL,
            fat REAL NOT NULL,
            saturated_fat REAL NOT NULL,
            cholesterol REAL NOT NULL,
            sodium REAL NOT NULL,
            carbohydrates REAL NOT NULL,
            fiber REAL NOT NULL,
            sugar REAL NOT NULL,
            protein REAL NOT NULL,
            recipe_servings INTEGER NOT NULL,
            recipe_yield TEXT NOT NULL
        )
        """)


        # Ingredients Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT UNIQUE NOT NULL
        )
        """)
    

    print("Database tables created successfully")


if __name__ == "__main__":
    initialise_database()