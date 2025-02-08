from functools import wraps
from flask import request, jsonify
import jwt

SECRET_KEY = "a super secret, secret key"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Look for the token in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['sub']  # Fetch the user ID
            
        except jose.exceptions.ExpiredSignatureError:
             return jsonify({'message': 'Token has expired!'}), 401
        except jose.exceptions.JWTError:
             return jsonify({'message': 'Invalid token!'}), 401

        return f(user_id, *args, **kwargs)

    return decorated