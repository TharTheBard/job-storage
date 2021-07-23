# in flask app: flask_app.logger.addFilter(RequestFilter())
import logging
import uuid

from flask import request


class RequestFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """
    DEFAULT = 'n-a'
    REQUEST_HEADER = 'X-Request-ID'
    CORRELATION_HEADER = 'X-Correlation-ID'
    FORWARD_HEADER = 'X-Forwarded-For'

    def filter(self, record):
        if request:
            record.request_id = request.headers.get(
                self.REQUEST_HEADER,
                request.headers.get(
                    self.CORRELATION_HEADER,
                    uuid.uuid4()
                )
            )
            record.client_ip = record.client_ip = request.headers.get(
                self.FORWARD_HEADER,
                request.remote_addr
            ) or self.DEFAULT
        else:
            record.client_ip = self.DEFAULT
            record.request_id = self.DEFAULT
        return True
