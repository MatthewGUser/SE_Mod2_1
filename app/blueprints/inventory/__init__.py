from flask import Blueprint

inventory_bp = Blueprint('invetory_bp', __name__)

from . import routes
