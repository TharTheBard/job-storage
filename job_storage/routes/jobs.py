from flask_restx import Model, fields, Namespace, Resource
from flask import current_app as app
from dataclasses import asdict, fields as d_fields

from job_storage import validators as v

api = Namespace(
    'jobs',
    description='Job offers related endpoints',
)


@api.route('')
class Jobs(Resource):
    """List all jobs"""

    def get(self):
        return {"data": app.db.list_jobs()}, 200

    @api.expect(api.model('insert_job_payload', v.jobs.InsertJobSchema.restx_expect_dict()))
    def post(self):
        payload = v.jobs.InsertJobSchema().load(api.payload or {})
        app.db.insert_job(payload)
        return {"message": "Job added successfully"}, 201
