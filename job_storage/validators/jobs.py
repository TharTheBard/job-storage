from marshmallow import fields, post_load, ValidationError, validates_schema, validates
from dataclasses import dataclass

from ._utils import JobStorageSchema


@dataclass(frozen=True)
class InsertJob:
    title: str
    salary: int
    description: str


class InsertJobSchema(JobStorageSchema):
    title = fields.String(required=True, metadata={"example": "Job title"})
    salary = fields.Integer(required=True, metadata={"example": "50000"})
    description = fields.String(required=True, metadata={"example": "This is a (not so) lengthy job description"})

    @post_load
    def load_func(self, data, **kwargs):
        return InsertJob(**data)
