#
# Story Time App
# Models
#


class AppException(Exception):
    def __init__(self, code=None, message=None):
        self.code = code
        self.message = message


class AppExceptionNotFound(AppException):
    pass
