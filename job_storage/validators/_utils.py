from marshmallow import Schema
from flask_restx import fields

marshmallow_to_restx_map = {
    "Integer": fields.Integer,
    "String": fields.String,
    "DateTime": fields.DateTime,
    "Decimal": fields.Float,
    "List": fields.List
}


class JobStorageSchema(Schema):
    @classmethod
    def restx_expect_dict(cls):
        schema_fields = cls._declared_fields
        result = {}
        for field in schema_fields:
            restx_field_args = schema_fields[field].metadata
            if schema_fields[field].__class__.__name__ == "List":
                result[field] = marshmallow_to_restx_map[schema_fields[field].__class__.__name__](
                    marshmallow_to_restx_map[schema_fields[field].inner.__class__.__name__](),
                    **restx_field_args
                )
            else:
                result[field] = marshmallow_to_restx_map[schema_fields[field].__class__.__name__](**restx_field_args)
        return result
