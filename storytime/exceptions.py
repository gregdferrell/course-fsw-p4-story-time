#
# Story Time App
# Exceptions
#


class AppException(Exception):
    def __init__(self, code=500, message="An unexpected error has occurred on the server."):
        self.code = code
        self.message = message

    def __repr__(self):
        return self.__class__.__name__ + ', code: {}, message: {}'.format(self.code, self.message)

    def __str__(self):
        return self.__repr__()


class AppExceptionNotFound(AppException):
    def __init__(self, code=404, message="The resource you're looking for can't be found."):
        super().__init__(code=code, message=message)
