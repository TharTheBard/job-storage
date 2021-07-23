class JobStorageException(Exception):
    RESPONSE = "Internal server error"
    STATUS_CODE = 500
    
    def __init__(self, response=None, status_code=None):
        self.response = response or type(self).RESPONSE
        self.status_code = status_code or type(self).STATUS_CODE


class DatabaseError(JobStorageException):
    pass


class UniqueViolationError(JobStorageException):
    RESPONSE = "Unique data already exists"
    STATUS_CODE = 400


class ForeignKeyViolationError(JobStorageException):
    RESPONSE = "Referenced data does not exist"
    STATUS_CODE = 400
