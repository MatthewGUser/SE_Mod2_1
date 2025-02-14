from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Part, User
from sqlalchemy.exc import IntegrityError
from . import inventory_bp
from sqlalchemy import select
from flask_sqlalchemy import SQLAlchemy

# Add some debug logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@inventory_bp.route('', methods=['POST'])  # Removed trailing slash
@jwt_required()
def create_part():
    """Create a new part"""
    logger.debug("Creating part...")
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['name', 'part_number', 'price', 'quantity']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'message': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400

        # Create part with data validation
        try:
            part = Part(
                name=str(data['name']).strip(),
                part_number=str(data['part_number']).strip(),
                price=float(data['price']),
                quantity=int(data['quantity'])
            )
        except (ValueError, TypeError) as e:
            return jsonify({
                'message': 'Invalid data format',
                'error': str(e)
            }), 400

        db.session.add(part)
        db.session.commit()
        
        # Return format matching test expectations
        response_data = part.to_dict()
        response_data['id'] = part.id
        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'message': 'An unexpected error occurred',
            'error': str(e)
        }), 500

@inventory_bp.route('', methods=['GET'])
def get_parts():
    """Get all parts - supports both paginated and non-paginated responses"""
    try:
        # Check if pagination parameters are provided
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)

        if page is not None and per_page is not None:
            # Paginated response
            pagination = Part.query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            return jsonify({
                'items': [part.to_dict() for part in pagination.items],
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total
            }), 200
        else:
            # Non-paginated response - return all parts as array
            parts = Part.query.all()
            return jsonify([part.to_dict() for part in parts]), 200

    except Exception as e:
        logger.error(f"Error retrieving parts: {str(e)}")
        return jsonify({
            'message': 'Error retrieving parts',
            'error': str(e)
        }), 500

@inventory_bp.route('/<int:part_id>', methods=['GET'])
def get_part(part_id):
    """Get a specific part"""
    try:
        # Using session.get() instead of query.get()
        part = db.session.get(Part, part_id)
        if not part:
            return jsonify({'message': 'Part not found'}), 404
        return jsonify(part.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Error retrieving part', 'error': str(e)}), 500

@inventory_bp.route('/<int:part_id>', methods=['PUT'])  # Changed from '/parts/<int:part_id>'
@jwt_required()
def update_part(part_id):
    """Update a part"""
    try:
        part = Part.query.get_or_404(part_id)
        data = request.get_json()
        logger.debug(f"Updating part {part_id} with data: {data}")
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Update fields if provided, with enhanced validation
        if 'name' in data and data['name']:
            part.name = str(data['name']).strip()
        if 'part_number' in data and data['part_number']:
            part.part_number = str(data['part_number']).strip()
        if 'price' in data:
            try:
                new_price = float(data['price'])
                if new_price >= 0:
                    part.price = new_price
                else:
                    return jsonify({'message': 'Price cannot be negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'message': 'Invalid price format'}), 400
        if 'quantity' in data:
            try:
                new_quantity = int(data['quantity'])
                if new_quantity >= 0:
                    part.quantity = new_quantity
                else:
                    return jsonify({'message': 'Quantity cannot be negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'message': 'Invalid quantity format'}), 400

        db.session.commit()
        
        # Return the updated part data directly instead of nested in a response
        return jsonify(part.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating part: {str(e)}")
        return jsonify({
            'message': 'Failed to update part',
            'error': str(e)
        }), 500

@inventory_bp.route('/<int:part_id>', methods=['DELETE'])  # Changed from '/parts/<int:part_id>'
@jwt_required()
def delete_part(part_id):
    """Delete a part"""
    part = db.session.get(Part, part_id)
    if not part:
        return jsonify({'message': 'Part not found'}), 404
        
    db.session.delete(part)
    db.session.commit()
    return jsonify({'message': 'Part deleted successfully'})