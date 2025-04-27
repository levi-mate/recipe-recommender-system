from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from components.db_connect import db_connection
from modules.api_utils import success_response, error_response
from modules.decorators import require_auth, handle_errors
from modules.utils import fetch_user_preferred_categories


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login/", methods = ["POST"])
@handle_errors
def login():
    form_type = request.form.get("form_type")

    if form_type == "login":
        username = request.form.get("loginUser")
        password = request.form.get("loginPwd")

        if not username or not password:
            return error_response("Username and password are required")

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                return error_response("Invalid username or password", 401)
                
            try:
                user_id = user["user_id"]
                user_name = user["username"]
                password_hash = user["password_hash"]
            except (TypeError, KeyError): 
                user_id = user[0]
                user_name = username
                password_hash = user[3]
            
            if not check_password_hash(password_hash, password):
                return error_response("Invalid username or password", 401)
            
            session["user_id"] = user_id
            session["username"] = user_name
            
            return success_response(message = "Login successful", data = {"redirect": "/account"})

    elif form_type == "register":
        username = request.form.get("registerUser")
        email = request.form.get("registerEmail")
        password = request.form.get("registerPwd")
        confirm_password = request.form.get("registerRepPwd")

        if not all([username, email, password, confirm_password]):
            return error_response("All fields are required")

        if password != confirm_password:
            return error_response("Passwords do not match")

        password_hash = generate_password_hash(password)

        try:
            with db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, password_hash))
                connection.commit()
                
                user_id = cursor.lastrowid
                session["user_id"] = user_id
                session["username"] = username
                
                return success_response(message = "Registration successful", data = {"redirect": "/select-categories"})
        
        except sqlite3.IntegrityError:
            return error_response("Username or email already exists")

    return error_response("Invalid form type")


@auth_bp.route("/logout", methods = ["POST"])
@handle_errors
def logout():
    session.clear()

    return success_response(message = "Logged out successfully")


@auth_bp.route("/check_login", methods = ["GET"])
@handle_errors
def check_login():
    logged_in = "user_id" in session
    user_id = session.get("user_id")
    username = session.get("username")

    return success_response(data = {"loggedIn": logged_in, "userId": user_id, "username": username})


@auth_bp.route("/get_user_profile", methods = ["GET"])
@require_auth
@handle_errors
def get_user_profile():
    user_id = session["user_id"]
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT username, email FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return error_response("User not found", 404)
            
        return success_response(data = {"username": result[0], "email": result[1]})


@auth_bp.route("/update_username", methods = ["POST"])
@require_auth
@handle_errors
def update_username():
    user_id = session["user_id"]
    data = request.json
    new_username = data.get("username")
    
    if not new_username:
        return error_response("Username is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ? AND user_id != ?", (new_username, user_id))

        if cursor.fetchone():
            return error_response("Username is already taken")
            
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (new_username, user_id))
        connection.commit()
        
        session["username"] = new_username

        return success_response(message = "Username updated successfully")


@auth_bp.route("/update_email", methods = ["POST"])
@require_auth
@handle_errors
def update_email():
    user_id = session["user_id"]
    data = request.json
    new_email = data.get("email")
    
    if not new_email:
        return error_response("Email is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = ? AND user_id != ?", (new_email, user_id))

        if cursor.fetchone():
            return error_response("Email is already registered to another account")
            
        cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (new_email, user_id))
        connection.commit()
        
        return success_response(message = "Email updated successfully")


@auth_bp.route("/update_password", methods = ["POST"])
@require_auth
@handle_errors
def update_password():
    user_id = session["user_id"]
    data = request.json
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return error_response("Both current and new passwords are required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result or not check_password_hash(result[0], current_password):
            return error_response("Current password is incorrect")
            
        new_password_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_password_hash, user_id))
        connection.commit()
        
        return success_response(message = "Password updated successfully")


@auth_bp.route("/save_preferred_categories", methods = ["POST"])
@require_auth
@handle_errors
def save_preferred_categories():
    user_id = session["user_id"]
    data = request.json
    preferred_categories = data.get("preferred_categories", [])

    if not preferred_categories or len(preferred_categories) != 10:
        return error_response("You must select exactly 10 categories")

    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET preferred_categories = ? WHERE user_id = ?", (",".join(preferred_categories), user_id))
        connection.commit()
        
        return success_response(message = "Preferred categories saved successfully")


@auth_bp.route("/get_preferred_categories", methods = ["GET"])
@require_auth
@handle_errors
def get_preferred_categories():
    user_id = session["user_id"]
    preferred_categories = fetch_user_preferred_categories(user_id)

    return success_response(data = preferred_categories)
    

@auth_bp.route("/add_preferred_category", methods = ["POST"])
@require_auth
@handle_errors
def add_preferred_category():
    user_id = session["user_id"]
    data = request.json
    category = data.get("category")
    
    if not category:
        return error_response("Category is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT preferred_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        categories = []
        if result and result[0]:
            categories = result[0].split(",")
        
        if category not in categories:
            categories.append(category)
            
            cursor.execute("UPDATE users SET preferred_categories = ? WHERE user_id = ?", (",".join(categories), user_id))
            connection.commit()
            
            return success_response(message = "Category added successfully")
        else:
            return error_response("Category already in preferences")


@auth_bp.route("/delete_preferred_category", methods = ["POST"])
@require_auth
@handle_errors
def delete_preferred_category():
    user_id = session["user_id"]
    data = request.json
    category = data.get("category")
    
    if not category:
        return error_response("Category is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT preferred_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return error_response("No preferred categories found", 404)
            
        categories = result[0].split(",")
        
        if category in categories:
            categories.remove(category)
            
            cursor.execute("UPDATE users SET preferred_categories = ? WHERE user_id = ?", (",".join(categories), user_id))
            connection.commit()
            
            return success_response(message = "Category deleted successfully")
        else:
            return error_response("Category not found in preferences", 404)


@auth_bp.route("/get_excluded_categories", methods = ["GET"])
@require_auth
@handle_errors
def get_excluded_categories():
    user_id = session["user_id"]
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT excluded_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return success_response(data = [])
        
        excluded_categories = result[0].split(",")
        return success_response(data = excluded_categories)


@auth_bp.route("/add_excluded_category", methods = ["POST"])
@require_auth
@handle_errors
def add_excluded_category():
    user_id = session["user_id"]
    data = request.json
    category = data.get("category")
    
    if not category:
        return error_response("Category is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT excluded_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        categories = []
        
        if result and result[0]:
            categories = result[0].split(",")
        
        cursor.execute("SELECT preferred_categories FROM users WHERE user_id = ?", (user_id,))
        pref_result = cursor.fetchone()

        if pref_result and pref_result[0]:
            preferred_categories = pref_result[0].split(",")

            if category in preferred_categories:
                return error_response("Cannot exclude a category that is in your preferred categories")
        
        if category not in categories:
            categories.append(category)
            
            cursor.execute("UPDATE users SET excluded_categories = ? WHERE user_id = ?", (",".join(categories), user_id))
            connection.commit()
            
            return success_response(message = "Category excluded successfully")
        else:
            return error_response("Category already in excluded list")


@auth_bp.route("/delete_excluded_category", methods = ["POST"])
@require_auth
@handle_errors
def delete_excluded_category():
    user_id = session["user_id"]
    data = request.json
    category = data.get("category")
    
    if not category:
        return error_response("Category is required")
    
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT excluded_categories FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return error_response("No excluded categories found", 404)
            
        categories = result[0].split(",")
        
        if category in categories:
            categories.remove(category)
            
            cursor.execute("UPDATE users SET excluded_categories = ? WHERE user_id = ?", (",".join(categories), user_id))
            connection.commit()
            
            return success_response(message = "Category removed from exclusion list")
        else:
            return error_response("Category not found in exclusions", 404)