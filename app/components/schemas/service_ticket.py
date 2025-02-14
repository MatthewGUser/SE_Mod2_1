from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE

class ServiceTicketSchema(Schema):
    """Schema for serializing/deserializing service tickets"""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    status = fields.Str(required=True)
    priority = fields.Str(required=True)
    user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Relationships
    user = fields.Nested('UserSchema', exclude=('service_tickets', 'password'), dump_only=True)
    mechanics = fields.List(fields.Nested('MechanicSchema', only=('id', 'name')), dump_only=True)
    parts = fields.List(fields.Nested('InventorySchema', only=('id', 'name', 'price')), dump_only=True)
    
    # Request-only fields
    mechanic_ids = fields.List(fields.Int(), load_only=True, required=False)
    part_ids = fields.List(fields.Int(), load_only=True, required=False)

    class Meta:
        unknown = EXCLUDE

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)