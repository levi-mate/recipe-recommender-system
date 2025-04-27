import pandas as pd
import re
import os
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "database" / "app_database.db")))
DATASET_PATH = Path(os.environ.get("DATASET_PATH", str(BASE_DIR / "dataset" / "recipes.csv")))


def db_connection():
    return sqlite3.connect(str(DB_PATH))


def clean_c_format(value):
    if isinstance(value, str) and value.startswith("c("):
        matches = re.findall(r'"(.*?)"|\'(.*?)\'', value)
        cleaned_values = [item for tup in matches for item in tup if item]

        return ", ".join(cleaned_values)
    
    return value.strip() if isinstance(value, str) else value


def extract_and_load_ingredients():
    print("Starting ingredient extraction from dataset")
    
    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset file not found at {DATASET_PATH}")

        return

    with db_connection() as connection:
        cursor = connection.cursor()

        try:
            df = pd.read_csv(DATASET_PATH)
            
            print("Extracting unique ingredients")
            
            all_ingredients = []

            for _, row in df.iterrows():
                if pd.notna(row.get("RecipeIngredientParts")):
                    ingredients_text = clean_c_format(row["RecipeIngredientParts"])
                    individual_ingredients = ingredients_text.split(", ")
                    
                    for ingredient in individual_ingredients:
                        ingredient = ingredient.strip().lower()
                        
                        if not ingredient:
                            continue
                        
                        all_ingredients.append(ingredient)
            
            unique_ingredients = list(set(all_ingredients))

            print(f"Found {len(unique_ingredients)} unique ingredients")
            
            ingredients_added = 0
            duplicates = 0
            
            for ingredient in unique_ingredients:
                cleaned_ingredient = ingredient
                
                if ingredient.startswith('"') and ingredient.endswith('"'):
                    cleaned_ingredient = ingredient[1:-1]
                elif ingredient.startswith("'") and ingredient.endswith("'"):
                    cleaned_ingredient = ingredient[1:-1]

                try:
                    cursor.execute("INSERT INTO ingredients (ingredient_name) VALUES (?)", (cleaned_ingredient,))
                    ingredients_added += 1
                    
                except Exception as e:
                    duplicates += 1
            
            print(f"Added {ingredients_added} ingredients ({duplicates} duplicates skipped)")
            
        except Exception as e:
            print(f"Error during ingredient extraction: {str(e)}")

            return
    
    print("Successfully extracted and loaded ingredients")


if __name__ == "__main__":
    extract_and_load_ingredients()