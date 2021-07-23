from flask_restx import Model, fields, Namespace, Resource
from flask import current_app as app
from dataclasses import asdict, fields as d_fields

from job_storage import validators as v

api = Namespace(
    'candidates',
    description='Candidates related endpoints',
)


@api.route('')
class Candidates(Resource):
    """List/insert candidates"""

    def get(self):
        return {"data": app.db.list_candidates()}, 200

    @api.expect(api.model('insert_candidate_payload', v.candidates.InsertCandidateSchema.restx_expect_dict()))
    def post(self):
        payload = v.candidates.InsertCandidateSchema().load(api.payload or {})
        app.db.insert_candidate(payload)
        return {"message": "Candidate added successfully"}, 201


@api.route('/<int:candidate_id>')
class CandidateDetail(Resource):
    """Candidate detail and operations"""
    def get(self, candidate_id):
        return {"data": app.db.find_candidate(candidate_id)}, 200

    @api.expect(api.model('insert_candidate_payload', v.candidates.InsertCandidateSchema.restx_expect_dict()))
    def put(self, candidate_id):
        payload = v.candidates.InsertCandidateSchema().load(api.payload or {})
        app.db.force_insert_candidate(candidate_id, payload)
        return {"message": "Candidate updated/added successfully"}, 201

    def delete(self, candidate_id):
        app.db.delete_candidate(candidate_id)
        return {"message": "Candidate deleted successfully"}, 202


@api.route('/<int:candidate_id>/apply/jobs/<int:job_id>')
class CandidateDetail(Resource):
    """Apply candidate for a job"""
    def post(self, candidate_id, job_id):
        app.db.apply_candidate(candidate_id, job_id)
        return {"message": "Candidate applied successfully"}, 201
