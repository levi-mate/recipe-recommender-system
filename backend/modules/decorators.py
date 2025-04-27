from functools import wraps
from flask import session
import traceback
import logging

from modules.api_utils import unauthorised_response, error_response


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return unauthorised_response()
        
        return f(*args, **kwargs)
    
    return decorated_function


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            traceback.print_exc()

            return error_response("An unexpected error occurred", 500)
        
    return decorated_function