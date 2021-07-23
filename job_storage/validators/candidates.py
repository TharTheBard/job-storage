from marshmallow import fields, post_load
from dataclasses import dataclass

from ._utils import JobStorageSchema


@dataclass(frozen=True)
class InsertCandidate:
    full_name: str
    expected_salary: int
    skills: list


class InsertCandidateSchema(JobStorageSchema):
    full_name = fields.String(required=True, metadata={"example": "John Smith"})
    expected_salary = fields.Integer(required=True, metadata={"example": "54321"})
    skills = fields.List(fields.String, allow_none=True, missing=[], metadata={"example": ["Python", "Flask"]})

    @post_load
    def load_func(self, data, **kwargs):
        return InsertCandidate(**data)
