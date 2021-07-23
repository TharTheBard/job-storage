import os
import arrow
import logging
import logging.config
import typing
import datetime as dt
import decimal
import uuid
from json import JSONEncoder

from flask import Flask, request
# Restx monkey patch start
#import flask.scaffold
#flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
# Restx monkey patch end
from flask.logging import default_handler
from flask_restx import Api
from marshmallow.exceptions import ValidationError

from . import db
from .log import RequestFilter
from . import routes
from .custom_exceptions import JobStorageException


class JobStorage(Flask):
    db: db.Storage
    api: Api

    LOG_NAME = "flask.app"

    def __init__(self, *args, **kwargs) -> None:
        super(JobStorage, self).__init__(*args, **kwargs)
        # parse config
        self.config.from_pyfile('../config.py')
        self.config.from_pyfile('/etc/job-storage/config.py', silent=True)
        # set logger
        self.logger = logging.getLogger(self.LOG_NAME)
        self.set_logger()

        # set up db
        self.logger.info('DB - verifying ...')
        self.db = db.Storage(
            user=self.config["DB_USER"],
            password=self.config["DB_PASS"],
            host=self.config["DB_HOST"],
            port=self.config["DB_PORT"],
            path=self.config["DB_PATH"],
        )

        # create REST Api
        doc = '/'
        if not self.config.get('SWAGGER_UI_DOC'):
            doc = False
        self.api = Api(
            app=self,
            doc=doc,
            title='Job Storage API',
            prefix="/api",
        )
        self.api.add_namespace(routes.jobs.api, path='/jobs')
        self.api.add_namespace(routes.candidates.api, path='/candidates')
        self.api.add_namespace(routes.skills.api, path='/skills')

    def set_logger(self):
        """
        Set up logging from current app config
        Uses LOG_CONF setting
        """

        self.logger.addFilter(RequestFilter())
        print("logger name : {}".format(self.logger.name))
        if self.config.get('LOG_CONF', False):
            print("found special LOG_CONF")
            logging.config.dictConfig(self.config.get('LOG_CONF'))
            self.logger.removeHandler(default_handler)
            print("logger {} set up successfully".format(self.logger.name))
            self.logger.info('LOG_CONF resolved and set up')
        else:
            print('using default flask logger set up')
            self.logger.info('using default flask logger set up')
        self.logger.info('App logger bound')

    def dispose(self) -> None:
        """This has the effect of fully closing all **currently checked in** connections to outer world"""
        self.db.client.dispose()


class ExtendedJSONEncoder(JSONEncoder):
    """
    JSON encoder capable to convert datetime object into iso-string
    """

    def default(self, obj):
        if isinstance(obj, dt.datetime):
            return arrow.get(obj).isoformat().replace("+00:00", "Z")

        if isinstance(obj, dt.date):
            return arrow.get(obj).isoformat().replace("+00:00", "Z")

        if isinstance(obj, decimal.Decimal):
            return float(obj)

        return JSONEncoder.default(self, obj)


app = JobStorage(
    __name__,
)

app.config['RESTX_JSON'] = {
    'separators': (',', ':'),
    'indent': 0,
    'cls': ExtendedJSONEncoder
}


@app.before_request
def get_request_id():
    if not getattr(request, 'request_id', None):
        request.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    app.logger.info(f"Requested - {request.path}")


@app.api.errorhandler(JobStorageException)
def handle_data_server_exception(error):
    """Return a custom message"""
    app.logger.warning(f"{error.response}: {str(error)}")
    return {'error': error.response}, error.status_code


@app.api.errorhandler(ValidationError)
def handle_data_server_exception(error):
    """Return a custom message and 400 status code"""
    app.logger.warning(f"Error while validating input data: {error}")
    error.data = {"error": "Validation error",
                  "fields": error.messages}
    return error.data, 400


app.dispose()
