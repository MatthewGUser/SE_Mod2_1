import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from config import Config

def encode_auth_token(user_id):
    """Generate JWT token for user"""
    try:
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(days=1),
            'iat': datetime.now(timezone.utc),
            'sub': str(user_id)
        }
        return jwt.encode(
            payload,
            Config.SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        return str(e)

def auth_required():
    """Basic token authentication decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization')
            
            if auth_header:
                try:
                    token = auth_header.split(' ')[1]
                except IndexError:
                    return jsonify({'message': 'Invalid token format'}), 401
            
            if not token:
                return jsonify({'message': 'Token is missing'}), 401

            try:
                payload = jwt.decode(
                    token,
                    Config.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = int(payload['sub'])
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 401
            except ValueError:
                return jsonify({'message': 'Invalid user ID in token'}), 401

            return f(user_id, *args, **kwargs)
        return decorated
    return decorator

def owner_required(id_param):
    """Decorator to check if user is the owner of the resource"""
    def decorator(f):
        @wraps(f)
        @auth_required()
        def decorated(user_id, *args, **kwargs):
            try:
                resource_id = kwargs.get(id_param)
                
                if str(user_id) != str(resource_id):
                    return jsonify({'message': 'Unauthorized access'}), 403

                return f(user_id, *args, **kwargs)
            except Exception as e:
                return jsonify({'message': str(e)}), 401
        return decorated
    return decorator