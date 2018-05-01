# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>


class QetchException(Exception):
    """ All framework exceptions extend this.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ExtractorException(QetchException):
    """ All extractor errors extend this.
    """

    pass


class ExtractionError(ExtractorException):
    """ Error for when any extraction error occurs.
    """

    pass


class AuthenticationException(QetchException):
    """ All authentication errors extend this.
    """

    pass


class AuthenticationError(AuthenticationException):
    """ Error for when any authentication error occurs.
    """

    pass
