from marshmallow import Schema, fields, validate

class MechanicSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str(required=True)
    salary = fields.Float(required=True)
    service_tickets = fields.List(fields.Nested('ServiceTicketSchema', exclude=('mechanics',)))

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)