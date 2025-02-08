from flask import jsonify, request
from . import inventory_bp
from app.models import Inventory, db
from app.schemas.inventory import inventory_schema, inventories_schema
from app.utils.util import token_required
from app import limiter, cache
from sqlalchemy.exc import IntegrityError

@inventory_bp.post('')
@token_required
@limiter.limit("30 per minute")
def create_part(user_id):    # Changed from customer_id
    """Create a new inventory part"""
    try:
        data = request.get_json()
        validated_data = inventory_schema.load(data)
        
        part = Inventory(**validated_data)
        db.session.add(part)
        db.session.commit()
        
        return jsonify(inventory_schema.dump(part)), 201
        
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

@inventory_bp.get('')
@cache.cached(timeout=300)
def get_parts():
    """Get paginated list of inventory parts"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Inventory.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'parts': inventories_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@inventory_bp.put('/<int:part_id>')
@token_required
@limiter.limit("30 per minute")
def update_part(user_id, part_id):
    """Update an inventory part"""
    try:
        part = Inventory.query.get_or_404(part_id)
        data = request.get_json()
        validated_data = inventory_schema.load(data, partial=True)
        
        for key, value in validated_data.items():
            setattr(part, key, value)
        
        db.session.commit()
        return jsonify(inventory_schema.dump(part))
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'message': 'Database error occurred',
            'error': 'integrity_error'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': 'Failed to update part',
            'error': str(e)
        }), 500

@inventory_bp.delete('/<int:part_id>')
@token_required
@limiter.limit("10 per hour")
def delete_part(user_id, part_id):
    """Delete an inventory part"""
    try:
        part = Inventory.query.get_or_404(part_id)
        
        # Check if part is used in any service tickets
        if part.service_tickets:
            return jsonify({
                'message': 'Cannot delete part that is used in service tickets',
                'ticket_count': len(part.service_tickets)
            }), 400
        
        db.session.delete(part)
        db.session.commit()
        
        return jsonify({'message': 'Part deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': 'Failed to delete part',
            'error': str(e)
        }), 500