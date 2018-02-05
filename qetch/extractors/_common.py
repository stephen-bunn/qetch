# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import re
import abc
from typing import (List,)

import furl
import requests


class BaseExtractor(abc.ABC):

    def __repr__(self):
        return (f'<{self.__class__.__name__} "{self.name}">')

    @abc.abstractproperty
    def name(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def description(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def domains(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def handles(self):
        raise NotImplementedError()

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
        return self._session

    @classmethod
    def get_handle(cls, url: str):
        for (handle_name, handle_pattern,) in cls.handles.items():
            match = re.match(handle_pattern, url)
            if match:
                return (handle_name, match,)

    @classmethod
    def can_handle(cls, url: str):
        return cls.get_handle(url) is not None

    @abc.abstractmethod
    def merge(self, ordered_filepaths: List[str]):
        raise NotImplementedError()

    def extract(self, url: str):
        (handle_name, handle_match,) = self.get_handle(url)
        handle_method = f'_handle_{handle_name}'
        if not hasattr(self, handle_method):
            raise NotImplementedError((
                f"no handled method named {handle_method!r} is implemented "
                f"for {self!r}"
            ))
        for content in getattr(self, handle_method)(url, handle_match):
            yield content
