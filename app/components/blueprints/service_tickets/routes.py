from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import ServiceTicket, Mechanic, Inventory, Part, db  # Added Part to imports
from app.components.schemas.service_ticket import service_ticket_schema, service_tickets_schema
from . import service_ticket_bp
from app import cache, limiter
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError

# Create service ticket
@service_ticket_bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_ticket():
    """Create a new service ticket"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), 400

        user_id = get_jwt_identity()

        # Set defaults for required fields
        data.setdefault('title', f"Service Ticket - {datetime.now().strftime('%Y-%m-%d')}")
        data.setdefault('status', 'pending')
        data.setdefault('priority', 'normal')
        
        # Create ticket first
        ticket = ServiceTicket(
            title=data['title'],
            description=data['description'],
            status=data['status'],
            priority=data['priority'],
            user_id=user_id  # Use the user_id from token
        )

        db.session.add(ticket)
        db.session.flush()

        # Handle mechanics if provided
        if 'mechanic_ids' in data:
            mechanics = Mechanic.query.filter(Mechanic.id.in_(data['mechanic_ids'])).all()
            for mechanic in mechanics:
                ticket.mechanics.append(mechanic)

        # Handle parts if provided
        if 'part_ids' in data:
            parts = Inventory.query.filter(Inventory.id.in_(data['part_ids'])).all()  # Changed from Part to Inventory
            for part in parts:
                ticket.parts.append(part)
        
        db.session.commit()
        result = service_ticket_schema.dump(ticket)
        return jsonify(result), 201

    except ValidationError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Validation error',
            'message': str(e.messages)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create ticket',
            'message': str(e)
        }), 400

# Get all tickets (paginated)
@service_ticket_bp.get('')
@jwt_required()
@cache.cached(timeout=300)
def get_tickets():
    """Get paginated list of service tickets"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = ServiceTicket.query.filter_by(user_id=user_id).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'tickets': service_tickets_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

# Get single ticket
@service_ticket_bp.get('/<int:ticket_id>')
@jwt_required()
def get_ticket(ticket_id):
    """Get a specific service ticket"""
    try:
        user_id = get_jwt_identity()
        
        # Convert user_id to int if it's a string
        if isinstance(user_id, str):
            user_id = int(user_id)
            
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        
        # Verify ownership
        if ticket.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        # Return single ticket with relationships
        result = service_ticket_schema.dump(ticket)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve ticket',
            'message': str(e)
        }), 400

# Update ticket
@service_ticket_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_ticket(id):
    """Update a service ticket"""
    try:
        current_user_id = get_jwt_identity()
        ticket = ServiceTicket.query.get_or_404(id)
        
        # Check if the token is an integer or string
        if isinstance(current_user_id, str):
            current_user_id = int(current_user_id)
        
        # Verify ownership
        if ticket.user_id != current_user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        
        # Update fields
        for field in ['status', 'priority', 'title', 'description']:
            if field in data:
                setattr(ticket, field, data[field])
            
        db.session.commit()
        
        return jsonify(service_ticket_schema.dump(ticket)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update ticket',
            'message': str(e)
        }), 400

# Delete ticket
@service_ticket_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_ticket(id):
    """Delete a service ticket"""
    try:
        user_id = get_jwt_identity()
        ticket = ServiceTicket.query.get_or_404(id)
        
        # Convert user_id to int if needed
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        # Verify ownership
        if ticket.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Remove relationships first
        ticket.mechanics = []
        ticket.parts = []
        
        db.session.delete(ticket)
        db.session.commit()
        
        # Return 204 No Content status code
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete ticket',
            'message': str(e)
        }), 400

# Update mechanics assigned to a service ticket
@service_ticket_bp.put('/<int:ticket_id>/edit')
@jwt_required()
@limiter.limit("30 per minute")
def update_ticket_mechanics(ticket_id):
    """Update mechanics assigned to a service ticket"""
    user_id = get_jwt_identity()
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    
    # Verify ticket belongs to authenticated customer
    if ticket.user_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    remove_ids = data.get('remove_ids', [])
    add_ids = data.get('add_ids', [])
    
    # Remove mechanics
    mechanics_to_remove = Mechanic.query.filter(Mechanic.id.in_(remove_ids)).all()
    for mechanic in mechanics_to_remove:
        if mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)
    
    # Add mechanics
    mechanics_to_add = Mechanic.query.filter(Mechanic.id.in_(add_ids)).all()
    for mechanic in mechanics_to_add:
        if mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Mechanics updated successfully',
        'mechanics': [{'id': m.id, 'name': m.name} for m in ticket.mechanics]
    })

@service_ticket_bp.route('/my-tickets')
@jwt_required()
@cache.cached(timeout=300)
def get_my_tickets():
    """Get all service tickets for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        tickets = ServiceTicket.query.filter_by(user_id=user_id).all()
        result = service_tickets_schema.dump(tickets)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve tickets',
            'message': str(e)
        }), 400