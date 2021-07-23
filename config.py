#!/usr/bin/python3
# -*- coding: utf-8 -*-

DEBUG = True
SWAGGER_UI_DOC = True

DB_USER = "postgres"
DB_PASS = "aweakpassword"
DB_HOST = "postgres-jobs"
DB_PORT = 5432
DB_PATH = "jobs_db"

DB_POOL_SIZE = 1
DB_POOL_RECYCLE = 17 * 60
DB_ISOLATION_LEVEL = 'REPEATABLE READ'

LOG_CONF = {  # see https://www.python.org/dev/peps/pep-0391/
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'general': {
            'format': 'job_storage ip=%(client_ip)s rid=%(request_id)s [%(levelname)s] %(message)s'
        },
    },
    'handlers': {
        'sysloc5': {
            'class': 'logging.handlers.SysLogHandler',
            'address': ('rsyslog', 514),
            'facility': "local5",
            'formatter': 'general', }
    },
    'loggers': {
        'flask.app': {
            'level': 'DEBUG',
            'handlers': ['sysloc5'],
            'propagate': False}
    }
}
