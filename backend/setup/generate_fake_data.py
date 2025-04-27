import random
import os
import sqlite3
from faker import Faker
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "database" / "app_database.db")))


def db_connection():
    return sqlite3.connect(str(DB_PATH))


fake = Faker()

def get_unique_categories():
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT category FROM recipes")
        categories = [row[0] for row in cursor.fetchall() if row[0]]

    return categories


def generate_fake_users(num_users = 100):
    categories = get_unique_categories()

    with db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "excluded_categories" in columns:
            insert_sql = "INSERT INTO users (username, email, password_hash, preferred_categories, excluded_categories) VALUES (?, ?, ?, ?, ?)"
        else:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN excluded_categories TEXT")
                insert_sql = "INSERT INTO users (username, email, password_hash, preferred_categories, excluded_categories) VALUES (?, ?, ?, ?, ?)"
            except:
                insert_sql = "INSERT INTO users (username, email, password_hash, preferred_categories) VALUES (?, ?, ?, ?)"

        for _ in range(num_users):
            username = fake.user_name()
            email = fake.email()
            password_hash = fake.sha256()
            
            preferred_categories = random.sample(categories, k = min(10, len(categories)))
            
            remaining_categories = [cat for cat in categories if cat not in preferred_categories]
            excluded_categories = random.sample(remaining_categories, k = min(10, len(remaining_categories)))
            
            if "excluded_categories" in columns or "ALTER TABLE" in insert_sql:
                cursor.execute(insert_sql, (username, email, password_hash, ",".join(preferred_categories), ",".join(excluded_categories)))
            else:
                cursor.execute(insert_sql, (username, email, password_hash, ",".join(preferred_categories)))

    print(f"Generated {num_users} fake users with preferences and exclusions")


def generate_fake_interactions():
    with db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT recipe_id, category FROM recipes")
        recipe_info = {row[0]: row[1] for row in cursor.fetchall()}
        
        if not recipe_info:
            print("No recipes found in the database. Cannot generate interactions.")
            return
            
        interactions_added = 0

        for user_id in user_ids:
            cursor.execute("SELECT preferred_categories FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            pref_categories = result[0].split(",") if result and result[0] else []
            
            num_interactions = random.randint(20, 40)
            
            recipes_by_category = {}

            for rid, cat in recipe_info.items():
                if cat not in recipes_by_category:
                    recipes_by_category[cat] = []

                recipes_by_category[cat].append(rid)
            
            liked_recipes = []
            
            for cat in pref_categories:
                if cat in recipes_by_category:
                    cat_recipes = recipes_by_category[cat]
                    sample_size = min(len(cat_recipes), random.randint(5, 10))
                    liked_recipes.extend(random.sample(cat_recipes, sample_size))
            
            other_cats = [c for c in recipes_by_category if c not in pref_categories]

            for cat in random.sample(other_cats, min(len(other_cats), random.randint(1, 3))):
                cat_recipes = recipes_by_category[cat]
                sample_size = min(len(cat_recipes), random.randint(1, 3))
                liked_recipes.extend(random.sample(cat_recipes, sample_size))
                
            remaining = max(0, num_interactions - len(liked_recipes))
            available_recipes = [r for r in recipe_info.keys() if r not in liked_recipes]

            if remaining > 0 and available_recipes:
                liked_recipes.extend(random.sample(available_recipes, min(remaining, len(available_recipes))))
            
            for recipe_id in liked_recipes:
                interaction_type = random.choices(["like", "dislike"], weights = [0.8, 0.2])[0]
                
                try:
                    cursor.execute("INSERT INTO user_interactions (user_id, recipe_id, interaction_type) VALUES (?, ?, ?)", (user_id, recipe_id, interaction_type))
                    interactions_added += 1

                except Exception as e:
                    print(f"Error adding interaction for user {user_id}, recipe {recipe_id}: {e}")

        print(f"Generated {interactions_added} fake interactions")


def generate_fake_user_ingredients():
    with db_connection() as connection:
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT ingredient_name FROM ingredients")
        all_ingredients = [row[0] for row in cursor.fetchall() if row[0]]
        
        if not all_ingredients:
            print("No ingredients found in the ingredients table")

            return
            
        ingredients_added = 0
        
        for user_id in user_ids:
            num_ingredients = random.randint(10, 20)
            
            if len(all_ingredients) >= num_ingredients:
                user_ingredients = random.sample(all_ingredients, num_ingredients)
            else:
                user_ingredients = random.choices(all_ingredients, k = num_ingredients)
                
            for ingredient_name in user_ingredients:
                try:
                    cursor.execute("INSERT INTO user_ingredients (user_id, ingredient_name, quantity, unit, category) VALUES (?, ?, ?, ?, ?)", (user_id, ingredient_name, 1, "unit", "TBD"))
                    ingredients_added += 1

                except Exception as e:
                    print(f"Error adding ingredient '{ingredient_name}' for user {user_id}: {e}")
                    
        connection.commit()

        print(f"Added {ingredients_added} ingredients for {len(user_ids)} users")


if __name__ == "__main__":
    generate_fake_users(num_users = 100)
    generate_fake_interactions()
    generate_fake_user_ingredients()