from flask import Blueprint, request, session

from components.db_connect import db_connection
from modules.api_utils import success_response, error_response
from modules.decorators import require_auth, handle_errors


ingredients_bp = Blueprint("ingredients", __name__)


@ingredients_bp.route("/account_ingredients/", methods = ["GET"])
@require_auth
@handle_errors
def get_ingredients():
    user_id = session["user_id"]

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user_ingredients WHERE user_id = ? ORDER BY category, ingredient_name", (user_id,))
        ingredients = cursor.fetchall()

        ingredients_list = [
            {
                "ingredient_id": row["ingredient_id"],
                "ingredient_name": row["ingredient_name"],
                "quantity": row["quantity"],
                "unit": row["unit"],
                "category": row["category"]
            }

            for row in ingredients
        ]

        return success_response(data = ingredients_list)


@ingredients_bp.route("/add_ingredient", methods = ["POST"])
@require_auth
@handle_errors
def add_ingredient():
    user_id = session["user_id"]
    data = request.json
    name = data.get("ingredient_name")
    quantity = data.get("quantity")
    unit = data.get("unit")
    category = data.get("category")

    if not all([name, quantity, unit, category]):
        return error_response("All fields are required")

    with db_connection() as connection:
        cursor = connection.cursor()

        try:
            cursor.execute("INSERT INTO user_ingredients (user_id, ingredient_name, quantity, unit, category) VALUES (?, ?, ?, ?, ?)", (user_id, name, quantity, unit, category))
            connection.commit()

            return success_response(message = "Ingredient added successfully")
        
        except Exception as e:
            print(f"Error adding ingredient: {str(e)}")

            return error_response("Ingredient already exists")


@ingredients_bp.route("/update_ingredient/<int:ingredient_id>", methods = ["POST"])
@require_auth
@handle_errors
def update_ingredient(ingredient_id):
    user_id = session["user_id"]
    data = request.json
    quantity = data.get("quantity")
    unit = data.get("unit")
    category = data.get("category")

    if not quantity or not unit or not category:
        return error_response("Quantity, unit, and category are required")

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE user_ingredients SET quantity = ?, unit = ?, category = ? WHERE ingredient_id = ? AND user_id = ?", (quantity, unit, category, ingredient_id, user_id))
        connection.commit()

        if cursor.rowcount == 0:
            return error_response("Ingredient not found or not owned by user", 404)

        return success_response(message="Ingredient updated successfully")


@ingredients_bp.route("/delete_ingredient/<int:ingredient_id>", methods = ["POST"])
@require_auth
@handle_errors
def delete_ingredient(ingredient_id):
    user_id = session["user_id"]

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user_ingredients WHERE ingredient_id = ? AND user_id = ?", (ingredient_id, user_id))
        connection.commit()
        
        if cursor.rowcount == 0:
            return error_response("Ingredient not found or not owned by user", 404)
        
        return success_response(message = "Ingredient deleted successfully")


@ingredients_bp.route("/get_categories", methods = ["GET"])
@handle_errors
def get_categories():
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT category FROM recipes")
        categories = [row[0] for row in cursor.fetchall()]
        
        return success_response(data = categories)


@ingredients_bp.route("/move_to_user_ingredients", methods = ["POST"])
@require_auth
@handle_errors
def move_to_user_ingredients():
    user_id = session["user_id"]
    data = request.json
    ingredients = data.get("ingredients", [])

    if not ingredients:
        return error_response("No ingredients provided")

    with db_connection() as connection:
        cursor = connection.cursor()

        for ingredient in ingredients:
            name = ingredient["name"]
            quantity = float(ingredient.get("quantity", 0) or 0)  
            unit = ingredient.get("unit") or ""
            
            cursor.execute("SELECT ingredient_id, quantity FROM user_ingredients WHERE user_id = ? AND ingredient_name = ?", (user_id, name))
            existing = cursor.fetchone()
            
            if existing:
                existing_id = existing[0]
                existing_quantity = float(existing[1] or 0)
                new_quantity = existing_quantity + quantity
                
                cursor.execute("UPDATE user_ingredients SET quantity = ? WHERE ingredient_id = ?", (new_quantity, existing_id))
            else:
                cursor.execute("INSERT INTO user_ingredients (user_id, ingredient_name, quantity, unit, category) VALUES (?, ?, ?, ?, ?)", (user_id, name, quantity, unit, "TBD"))
            
            cursor.execute("DELETE FROM shopping_lists WHERE user_id = ? AND ingredient_name = ?", (user_id, name))

        connection.commit()
        
        return success_response(message = "Ingredients moved to user ingredients")


@ingredients_bp.route("/add_to_shopping_list", methods = ["POST"])
@require_auth
@handle_errors
def add_to_shopping_list():
    user_id = session["user_id"]
    data = request.json
    ingredients = data.get("ingredients", [])

    if not ingredients:
        return error_response("No ingredients provided")

    with db_connection() as connection:
        cursor = connection.cursor()

        for ingredient in ingredients:
            cursor.execute(
                "INSERT INTO shopping_lists (user_id, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)", 
                (user_id, ingredient["name"], ingredient.get("quantity"), ingredient.get("unit"))
            )

        connection.commit()

        return success_response(message = "Ingredients added to shopping list")


@ingredients_bp.route("/get_shopping_list", methods = ["GET"])
@require_auth
@handle_errors
def get_shopping_list():
    user_id = session["user_id"]
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT ingredient_name, quantity, unit FROM shopping_lists WHERE user_id = ?", (user_id,))
        shopping_list = [{"name": row[0], "quantity": row[1], "unit": row[2]} for row in cursor.fetchall()]
        
        return success_response(data = shopping_list)


@ingredients_bp.route("/update_shopping_list", methods = ["POST"])
@require_auth
@handle_errors
def update_shopping_list():
    user_id = session["user_id"]
    data = request.json
    ingredients = data.get("ingredients", [])

    if not isinstance(ingredients, list):
        return error_response("Invalid data format")

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM shopping_lists WHERE user_id = ?", (user_id,))

        for ingredient in ingredients:
            cursor.execute(
                "INSERT INTO shopping_lists (user_id, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)", 
                (user_id, ingredient["name"], ingredient.get("quantity"), ingredient.get("unit"))
            )

        connection.commit()

        return success_response(message = "Shopping list updated successfully")