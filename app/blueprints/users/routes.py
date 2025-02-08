from flask import jsonify, request
from . import user_bp
from app.models import User, ServiceTicket, db
from app.utils.util import token_required, encode_token
from app.schemas.user import user_schema, users_schema, login_schema
from app.schemas.service_ticket import service_tickets_schema
from app import limiter, cache
import jwt
from config import Config
from datetime import datetime, timezone

@user_bp.post('/login')
@limiter.limit("5 per minute")
def login():
    """Login with email and password"""
    data = request.get_json()
    validated_data = login_schema.load(data)
    
    user = User.query.filter_by(email=validated_data['email']).first()
    if not user or not user.check_password(validated_data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = encode_token(user.id)
    return jsonify({
        'message': 'Successfully logged in',
        'token': token
    })

@user_bp.post('/register')
@limiter.limit("3 per hour")
def register():
    """Register a new user"""
    data = request.get_json()
    validated_data = user_schema.load(data)
    
    if User.query.filter_by(email=validated_data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    user = User(
        name=validated_data['name'],
        email=validated_data['email'],
        phone=validated_data['phone']
    )
    user.set_password(validated_data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully registered',
        'user': user_schema.dump(user)
    }), 201

@user_bp.get('')  # Changed from '/users'
@cache.cached(timeout=300)
def get_users():
    """Get paginated list of users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = User.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'users': users_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@user_bp.get('/my-tickets')
@token_required
@limiter.limit("30 per minute")
@cache.memoize(300)
def get_my_tickets(user_id):
    """Get all service tickets for the authenticated user"""
    tickets = ServiceTicket.query.filter_by(user_id=user_id).all()
    return jsonify(service_tickets_schema.dump(tickets))

@user_bp.put('/<int:id>')
@token_required
def update_user(user_id, id):
    """Update user information - only allowed for the authenticated user"""
    if user_id != id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    user = User.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(user, key, value)
    
    db.session.commit()
    return jsonify(user_schema.dump(user))

@user_bp.delete('/<int:id>')
@token_required
def delete_user(user_id, id):
    """Delete user account and optionally all associated tickets"""
    if user_id != id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    try:
        user = User.query.get_or_404(id)
        force_delete = request.args.get('force', '').lower() == 'true'
        
        # Check if user has service tickets
        if user.service_tickets and not force_delete:
            return jsonify({
                'message': 'Cannot delete user with active service tickets. Use ?force=true to delete everything.',
                'ticket_count': len(user.service_tickets)
            }), 400
        
        # If force delete, remove all relationships first
        if force_delete:
            for ticket in user.service_tickets:
                ticket.mechanics.clear()
                ticket.parts.clear()
                db.session.delete(ticket)
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User and all associated data deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': 'Failed to delete user',
            'error': str(e)
        }), 500