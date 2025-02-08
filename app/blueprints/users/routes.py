from flask import jsonify
from app.blueprints.user import user_bp
from app.models import User
from app.extensions import limiter
from .schemas import user_schema, users_schema
from app.utils.util import encode_token, token_required

@user_bp.route("/login", methods=['POST']
def login():
	    #login route logic from above
	
	
@user_bp.route('/', methods=['DELETE'])
@token_rquired
def delete_user(user_id): #Recieving user_id from the token
    query = select(User).where(User.id == user_id)
    user = db.session.execute(query).scalars().first()
		
		db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succesfully deleted user {user_id}"})