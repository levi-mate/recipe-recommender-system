from flask import jsonify


def success_response(data = None, message = None):
    response = {"success": True}
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response)


def error_response(message, status_code = 400):
    return jsonify({"error": message}), status_code


def unauthorised_response():
    return error_response("Unauthorised", 401)


def not_found_response(resource_type = "Resource"):
    return error_response(f"{resource_type} not found", 404)