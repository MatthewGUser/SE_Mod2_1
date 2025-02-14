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
    current_user = db.session.get(User, get_jwt_identity())
    
    if not current_user or not current_user.is_admin:
        return jsonify({'message': 'Admin privileges required'}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        part = Part(
            name=data['name'],
            part_number=data['part_number'],
            price=float(data['price']),
            quantity=int(data['quantity'])
        )
        
        db.session.add(part)
        db.session.commit()
        return jsonify(part.to_dict()), 201

    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({'message': 'Invalid data format'}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Part number already exists'}), 400

@inventory_bp.route('', methods=['GET'])  # Changed from '/parts'
def get_parts():
    """Get all parts"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        parts = Part.query.paginate(page=page, per_page=per_page)
        return jsonify({
            'items': [part.to_dict() for part in parts.items],
            'total': parts.total,
            'page': parts.page,
            'pages': parts.pages,
            'per_page': parts.per_page
        })
    except Exception as e:
        return jsonify({'message': 'Error retrieving parts', 'error': str(e)}), 500

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
    current_user = db.session.get(User, get_jwt_identity())
    
    if not current_user or not current_user.is_admin:
        return jsonify({'message': 'Admin privileges required'}), 403

    try:
        part = Part.query.get_or_404(part_id)
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Type conversion for numeric fields
        if 'price' in data:
            data['price'] = float(data['price'])
        if 'quantity' in data:
            data['quantity'] = int(data['quantity'])

        # Update only valid fields
        valid_fields = ['name', 'part_number', 'price', 'quantity']
        for key, value in data.items():
            if key in valid_fields:
                setattr(part, key, value)

        db.session.commit()
        return jsonify(part.to_dict())

    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({'message': 'Invalid data format'}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Part number already exists'}), 400

@inventory_bp.route('/<int:part_id>', methods=['DELETE'])  # Changed from '/parts/<int:part_id>'
@jwt_required()
def delete_part(part_id):
    """Delete a part"""
    current_user = db.session.get(User, get_jwt_identity())
    
    if not current_user or not current_user.is_admin:
        return jsonify({'message': 'Admin privileges required'}), 403

    part = db.session.get(Part, part_id)
    if not part:
        return jsonify({'message': 'Part not found'}), 404
        
    db.session.delete(part)
    db.session.commit()
    return jsonify({'message': 'Part deleted successfully'})