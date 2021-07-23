from marshmallow import fields, post_load, ValidationError, validates_schema, validates
from dataclasses import dataclass

from ._utils import JobStorageSchema


@dataclass(frozen=True)
class InsertJob:
    title: str
    salary: int
    description: str


class InsertJobSchema(JobStorageSchema):
    title = fields.String(allow_none=False, metadata={"example": "Job title"})
    salary = fields.Integer(allow_none=False, metadata={"example": "50000"})
    description = fields.String(allow_none=True, missing=None,
                                metadata={"example": "This is a (not so) lengthy job description"})

    @post_load
    def load_func(self, data, **kwargs):
        return InsertJob(**data)
