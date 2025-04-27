from flask import Blueprint, jsonify, request

from components.db_connect import db_connection
from modules.decorators import handle_errors


autocomplete_bp = Blueprint("autocomplete", __name__)


@autocomplete_bp.route("/autocomplete_recipes", methods = ['GET'])
@handle_errors
def autocomplete_recipes():
    query = request.args.get("query", "").strip().lower()
    
    if not query:
        return jsonify([])
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT recipe_id, recipe_name FROM recipes WHERE LOWER(recipe_name) LIKE ? ORDER BY recipe_name ASC LIMIT 20", (f"%{query}%",))
        
        results = []

        for row in cursor.fetchall():
            recipe_name = row[1].strip('"') if row[1] else ""
            
            if (recipe_name and not recipe_name.startswith("http") and not recipe_name.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))):
                results.append({"recipe_id": row[0], "recipe_name": recipe_name})
        
        return jsonify(results)


@autocomplete_bp.route("/autocomplete_ingredients", methods = ["GET"])
@handle_errors
def autocomplete_ingredients():
    query = request.args.get("query", "").strip().lower()
    
    if not query:
        return jsonify([])
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT ingredient_id, ingredient_name FROM ingredients WHERE LOWER(ingredient_name) LIKE ? ORDER BY ingredient_name ASC LIMIT 20", (f"%{query}%",))
        
        suggestions = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

        return jsonify(suggestions)


@autocomplete_bp.route("/autocomplete_categories", methods = ["GET"])
@handle_errors
def autocomplete_categories():
    query = request.args.get("query", "").strip().lower()
    
    if not query:
        return jsonify([])
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT category FROM recipes WHERE LOWER(category) LIKE ? ORDER BY category ASC LIMIT 20", (f"%{query}%",))
        
        categories = [row[0] for row in cursor.fetchall()]

        return jsonify(categories)