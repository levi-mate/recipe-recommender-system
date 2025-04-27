import re

from components.db_connect import get_db_connection


def get_user_ingredients(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT ingredient_name FROM user_ingredients WHERE user_id = ?", (user_id,))
    ingredients = [row[0].strip().lower() for row in cursor.fetchall() if row[0].strip()]
    connection.close()

    return ingredients


def get_recipes():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT recipe_id, recipe_name, category, ingredient_parts, calories FROM recipes")
    recipes = cursor.fetchall()
    connection.close()

    return recipes


def parse_ingredient_parts(raw_string):
    if not raw_string:
        return []

    if raw_string.strip() == "character(0)":
        return []

    if raw_string.strip().startswith('"') and raw_string.strip().endswith('"'):
        return []
    
    if raw_string.strip().startswith("'") and raw_string.strip().endswith("'"):
        return []

    if raw_string.startswith("c("):
        matches = re.findall(r'"(.*?)"|\'(.*?)\'', raw_string)
        ingredients = [item for tup in matches for item in tup if item]

        return [ingredient.strip().lower() for ingredient in ingredients]

    if "," in raw_string:
        ingredients = [item.strip().lower() for item in raw_string.split(",") if item.strip()]

        return ingredients

    return []


def fetch_recipe_details(recipe_ids):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = f"""
        SELECT recipe_id, recipe_name, description, image_url, instructions, category,
               keywords, cook_time, prep_time, total_time, ingredient_quantity,
               ingredient_parts, calories, fat, saturated_fat, cholesterol, sodium,
               carbohydrates, fiber, sugar, protein, recipe_servings, recipe_yield
        FROM recipes
        WHERE recipe_id IN ({','.join(['?'] * len(recipe_ids))})
    """

    cursor.execute(query, recipe_ids)
    recipes = cursor.fetchall()
    connection.close()

    recipe_details = []

    for recipe in recipes:
        image_urls = re.findall(r'https?://[^\s,]+?\.(jpg|jpeg|png|gif)', recipe[3], re.IGNORECASE)
        first_image_url = image_urls[0] if image_urls else None

        recipe_details.append({
            "recipe_id": recipe[0],
            "recipe_name": recipe[1],
            "description": recipe[2],
            "image_url": first_image_url,
            "instructions": recipe[4],
            "category": recipe[5],
            "keywords": recipe[6],
            "cook_time": recipe[7],
            "prep_time": recipe[8],
            "total_time": recipe[9],
            "ingredient_quantity": recipe[10],
            "ingredient_parts": recipe[11],
            "calories": recipe[12],
            "fat": recipe[13],
            "saturated_fat": recipe[14],
            "cholesterol": recipe[15],
            "sodium": recipe[16],
            "carbohydrates": recipe[17],
            "fiber": recipe[18],
            "sugar": recipe[19],
            "protein": recipe[20],
            "recipe_servings": recipe[21],
            "recipe_yield": recipe[22],
        })

    return recipe_details


def fetch_recipe_categories():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT recipe_id, category FROM recipes")
        recipe_categories = {row[0]: row[1] for row in cursor.fetchall()}

        return recipe_categories
    
    finally:
        connection.close()


def fetch_user_preferred_categories(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT preferred_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result and result[0]:
            preferred_categories = result[0].split(",")

            return preferred_categories
        else:
            return []
        
    finally:
        connection.close()


def fetch_user_excluded_categories(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT excluded_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result and result[0]:
            excluded_categories = result[0].split(",")

            return excluded_categories
        else:
            return []
        
    finally:
        connection.close()


def find_similar_users(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT preferred_categories FROM users WHERE user_id = ?", (user_id,))
        current_user_result = cursor.fetchone()
        
        if not current_user_result or not current_user_result[0]:
            return []
            
        current_user_categories = set(current_user_result[0].split(','))
        
        cursor.execute("SELECT user_id, preferred_categories FROM users WHERE user_id != ?", (user_id,))
        all_users = cursor.fetchall()
        
        user_similarities = []

        for other_user_id, other_categories in all_users:
            if other_categories:
                other_user_categories = set(other_categories.split(','))
                shared_categories = current_user_categories.intersection(other_user_categories)
                similarity_score = len(shared_categories)
                user_similarities.append((other_user_id, similarity_score, list(shared_categories)))
        
        user_similarities.sort(key = lambda x: -x[1])
        
        return user_similarities
    
    finally:
        connection.close()


def fetch_interactions():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT user_id, recipe_id, interaction_type FROM user_interactions")
    interactions = cursor.fetchall()
    connection.close()

    if len(interactions) == 0:
        print("No interactions found in the database")

    return interactions


def get_user_liked_recipes(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT recipe_id FROM user_interactions WHERE user_id = ? AND interaction_type = 'like'", (user_id,))
        liked_recipes = [row[0] for row in cursor.fetchall()]

        return liked_recipes
    
    finally:
        connection.close()


def fetch_recipe_calories():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT recipe_id, calories FROM recipes")
        recipe_calories = {row[0]: float(row[1]) if row[1] else 0.0 for row in cursor.fetchall()}

        return recipe_calories
    
    finally:
        connection.close()


def get_meal_calorie_ranges(target_calories):
    return {
        "breakfast": (0.23 * target_calories, 0.27 * target_calories),
        "lunch": (0.43 * target_calories, 0.47 * target_calories),
        "dinner": (0.28 * target_calories, 0.32 * target_calories),
    }