import os
import sys
import tempfile
import pytest
import hashlib
import random
import string
from pathlib import Path
from datetime import datetime, timedelta


backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))


def pytest_configure(config):
    config.option.showlocals = False
    config.option.verbose = 2
    config.option.disable_warnings = True
    config.option.filterwarnings = ["ignore::DeprecationWarning"]


from components.db_connect import get_db_connection
from setup.setup_db import initialise_database
import webapp


def create_password_hash(password):
    salt = 'testingsalt'

    return f"pbkdf2:sha256:1000${salt}${hashlib.sha256((password + salt).encode()).hexdigest()}"


def generate_random_suffix(length = 8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    
    app = webapp.app
    app.config.update({'TESTING': True, 'DB_PATH': db_path, 'SECRET_KEY': 'test_key'})

    os.environ['DB_PATH'] = db_path
    initialise_database()
    
    test_suffix = generate_random_suffix()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        password_hash = create_password_hash('testpassword')
        
        cursor.execute("DELETE FROM users WHERE user_id IN (1, 2)")
        
        cursor.execute(
            "INSERT INTO users (user_id, username, email, password_hash, preferred_categories) VALUES (?, ?, ?, ?, ?)",
            (1, f'testuser_{test_suffix}', f'test_{test_suffix}@example.com', password_hash, None)
        )
        
        cursor.execute(
            "INSERT INTO users (user_id, username, email, password_hash, preferred_categories) VALUES (?, ?, ?, ?, ?)",
            (2, f'userprefs_{test_suffix}', f'pref_{test_suffix}@example.com', password_hash, 'Breakfast,Dinner')
        )
        
        user_ids = {'test_user': 1, 'pref_user': 2}
        
        cursor.execute("SELECT MAX(recipe_id) FROM recipes")
        result = cursor.fetchone()
        recipe_id_start = (result[0] or 0) + 1000
        
        recipe_templates = [
            ('Test Breakfast Recipe', 'A delicious breakfast recipe', 'http://example.com/img1.jpg',
             'Cook eggs and bacon. Toast bread.', 'Breakfast', 'breakfast,eggs,bacon',
             '10m', '5m', '15m', '3,3 slices,2 slices', 'eggs,bacon,toast', 
             500, 20, 5, 200, 300, 30, 2, 5, 15, 1, '1 serving'),
             
            ('Healthy Oatmeal', 'Nutritious breakfast oatmeal', 'http://example.com/img2.jpg',
             'Cook oats with milk. Add honey and berries.', 'Breakfast', 'breakfast,healthy,oats',
             '5m', '2m', '7m', '1 cup,1 cup,1 tbsp,1/2 cup', 'oats,milk,honey,berries',
             350, 5, 1, 0, 100, 60, 8, 12, 10, 1, '1 bowl'),
             
            ('Breakfast Burrito', 'Hearty breakfast burrito', 'http://example.com/img3.jpg',
             'Scramble eggs. Fill tortilla with eggs, cheese, beans. Top with salsa.', 'Breakfast', 
             'breakfast,mexican,eggs',
             '10m', '5m', '15m', '2,1,1/4 cup,1/4 cup,2 tbsp', 'eggs,tortilla,cheese,beans,salsa',
             550, 22, 8, 380, 800, 45, 3, 2, 22, 1, '1 burrito'),
            
            ('Chicken Salad', 'Fresh chicken salad', 'http://example.com/img4.jpg',
             'Grill chicken. Mix with salad and dressing.', 'Lunch', 'lunch,chicken,salad',
             '10m', '15m', '25m', '200g,2 cups,2 tbsp', 'chicken,salad,dressing',
             800, 15, 3, 70, 500, 20, 3, 2, 40, 2, '2 servings'),
             
            ('Pasta Salad', 'Mediterranean pasta salad', 'http://example.com/img5.jpg',
             'Cook pasta. Mix with vegetables, cheese and dressing.', 'Lunch', 'lunch,pasta,vegetarian',
             '15m', '10m', '25m', '2 cups,1 cup,1/2,1/4 cup,1/4 cup,3 tbsp', 
             'pasta,tomatoes,cucumber,olives,feta,dressing',
             700, 25, 8, 20, 600, 80, 4, 5, 15, 2, '2 servings'),
             
            ('Vegetable Soup', 'Hearty vegetable soup', 'http://example.com/img6.jpg',
             'Chop vegetables. Simmer in broth with herbs until tender.', 'Lunch', 'lunch,soup,vegetarian',
             '15m', '30m', '45m', '2,2 stalks,1,2,4 cups,1 tbsp', 
             'carrots,celery,onion,potato,broth,herbs',
             400, 2, 0, 0, 800, 45, 8, 5, 10, 4, '4 servings'),
            
            ('Pasta with Sauce', 'Classic pasta dish', 'http://example.com/img7.jpg',
             'Cook pasta. Mix with sauce and top with cheese.', 'Dinner', 'dinner,pasta,italian',
             '10m', '10m', '20m', '2 cups,1 cup,1/4 cup', 'pasta,sauce,cheese',
             600, 12, 6, 30, 700, 80, 3, 8, 18, 2, '2 servings'),
             
            ('Grilled Salmon', 'Healthy grilled salmon', 'http://example.com/img8.jpg',
             'Season salmon with herbs, olive oil, and lemon. Grill with asparagus.', 'Dinner', 
             'dinner,seafood,healthy',
             '5m', '15m', '20m', '200g,1,1 tbsp,2 tbsp,8 spears', 
             'salmon,lemon,herbs,olive oil,asparagus',
             550, 35, 6, 80, 320, 5, 3, 0, 40, 1, '1 serving'),
             
            ('Vegetable Stir Fry', 'Quick vegetable stir fry', 'http://example.com/img9.jpg',
             'Cook rice. Stir fry tofu and vegetables with soy sauce and ginger.', 'Dinner', 
             'dinner,asian,vegetarian',
             '15m', '15m', '30m', '1 cup,200g,1 cup,1 cup,3 tbsp,1 tbsp', 
             'rice,tofu,broccoli,carrots,soy sauce,ginger',
             450, 10, 1, 0, 900, 60, 6, 4, 20, 2, '2 servings')
        ]
        
        recipe_ids = {}
        
        for i, recipe_template in enumerate(recipe_templates, 1):
            assigned_id = recipe_id_start + i
            full_recipe = (assigned_id,) + recipe_template
            
            try:
                cursor.execute("""
                    INSERT INTO recipes 
                    (recipe_id, recipe_name, description, image_url, instructions, category, 
                     keywords, cook_time, prep_time, total_time, 
                     ingredient_quantity, ingredient_parts, calories, fat, saturated_fat, 
                     cholesterol, sodium, carbohydrates, fiber, sugar, protein, 
                     recipe_servings, recipe_yield) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, full_recipe)
                
                recipe_ids[i] = assigned_id

            except Exception as e:
                print(f"Error inserting recipe {i}: {e}")
        
        cursor.execute("DELETE FROM user_interactions WHERE user_id IN (?, ?)", (user_ids['test_user'], user_ids['pref_user']))
                      
        interactions_data = [
            (user_ids['test_user'], recipe_ids[1], "like"),
            (user_ids['test_user'], recipe_ids[4], "like"),
            (user_ids['test_user'], recipe_ids[7], "like"),
            (user_ids['pref_user'], recipe_ids[2], "like"),
            (user_ids['pref_user'], recipe_ids[5], "like"),
            (user_ids['pref_user'], recipe_ids[8], "like")
        ]
        
        for interaction in interactions_data:
            cursor.execute("INSERT INTO user_interactions (user_id, recipe_id, interaction_type) VALUES (?, ?, ?)", interaction)
        
        cursor.execute("DELETE FROM user_ingredients WHERE user_id IN (?, ?)", (user_ids['test_user'], user_ids['pref_user']))
        
        user_ingredients = [
            (user_ids['test_user'], 'eggs', 12, 'units', 'Dairy'),
            (user_ids['test_user'], 'bacon', 500, 'g', 'Meat'),
            (user_ids['test_user'], 'bread', 1, 'loaf', 'Bakery'),
            (user_ids['test_user'], 'milk', 1, 'liter', 'Dairy'),
            (user_ids['pref_user'], 'oats', 500, 'g', 'Grains'),
            (user_ids['pref_user'], 'berries', 200, 'g', 'Produce')
        ]
        
        for ingredient in user_ingredients:
            cursor.execute("INSERT INTO user_ingredients (user_id, ingredient_name, quantity, unit, category) VALUES (?, ?, ?, ?, ?)", ingredient)
        
        cursor.execute("DELETE FROM shopping_lists WHERE user_id IN (?, ?)", (user_ids['test_user'], user_ids['pref_user']))
        
        cursor.execute("PRAGMA table_info(shopping_lists)")
        columns = [col[1] for col in cursor.fetchall()]
        has_category = 'category' in columns
        
        shopping_list = [
            (user_ids['test_user'], 'tomatoes', 5, 'units', 'Produce'),
            (user_ids['test_user'], 'chicken', 1, 'kg', 'Meat'),
            (user_ids['pref_user'], 'milk', 2, 'liters', 'Dairy')
        ]
        
        for item in shopping_list:
            if has_category:
                cursor.execute("INSERT INTO shopping_lists (user_id, ingredient_name, quantity, unit, category) VALUES (?, ?, ?, ?, ?)", item)
            else:
                cursor.execute("INSERT INTO shopping_lists (user_id, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)", item[0:4])
        
        cursor.execute("DELETE FROM user_meal_plans WHERE user_id IN (?, ?)", (user_ids['test_user'], user_ids['pref_user']))
                      
        today = datetime.now()
        tomorrow = today + timedelta(days = 1)
        day_after = today + timedelta(days = 2)
        
        meal_plans = [
            (user_ids['test_user'], today.strftime('%Y-%m-%d'), recipe_ids[1], recipe_ids[4], recipe_ids[7]),
            (user_ids['test_user'], tomorrow.strftime('%Y-%m-%d'), recipe_ids[2], recipe_ids[5], recipe_ids[8]),
            (user_ids['pref_user'], tomorrow.strftime('%Y-%m-%d'), recipe_ids[3], recipe_ids[6], recipe_ids[9])
        ]
        
        for plan in meal_plans:
            cursor.execute("INSERT INTO user_meal_plans (user_id, meal_date, breakfast_id, lunch_id, dinner_id) VALUES (?, ?, ?, ?, ?)", plan)
        
        cursor.execute("DELETE FROM user_nutrition WHERE user_id IN (?, ?)", (user_ids['test_user'], user_ids['pref_user']))
                      
        nutrition_profiles = [
            (user_ids['test_user'], True, 'male', 35, 180, 75, 75/(1.8*1.8), 'maintain', 'moderate', 2200),
            (user_ids['pref_user'], True, 'female', 28, 165, 60, 60/(1.65*1.65), 'lose', 'light', 1800)
        ]
        
        for profile in nutrition_profiles:
            cursor.execute("INSERT INTO user_nutrition (user_id, nutri_state, sex, age, height, weight, bmi, goal, activity_level, target_calories) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", profile)
        
        app.config['TEST_USER_IDS'] = user_ids
        app.config['TEST_RECIPE_IDS'] = recipe_ids
        
        conn.commit()

    yield app
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    with client.session_transaction() as session:
        user_ids = client.application.config['TEST_USER_IDS'] 
        session['user_id'] = user_ids['test_user']
        session['username'] = 'testuser'

    return client


@pytest.fixture
def db_connection(app):
    with get_db_connection() as conn:
        yield conn


@pytest.fixture
def recipe_ids(app):
    return app.config['TEST_RECIPE_IDS']


@pytest.fixture
def meal_calorie_ranges():
    from modules.utils import get_meal_calorie_ranges

    return get_meal_calorie_ranges(2000)