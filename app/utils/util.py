import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from config import Config

def encode_token(customer_id):
    """Generate JWT token for customer"""
    try:
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(days=1),
            'iat': datetime.now(timezone.utc),
            'sub': str(customer_id)  # Convert customer_id to string
        }
        return jwt.encode(
            payload,
            Config.SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        return str(e)

def token_required(f):
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
            customer_id = int(payload['sub'])  # Convert string back to integer
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except ValueError:
            return jsonify({'message': 'Invalid customer ID in token'}), 401

        return f(customer_id, *args, **kwargs)
    return decorated