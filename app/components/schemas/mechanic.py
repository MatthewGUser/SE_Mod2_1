from marshmallow import Schema, fields, EXCLUDE, validate

class MechanicSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    phone = fields.Str(required=True)
    specialty = fields.Str(required=True)

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)