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


def clean_and_validate_row(row):
    try:
        return {
            "recipe_name": str(row["Name"]).strip() if pd.notna(row["Name"]) else "",
            "description": str(row["Description"]).strip() if pd.notna(row["Description"]) else "",
            "image_url": clean_c_format(row["Images"]) if pd.notna(row["Images"]) else "",
            "instructions": clean_c_format(row["RecipeInstructions"]) if pd.notna(row["RecipeInstructions"]) else "",
            "category": str(row["RecipeCategory"]).strip() if pd.notna(row["RecipeCategory"]) else "",
            "keywords": clean_c_format(row["Keywords"]) if pd.notna(row["Keywords"]) else "",
            "cook_time": str(row["CookTime"]).strip() if pd.notna(row["CookTime"]) else "",
            "prep_time": str(row["PrepTime"]).strip() if pd.notna(row["PrepTime"]) else "",
            "total_time": str(row["TotalTime"]).strip() if pd.notna(row["TotalTime"]) else "",
            "ingredient_quantity": clean_c_format(row["RecipeIngredientQuantities"]) if pd.notna(row["RecipeIngredientQuantities"]) else "",
            "ingredient_parts": clean_c_format(row["RecipeIngredientParts"]) if pd.notna(row["RecipeIngredientParts"]) else "",
            "calories": float(row["Calories"]) if pd.notna(row["Calories"]) else 0.0,
            "fat": float(row["FatContent"]) if pd.notna(row["FatContent"]) else 0.0,
            "saturated_fat": float(row["SaturatedFatContent"]) if pd.notna(row["SaturatedFatContent"]) else 0.0,
            "cholesterol": float(row["CholesterolContent"]) if pd.notna(row["CholesterolContent"]) else 0.0,
            "sodium": float(row["SodiumContent"]) if pd.notna(row["SodiumContent"]) else 0.0,
            "carbohydrates": float(row["CarbohydrateContent"]) if pd.notna(row["CarbohydrateContent"]) else 0.0,
            "fiber": float(row["FiberContent"]) if pd.notna(row["FiberContent"]) else 0.0,
            "sugar": float(row["SugarContent"]) if pd.notna(row["SugarContent"]) else 0.0,
            "protein": float(row["ProteinContent"]) if pd.notna(row["ProteinContent"]) else 0.0,
            "recipe_servings": int(row["RecipeServings"]) if pd.notna(row["RecipeServings"]) else 0,
            "recipe_yield": str(row["RecipeYield"]).strip() if pd.notna(row["RecipeYield"]) else "",
        }
    
    except Exception as e:
        recipe_name = str(row.get("Name", "Unknown"))[:30]
        print(f"[ERROR] Failed to process recipe: {recipe_name}...")

        return None


def load_recipes_to_db():
    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset file not found at {DATASET_PATH}")

        return

    df = pd.read_csv(DATASET_PATH)

    required_columns = [
        "Name", "Description", "Images", "RecipeInstructions", "RecipeCategory",
        "Keywords", "CookTime", "PrepTime", "TotalTime", "RecipeIngredientQuantities",
        "RecipeIngredientParts", "Calories", "FatContent", "SaturatedFatContent",
        "CholesterolContent", "SodiumContent", "CarbohydrateContent", "FiberContent",
        "SugarContent", "ProteinContent", "RecipeServings", "RecipeYield"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"[ERROR] Missing columns in dataset: {missing_columns}")

        return

    rows_inserted = 0
    rows_failed = 0
    total_rows = len(df)

    print(f"Processing {total_rows} recipes...")

    with db_connection() as connection:
        cursor = connection.cursor()

        for _, row in df.iterrows():
            cleaned_row = clean_and_validate_row(row)

            if cleaned_row:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO recipes (
                            recipe_name, description, image_url, instructions, category,
                            keywords, cook_time, prep_time, total_time, ingredient_quantity,
                            ingredient_parts, calories, fat, saturated_fat, cholesterol, sodium,
                            carbohydrates, fiber, sugar, protein, recipe_servings, recipe_yield
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cleaned_row["recipe_name"],
                            cleaned_row["description"],
                            cleaned_row["image_url"],
                            cleaned_row["instructions"],
                            cleaned_row["category"],
                            cleaned_row["keywords"],
                            cleaned_row["cook_time"],
                            cleaned_row["prep_time"],
                            cleaned_row["total_time"],
                            cleaned_row["ingredient_quantity"],
                            cleaned_row["ingredient_parts"],
                            cleaned_row["calories"],
                            cleaned_row["fat"],
                            cleaned_row["saturated_fat"],
                            cleaned_row["cholesterol"],
                            cleaned_row["sodium"],
                            cleaned_row["carbohydrates"],
                            cleaned_row["fiber"],
                            cleaned_row["sugar"],
                            cleaned_row["protein"],
                            cleaned_row["recipe_servings"],
                            cleaned_row["recipe_yield"],
                        ),
                    )

                    rows_inserted += 1

                except Exception:
                    rows_failed += 1

            else:
                rows_failed += 1

    print(f"Recipes processed: {rows_inserted + rows_failed}/{total_rows}")
    print(f"Successfully inserted: {rows_inserted}")
    
    if rows_failed > 0:
        print(f"Failed to process: {rows_failed}")


if __name__ == "__main__":
    load_recipes_to_db()