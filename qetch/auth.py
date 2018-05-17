# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import enum
import inspect
from typing import Any, Union, Generator
from collections import Iterable, MutableMapping

import attr

from .extractors._common import BaseExtractor


class AuthTypes(enum.Enum):
    """An enumeration of available authentication types.

    Values:
        - ``NONE``: No authentication required
        - ``BASIC``: Basic (username, password) authentication required
        - ``OAUTH``: Standard oauth (key, secret) authentication required
    """

    NONE = None
    BASIC = ("USERNAME", "PASSWORD")
    OAUTH = ("KEY", "SECRET")


@attr.s
class AuthRegistry(MutableMapping):
    """The authentication registry.

    Implements the borg pattern for shared state between instances.
    """
    __shared_state = {}

    registry = attr.ib(init=False, repr=False, default={})

    def __init__(self, *args, **kwargs):
        self.__dict__ = self.__shared_state
        super().__init__(*args, **kwargs)

    def __len__(self) -> int:
        return len(self.registry)

    def __iter__(self) -> Generator[Any, None, None]:
        for item in self.registry.__iter__():
            yield item

    def __setitem__(self, key: str, value: Any):
        self.registry[key] = value

    def __getitem__(self, key: Any) -> Any:
        return self.registry[key]

    def __delitem__(self, key: Any) -> Any:
        del self.registry[key]

    @classmethod
    def from_dict(cls, dictionary: dict) -> Any:
        registry = cls()
        for (key, value) in dictionary.get("registry", {}).items():
            registry[key] = value
        return registry

    def to_dict(self) -> dict:
        return attr.asdict(self)
