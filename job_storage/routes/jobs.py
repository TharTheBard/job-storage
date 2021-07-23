from flask_restx import Namespace, Resource
from flask import current_app as app

from job_storage import validators as v

api = Namespace(
    'jobs',
    description='Job offers related endpoints',
)


@api.route('')
class JobsList(Resource):
    """List/insert jobs"""
    def get(self):
        return {"data": app.db.list_jobs()}, 200

    @api.expect(api.model('insert_job_payload', v.jobs.InsertJobSchema.restx_expect_dict()))
    def post(self):
        payload = v.jobs.InsertJobSchema().load(api.payload or {})
        app.db.insert_job(payload)
        return {"message": "Job added successfully"}, 201


@api.route('/<int:job_id>')
class JobDetail(Resource):
    """Job detail and operations"""
    def get(self, job_id):
        return {"data": app.db.find_job(job_id)}, 200

    @api.expect(api.model('insert_job_payload', v.jobs.InsertJobSchema.restx_expect_dict()))
    def put(self, job_id):
        payload = v.jobs.InsertJobSchema().load(api.payload or {})
        app.db.force_insert_job(job_id, payload)
        return {"message": "Job updated/added successfully"}, 201

    def delete(self, job_id):
        app.db.delete_job(job_id)
        return {"message": "Job deleted successfully"}, 202
