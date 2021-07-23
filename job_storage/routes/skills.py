from flask_restx import Namespace, Resource
from flask import current_app as app

api = Namespace(
    'skills',
    description='Skills related endpoints',
)


@api.route('')
class SkillsList(Resource):
    """List all jobs"""

    def get(self):
        return {"data": app.db.list_skills()}, 200
