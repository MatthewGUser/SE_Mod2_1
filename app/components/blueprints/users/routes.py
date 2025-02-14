from flask import jsonify, request, current_app as app, Blueprint
from marshmallow import ValidationError
from . import user_bp
from app.models import User, ServiceTicket, db
from app.components.schemas.user import user_schema, users_schema, login_schema
from app.components.schemas.service_ticket import service_tickets_schema
from app import limiter, cache
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from functools import wraps

def make_cache_key(*args, **kwargs):
    """Generate a cache key based on the route and query parameters"""
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return f'view/{path}:{args}'

# Remove the duplicate Blueprint creation
# user_bp = Blueprint('user', __name__)  # Remove this line

@user_bp.post('/login')
@limiter.limit("5 per minute")
def login():
    """Login user"""
    try:
        data = request.get_json()
        validated_data = login_schema.load(data)
        
        user = User.query.filter_by(email=validated_data['email']).first()
        if not user or not user.check_password(validated_data['password']):
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Invalid email or password!'
            }), 401
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user_schema.dump(user),
            'token': access_token
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'message': str(e.messages)
        }), 400

# Support both /users and /users/register endpoints
@user_bp.route('', methods=['POST'])
@user_bp.route('/register', methods=['POST'])
@limiter.limit("3 per hour")
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'phone']
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Please provide name, email, password, and phone'
            }), 400

        # Check for existing email
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'error': 'Email already registered',
                'message': 'This email is already in use'
            }), 409
        
        # Create new user
        user = User(
            name=data['name'],
            email=data['email'],
            phone=data['phone']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user_schema.dump(user)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Registration failed',
            'message': str(e)
        }), 400

@user_bp.get('')  # This route is at '/users' (since blueprint has a prefix)
@jwt_required()
@cache.cached(timeout=300, key_prefix=make_cache_key)
def get_users():
    """Get list of users - accessible to any authenticated user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'items': users_schema.dump(pagination.items),
            'page': page,
            'pages': pagination.pages,
            'per_page': per_page,
            'total': pagination.total
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve users',
            'message': str(e)
        }), 500

@user_bp.route('/my-tickets')
@jwt_required()
@limiter.limit("30 per minute")
@cache.memoize(300)
def get_my_tickets():
    """Get all service tickets for the authenticated user"""
    user_id = get_jwt_identity()
    tickets = ServiceTicket.query.filter_by(user_id=user_id).all()
    return jsonify(service_tickets_schema.dump(tickets))

@user_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    """Update user details - only owner can update their profile"""
    try:
        current_user_id = get_jwt_identity()
        
        # Convert both IDs to strings for comparison
        if str(current_user_id) != str(id):
            return jsonify({'message': 'Can only update your own profile'}), 403
            
        user = User.query.get_or_404(id)
        data = request.get_json()
        
        # Validate the update data
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        cache.delete(make_cache_key())
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user_schema.dump(user)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@user_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    """Delete user account"""
    try:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        
        # Clear cached data
        cache.delete(make_cache_key())
        
        return jsonify({
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@user_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    """Get user details - accessible to any authenticated user"""
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({
                'message': 'User not found',
                'user_id': id
            }), 404
        return jsonify(user_schema.dump(user)), 200
    except Exception as e:
        return jsonify({
            'error': 'Database error',
            'message': str(e)
        }), 500