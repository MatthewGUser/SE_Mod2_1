from flask import jsonify, request
from . import service_ticket_bp
from app.models import ServiceTicket, Mechanic, Inventory, db  # Added Inventory import
from app.utils.util import token_required
from app import limiter, cache
from app.schemas.service_ticket import service_ticket_schema, service_tickets_schema
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Create service ticket
@service_ticket_bp.post('')
@token_required
@limiter.limit("20 per minute")
def create_ticket(user_id):  # Changed from customer_id
    """Create a new service ticket with optional mechanic and part assignments"""
    try:
        data = request.get_json()
        validated_data = service_ticket_schema.load(data)
        
        # No need to parse the date as marshmallow handles it
        ticket = ServiceTicket(
            user_id=user_id,  # Changed from customer_id
            VIN=validated_data['VIN'],
            description=validated_data['description'],
            service_date=validated_data['service_date']  # Date is already converted by schema
        )
        
        # Handle mechanic assignments
        if 'mechanic_ids' in validated_data:
            mechanics = Mechanic.query.filter(Mechanic.id.in_(validated_data['mechanic_ids'])).all()
            if len(mechanics) != len(validated_data['mechanic_ids']):
                return jsonify({'message': 'One or more mechanic IDs are invalid'}), 400
            ticket.mechanics.extend(mechanics)
        
        # Handle part assignments
        if 'part_ids' in validated_data:
            parts = Inventory.query.filter(Inventory.id.in_(validated_data['part_ids'])).all()
            if len(parts) != len(validated_data['part_ids']):
                return jsonify({'message': 'One or more part IDs are invalid'}), 400
            ticket.parts.extend(parts)
        
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify(service_ticket_schema.dump(ticket)), 201
        
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

# Get all tickets (paginated)
@service_ticket_bp.get('')
@token_required
@cache.cached(timeout=300)
def get_tickets(user_id):    # Changed from customer_id
    """Get paginated list of service tickets"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = ServiceTicket.query.filter_by(user_id=user_id).paginate(    # Changed from customer_id
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
@token_required
def get_ticket(user_id, ticket_id):    # Changed from customer_id
    """Get a specific service ticket"""
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    
    if ticket.user_id != user_id:    # Changed from customer_id
        return jsonify({'message': 'Unauthorized'}), 403
        
    return jsonify(service_ticket_schema.dump(ticket))

# Update ticket
@service_ticket_bp.put('/<int:ticket_id>')
@token_required
@limiter.limit("30 per minute")
def update_ticket(user_id, ticket_id):    # Changed from customer_id
    """Update a service ticket"""
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    
    if ticket.user_id != user_id:    # Changed from customer_id
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    validated_data = service_ticket_schema.load(data, partial=True)
    
    for key, value in validated_data.items():
        setattr(ticket, key, value)  # Marshmallow already handles date conversion
    
    db.session.commit()
    return jsonify(service_ticket_schema.dump(ticket))

# Delete ticket
@service_ticket_bp.delete('/<int:ticket_id>')
@token_required
@limiter.limit("10 per hour")
def delete_ticket(user_id, ticket_id):
    """Delete a service ticket"""
    try:
        # First check if ticket exists
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        
        # Check authorization
        if ticket.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Remove relationships before deleting
        ticket.mechanics.clear()
        ticket.parts.clear()
        
        db.session.delete(ticket)
        db.session.commit()
        
        return jsonify({'message': 'Service ticket deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting ticket: {str(e)}")  # Add logging for debugging
        return jsonify({
            'message': 'Failed to delete ticket',
            'error': str(e)
        }), 500

# Update mechanics assigned to a service ticket
@service_ticket_bp.put('/<int:ticket_id>/edit')
@token_required
@limiter.limit("30 per minute")
def update_ticket_mechanics(user_id, ticket_id):    # Changed from customer_id
    """Update mechanics assigned to a service ticket"""
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    
    # Verify ticket belongs to authenticated customer
    if ticket.user_id != user_id:    # Changed from customer_id
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