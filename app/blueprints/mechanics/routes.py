from flask import jsonify, request
from . import mechanic_bp
from app.models import Mechanic, ServiceTicket, db
from sqlalchemy import func
from app import limiter, cache
from app.utils.util import token_required
from app.schemas.mechanic import mechanic_schema, mechanics_schema  # Add these imports
from sqlalchemy.exc import IntegrityError

# Create mechanic
@mechanic_bp.post('')
@token_required
@limiter.limit("10 per hour")
def create_mechanic(user_id):    # Changed from customer_id
    """Create a new mechanic"""
    try:
        data = request.get_json()
        validated_data = mechanic_schema.load(data)
        
        # Check if email already exists
        if Mechanic.query.filter_by(email=validated_data['email']).first():
            return jsonify({
                'message': 'Email already registered',
                'error': 'duplicate_email'
            }), 400
        
        mechanic = Mechanic(**validated_data)
        db.session.add(mechanic)
        db.session.commit()
        
        return jsonify(mechanic_schema.dump(mechanic)), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'message': 'Database error occurred',
            'error': 'integrity_error'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': 'An error occurred',
            'error': str(e)
        }), 500

# Get all mechanics with pagination
@mechanic_bp.get('')
@cache.cached(timeout=300)
def get_mechanics():
    """Get paginated list of mechanics"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Mechanic.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'mechanics': mechanics_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

# Get single mechanic
@mechanic_bp.get('/<int:id>')
@cache.memoize(300)
def get_mechanic(id):
    """Get mechanic by ID"""
    mechanic = Mechanic.query.get_or_404(id)
    return jsonify(mechanic_schema.dump(mechanic))

# Update mechanic
@mechanic_bp.put('/<int:id>')
@token_required
@limiter.limit("20 per minute")
def update_mechanic(user_id, id):    # Changed from customer_id
    """Update mechanic information"""
    mechanic = Mechanic.query.get_or_404(id)
    data = request.get_json()
    validated_data = mechanic_schema.load(data, partial=True)
    
    for key, value in validated_data.items():
        setattr(mechanic, key, value)
    
    db.session.commit()
    return jsonify(mechanic_schema.dump(mechanic))

# Delete mechanic
@mechanic_bp.delete('/<int:id>')
@token_required
@limiter.limit("10 per hour")
def delete_mechanic(user_id, id):    # Changed from customer_id
    """Delete mechanic"""
    mechanic = Mechanic.query.get_or_404(id)
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({'message': 'Mechanic deleted successfully'})

@mechanic_bp.get('/tickets')
@token_required
@limiter.limit("100 per minute")
def get_assigned_tickets(mechanic_id):
    mechanic = Mechanic.query.get_or_404(mechanic_id)
    tickets = mechanic.service_tickets
    return jsonify({
        'tickets': [
            {
                'id': ticket.id,
                'VIN': ticket.VIN,
                'description': ticket.description,
                'service_date': ticket.service_date
            }
            for ticket in tickets
        ]
    })