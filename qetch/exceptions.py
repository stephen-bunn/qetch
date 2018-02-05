# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>


class QetchException(Exception):

    def __init__(self, message: str):
        (self.message,) = (message,)
        super().__init__(self.message)


class ExtractorException(QetchException):
    pass


class ExtractionError(ExtractorException):
    pass
