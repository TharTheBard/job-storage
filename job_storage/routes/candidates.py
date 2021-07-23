from flask_restx import Model, fields, Namespace, Resource
from flask import current_app as app
from dataclasses import asdict, fields as d_fields

from job_storage import validators as v

api = Namespace(
    'candidates',
    description='Candidates related endpoints',
)
