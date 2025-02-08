from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE  # Added EXCLUDE import

class UserSchema(Schema):
    """Schema for serializing/deserializing users"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    phone = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    
    # Relationships
    service_tickets = fields.List(fields.Nested('ServiceTicketSchema', exclude=('user',)), dump_only=True)

    class Meta:
        unknown = EXCLUDE

class LoginSchema(Schema):
    """Schema for login validation"""
    email = fields.Str(required=True)
    password = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE

user_schema = UserSchema()
users_schema = UserSchema(many=True)
login_schema = LoginSchema()