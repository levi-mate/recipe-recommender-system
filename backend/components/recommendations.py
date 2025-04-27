from flask import Blueprint, jsonify, session, request
from datetime import datetime, timedelta

from components.db_connect import db_connection
from modules.utils import fetch_recipe_details
from modules.hybrid import hybrid_recommendations
from modules.api_utils import success_response, error_response
from modules.decorators import require_auth, handle_errors


recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/generate_recommendations", methods = ["GET"])
@require_auth
@handle_errors
def generate_recommendations_endpoint():
    user_id = session["user_id"]
    days = request.args.get("days", default = 1, type = int)
    target_calories = request.args.get("targetCalories", default = 2000, type = int)
    start_date_str = request.args.get("startDate", None)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = datetime.now().date()
    else:
        start_date = datetime.now().date()

    recommendations = hybrid_recommendations(user_id, days = days, target_calories = target_calories)

    session["meal_plan_start_date"] = start_date_str
    
    return success_response(data = recommendations)


@recommendations_bp.route("/save_meal_plans", methods = ["POST"])
@require_auth
@handle_errors
def save_meal_plans():
    user_id = session["user_id"]
    data = request.json
    meal_plans = data.get("mealPlans")
    start_date_str = session.get("meal_plan_start_date", None)

    if not meal_plans or not isinstance(meal_plans, list):
        return error_response("Invalid meal plans data")
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = datetime.now().date()
    else:
        start_date = datetime.now().date()

    with db_connection() as connection:
        cursor = connection.cursor()

        for day, meal_plan in enumerate(meal_plans, start = 1):
            breakfast_id = meal_plan.get("breakfast_id")
            lunch_id = meal_plan.get("lunch_id")
            dinner_id = meal_plan.get("dinner_id")

            if not all([breakfast_id, lunch_id, dinner_id]):
                return error_response(f"Missing meal data for day {day}")
            
            meal_date = (start_date + timedelta(days = day - 1))

            cursor.execute("SELECT 1 FROM user_meal_plans WHERE user_id = ? AND meal_date = ?", (user_id, meal_date.strftime("%Y-%m-%d")))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute(
                    "UPDATE user_meal_plans SET breakfast_id = ?, lunch_id = ?, dinner_id = ? WHERE user_id = ? AND meal_date = ?",
                    (breakfast_id, lunch_id, dinner_id, user_id, meal_date.strftime("%Y-%m-%d"))
                )
            else:
                cursor.execute(
                    "INSERT INTO user_meal_plans (user_id, meal_date, breakfast_id, lunch_id, dinner_id) VALUES (?, ?, ?, ?, ?)",
                    (user_id, meal_date.strftime("%Y-%m-%d"), breakfast_id, lunch_id, dinner_id)
                )

        connection.commit()

    return success_response(message = "Meal plans saved successfully")


@recommendations_bp.route("/get_meal_plan", methods = ["GET"])
@require_auth
@handle_errors
def get_meal_plan():
    user_id = session["user_id"]
    meal_date = request.args.get("meal_date")

    if not meal_date:
        return error_response("Meal date is required")

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT breakfast_id, lunch_id, dinner_id, breakfast_finished, lunch_finished, dinner_finished FROM user_meal_plans WHERE user_id = ? AND meal_date = ?", (user_id, meal_date))
        meal_plan = cursor.fetchone()

        if not meal_plan:
            return error_response("No meal plan found for the specified date", 404)

        recipe_ids = [meal_plan[0], meal_plan[1], meal_plan[2]]

        finished_states = {
            "breakfast_finished": bool(meal_plan[3]),
            "lunch_finished": bool(meal_plan[4]),
            "dinner_finished": bool(meal_plan[5])
        }

        placeholders = ", ".join(["?"] * len(recipe_ids))
        cursor.execute(
            f"""SELECT recipe_id, recipe_name, description, instructions, calories, category, ingredient_parts, 
            ingredient_quantity, cook_time, prep_time, total_time, recipe_servings, fat, saturated_fat, cholesterol, sodium, 
            carbohydrates, fiber, sugar, protein FROM recipes WHERE recipe_id IN ({placeholders})""", 
            recipe_ids
        )
        recipes = cursor.fetchall()

        meal_plan_details = {
            "breakfast": None,
            "lunch": None,
            "dinner": None,
            "breakfast_finished": finished_states["breakfast_finished"],
            "lunch_finished": finished_states["lunch_finished"],
            "dinner_finished": finished_states["dinner_finished"]
        }

        for recipe in recipes:
            recipe_data = {
                "recipe_id": recipe[0],
                "recipe_name": recipe[1],
                "description": recipe[2],
                "instructions": recipe[3],
                "calories": recipe[4],
                "category": recipe[5],
                "ingredient_parts": recipe[6],
                "ingredient_quantity": recipe[7],
                "cook_time": recipe[8],
                "prep_time": recipe[9],
                "total_time": recipe[10],
                "recipe_servings": recipe[11],
                "fat": recipe[12],
                "saturated_fat": recipe[13],
                "cholesterol": recipe[14],
                "sodium": recipe[15],
                "carbohydrates": recipe[16],
                "fiber": recipe[17],
                "sugar": recipe[18],
                "protein": recipe[19],
            }

            if recipe[0] == meal_plan[0]:
                meal_plan_details["breakfast"] = recipe_data
            elif recipe[0] == meal_plan[1]:
                meal_plan_details["lunch"] = recipe_data
            elif recipe[0] == meal_plan[2]:
                meal_plan_details["dinner"] = recipe_data

        return jsonify(meal_plan_details)


@recommendations_bp.route("/get_weekly_meal_plan", methods = ["GET"])
@require_auth
@handle_errors
def get_weekly_meal_plan():
    user_id = session["user_id"]
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return error_response("Start date and end date are required")

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT meal_date, breakfast_id, lunch_id, dinner_id FROM user_meal_plans WHERE user_id = ? AND meal_date BETWEEN ? AND ? ORDER BY meal_date", (user_id, start_date, end_date))
        meal_plans = cursor.fetchall()

        if not meal_plans:
            return error_response("No meal plans found for the specified week", 404)

        recipe_ids = set()

        for meal_plan in meal_plans:
            recipe_ids.update([meal_plan[1], meal_plan[2], meal_plan[3]])

        placeholders = ", ".join(["?"] * len(recipe_ids))
        cursor.execute(
            f"""SELECT recipe_id, recipe_name, description, instructions, calories, category, ingredient_parts,
                ingredient_quantity, cook_time, prep_time, total_time, recipe_servings, fat, saturated_fat, cholesterol, sodium,
                carbohydrates, fiber, sugar, protein
                FROM recipes WHERE recipe_id IN ({placeholders})""", 
            list(recipe_ids)
        )

        recipes = cursor.fetchall()

        recipe_details_map = {
            recipe[0]: {
                "recipe_id": recipe[0],
                "recipe_name": recipe[1],
                "description": recipe[2],
                "instructions": recipe[3],
                "calories": recipe[4],
                "category": recipe[5],
                "ingredient_parts": recipe[6],
                "ingredient_quantity": recipe[7],
                "cook_time": recipe[8],
                "prep_time": recipe[9],
                "total_time": recipe[10],
                "recipe_servings": recipe[11],
                "fat": recipe[12],
                "saturated_fat": recipe[13],
                "cholesterol": recipe[14],
                "sodium": recipe[15],
                "carbohydrates": recipe[16],
                "fiber": recipe[17],
                "sugar": recipe[18],
                "protein": recipe[19],
            }

            for recipe in recipes
        }

        weekly_meal_plan = []

        for meal_date, breakfast_id, lunch_id, dinner_id in meal_plans:
            daily_plan = {
                "date": meal_date,
                "breakfast": recipe_details_map.get(breakfast_id),
                "lunch": recipe_details_map.get(lunch_id),
                "dinner": recipe_details_map.get(dinner_id),
            }

            weekly_meal_plan.append(daily_plan)

        return jsonify(weekly_meal_plan)


@recommendations_bp.route("/fetch_recipe_details", methods = ["POST"])
@handle_errors
def fetch_recipe_details_endpoint():
    data = request.json
    recipe_ids = data.get("recipeIds", [])

    if not recipe_ids or not isinstance(recipe_ids, list):
        return error_response("Invalid recipe IDs")

    recipe_details = fetch_recipe_details(recipe_ids)

    return jsonify(recipe_details)


@recommendations_bp.route("/get_recipe_ingredients/<int:recipe_id>", methods = ["GET"])
@handle_errors
def get_recipe_ingredients(recipe_id):
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT ingredient_parts, ingredient_quantity FROM recipes WHERE recipe_id = ?", (recipe_id,))
        recipe = cursor.fetchone()

        if not recipe:
            return error_response("Recipe not found", 404)

        ingredient_parts = recipe[0].split(",")
        ingredient_quantities = recipe[1].split(",") if recipe[1] else [None] * len(ingredient_parts)

        ingredients = [{"name": part.strip(), "quantity": quantity.strip() if quantity else None} for part, quantity in zip(ingredient_parts, ingredient_quantities)]

        return jsonify(ingredients)


@recommendations_bp.route("/check_meal_plan_dates", methods = ["POST"])
@require_auth
@handle_errors
def check_meal_plan_dates():
    user_id = session["user_id"]
    data = request.json
    dates = data.get("dates", [])
    
    if not dates:
        return error_response("No dates provided")
    
    with db_connection() as connection:
        cursor = connection.cursor()
    
        results = []

        for date in dates:
            cursor.execute("SELECT 1 FROM user_meal_plans WHERE user_id = ? AND meal_date = ?", (user_id, date))

            results.append(bool(cursor.fetchone()))
            
        return success_response(data = {"results": results})


@recommendations_bp.route("/mark_meal_finished", methods = ["POST"])
@require_auth
@handle_errors
def mark_meal_finished():
    user_id = session["user_id"]
    data = request.json
    meal_date = data.get("meal_date")
    meal_type = data.get("meal_type")
    
    if not meal_date or not meal_type:
        return error_response("Meal date and meal type are required")
    
    if meal_type not in ["breakfast", "lunch", "dinner"]:
        return error_response("Invalid meal type")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM user_meal_plans WHERE user_id = ? AND meal_date = ?", (user_id, meal_date))
        
        if not cursor.fetchone():
            return error_response("No meal plan found for the specified date", 404)
        
        cursor.execute(f"UPDATE user_meal_plans SET {meal_type}_finished = 1 WHERE user_id = ? AND meal_date = ?", (user_id, meal_date))
        connection.commit()

        return success_response(message = f"{meal_type.capitalize()} marked as finished")


@recommendations_bp.route("/delete_meal_plan", methods = ["POST"])
@require_auth
@handle_errors
def delete_meal_plan():
    user_id = session["user_id"]
    data = request.json
    meal_date = data.get("meal_date")
    
    if not meal_date:
        return error_response("Meal date is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user_meal_plans WHERE user_id = ? AND meal_date = ?", (user_id, meal_date))
        
        if cursor.rowcount == 0:
            return error_response("No meal plan found for the specified date", 404)
            
        connection.commit()
        
        return success_response(message = f"Meal plan deleted for {meal_date}")


@recommendations_bp.route("/get_user_interactions", methods = ["GET"])
@require_auth
@handle_errors
def get_user_interactions():
    user_id = session["user_id"]
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT recipe_id, interaction_type FROM user_interactions WHERE user_id = ?", (user_id,))
        interactions = [{"recipe_id": row[0], "interaction_type": row[1]} for row in cursor.fetchall()]
        
        return success_response(data = {"interactions": interactions})


@recommendations_bp.route("/save_interaction", methods = ["POST"])
@require_auth
@handle_errors
def save_interaction():
    user_id = session["user_id"]
    data = request.json
    recipe_id = data.get("recipe_id")
    interaction_type = data.get("interaction_type")

    if not recipe_id or interaction_type not in ["like", "dislike"]:
        return error_response("Invalid data")

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO user_interactions (user_id, recipe_id, interaction_type) VALUES (?, ?, ?)", (user_id, recipe_id, interaction_type))
        connection.commit()

        return success_response(message = "Interaction saved successfully")