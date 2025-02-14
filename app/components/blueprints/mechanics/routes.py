from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from . import mechanic_bp
from app.models import Mechanic, ServiceTicket, User, db
from app.components.schemas.mechanic import mechanic_schema, mechanics_schema
from app import limiter, cache

# Create mechanic
@mechanic_bp.route('', methods=['POST'])
@jwt_required()
def create_mechanic():
    """Create a new mechanic"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), 400

        # Only use valid fields for Mechanic model
        mechanic = Mechanic(
            name=data['name'],
            specialty=data.get('specialty', ''),
            phone=data['phone']
        )
        
        db.session.add(mechanic)
        db.session.commit()
        
        return jsonify(mechanic.to_dict()), 201

    except KeyError as e:
        return jsonify({'message': f'Missing required field: {str(e)}'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': 'Database error', 'error': str(e)}), 500

# Get all mechanics with pagination
@mechanic_bp.route('', methods=['GET'])
@jwt_required()
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
    try:
        mechanic = db.session.get(Mechanic, id)
        if not mechanic:
            return jsonify({'message': 'Mechanic not found'}), 404
            
        # Include tickets in response
        result = mechanic.to_dict()
        result['tickets'] = [t.id for t in mechanic.service_tickets]
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'message': 'Error retrieving mechanic', 'error': str(e)}), 500

# Update mechanic
@mechanic_bp.put('/<int:id>')
@jwt_required()  # Changed from @token_required
@limiter.limit("20 per minute")
def update_mechanic(id):  # Removed user_id parameter
    """Update mechanic information"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'message': 'Admin privileges required'}), 403

        mechanic = Mechanic.query.get_or_404(id)
        data = request.get_json()
        validated_data = mechanic_schema.load(data, partial=True)
        
        for key, value in validated_data.items():
            setattr(mechanic, key, value)
        
        db.session.commit()
        return jsonify(mechanic_schema.dump(mechanic))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete mechanic
@mechanic_bp.delete('/<int:id>')
@jwt_required()  # Changed from @token_required
@limiter.limit("10 per hour")
def delete_mechanic(id):  # Removed user_id parameter
    """Delete mechanic"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'message': 'Admin privileges required'}), 403

        mechanic = Mechanic.query.get_or_404(id)
        db.session.delete(mechanic)
        db.session.commit()
        return jsonify({'message': 'Mechanic deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@mechanic_bp.get('/tickets')
@jwt_required()  # Changed from @token_required
@limiter.limit("100 per minute")
def get_assigned_tickets():  # Removed mechanic_id parameter
    """Get tickets assigned to mechanic"""
    try:
        current_user_id = get_jwt_identity()
        mechanic = Mechanic.query.filter_by(user_id=current_user_id).first()
        
        if not mechanic:
            return jsonify({'message': 'Mechanic not found'}), 404
            
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
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@mechanic_bp.post('/<int:mechanic_id>/tickets/<int:ticket_id>')
@jwt_required()
@limiter.limit("10 per hour")
def assign_mechanic_to_ticket(mechanic_id, ticket_id):
    """Assign mechanic to service ticket"""
    try:
        # Get mechanic and ticket
        mechanic = db.session.get(Mechanic, mechanic_id)
        if not mechanic:
            return jsonify({'message': 'Mechanic not found'}), 404

        ticket = db.session.get(ServiceTicket, ticket_id)
        if not ticket:
            return jsonify({'message': 'Service ticket not found'}), 404

        # Assign ticket to mechanic
        mechanic.service_tickets.append(ticket)
        db.session.commit()

        return jsonify({
            'message': 'Mechanic assigned successfully',
            'mechanic': mechanic.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': 'Failed to assign mechanic',
            'error': str(e)
        }), 500