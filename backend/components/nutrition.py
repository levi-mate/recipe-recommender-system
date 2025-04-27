from flask import Blueprint, session, request

from components.db_connect import db_connection
from modules.api_utils import success_response, error_response
from modules.decorators import require_auth, handle_errors


nutrition_bp = Blueprint("nutrition", __name__)


@nutrition_bp.route("/get_nutrition_info", methods = ["GET"])
@require_auth
@handle_errors
def get_nutrition_info():
    user_id = session["user_id"]

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT nutri_state, sex, age, height, weight, bmi, goal, activity_level, target_calories FROM user_nutrition WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result:
            return success_response(data = {
                "nutri_state": False,
                "sex": "",
                "age": "",
                "height": "",
                "weight": "",
                "bmi": None,
                "goal": "maintain",
                "activity_level": "low",
                "target_calories": 2000
            })
        
        return success_response(data = {
            "nutri_state": bool(result[0]),
            "sex": result[1] or "",
            "age": result[2] or "",
            "height": result[3] or "",
            "weight": result[4] or "",
            "bmi": result[5],
            "goal": result[6] or "maintain",
            "activity_level": result[7] or "low",
            "target_calories": result[8] or 2000
        })


@nutrition_bp.route("/update_nutrition_info", methods = ["POST"])
@require_auth
@handle_errors
def update_nutrition_info():
    user_id = session["user_id"]
    data = request.json

    nutri_state = data.get("nutri_state", False)
    sex = data.get("sex", "")
    age = data.get("age", None)
    height = data.get("height", None)
    weight = data.get("weight", None)
    bmi = data.get("bmi", None)
    goal = data.get("goal", "maintain")
    activity_level = data.get("activity_level", "low")
    target_calories = data.get("target_calories", 2000)

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM user_nutrition WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE user_nutrition 
                SET nutri_state = ?, sex = ?, age = ?, height = ?, weight = ?, bmi = ?, goal = ?, activity_level = ?, target_calories = ?
                WHERE user_id = ?""", 
                (nutri_state, sex, age, height, weight, bmi, goal, activity_level, target_calories, user_id)
            )
        else:
            cursor.execute("""
                INSERT INTO user_nutrition (user_id, nutri_state, sex, age, height, weight, bmi, goal, activity_level, target_calories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (user_id, nutri_state, sex, age, height, weight, bmi, goal, activity_level, target_calories)
            )
        
        connection.commit()

        return success_response(message = "Nutrition information updated successfully")


@nutrition_bp.route("/calculate_target_calories", methods = ["POST"])
@require_auth
@handle_errors
def calculate_target_calories():
    data = request.json
    sex = data.get("sex")
    age = data.get("age")
    height = data.get("height")
    weight = data.get("weight")
    goal = data.get("goal", "maintain")
    activity_level = data.get("activity_level", "low")
    
    if not all([sex, age, height, weight]):
        return error_response("Missing required parameters")
    
    try:
        age = int(age)
        height = float(height)
        weight = float(weight)
        
        bmi = round(weight / ((height / 100) ** 2), 1)

        activity_multipliers = {
            "sedentary": 1.2,
            "low": 1.375, 
            "moderate": 1.55,
            "heavy": 1.725
        }
        
        multiplier = activity_multipliers.get(activity_level, 1.55)
        
        if sex == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        tdee = bmr * multiplier
        
        if goal == "lose":
            target_calories = int(tdee * 0.85)
        elif goal == "gain":
            target_calories = int(tdee * 1.15)
        else:
            target_calories = int(tdee)
        
        return success_response(data = {"target_calories": target_calories, "bmi": bmi})
    
    except ValueError as e:
        return error_response("Invalid input values")
    
    except Exception as e:
        return error_response("Failed to calculate target calories", 500)