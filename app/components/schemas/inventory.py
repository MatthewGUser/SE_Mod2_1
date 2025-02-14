from marshmallow import Schema, fields

class InventorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    service_tickets = fields.List(fields.Nested('ServiceTicketSchema', exclude=('parts',)))

inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)