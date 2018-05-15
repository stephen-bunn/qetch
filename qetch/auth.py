# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import enum
import inspect
from typing import Any, Union, Generator
from collections import MutableMapping, Iterable

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

    def __setitem__(self, key: BaseExtractor, value: Any):
        if not inspect.isclass(key) and issubclass(key, BaseExtractor):
            raise ValueError(
                (
                    f"key to {self.__class__.__name__!r} must be a subclass of "
                    f"{BaseExtractor!r}"
                )
            )

        if key.authentication != AuthTypes.NONE:
            if (
                not isinstance(value, Iterable)
                or len(value) != len(key.authentication.value)
            ):
                raise ValueError(
                    (
                        f"authentication for {key.name!r} is {key.authentication!r}, "
                        f"received {value!r}"
                    )
                )

        self.registry[key.name] = value

    def __getitem__(self, key: Any) -> Any:
        return self.registry[key]

    def __delitem__(self, key: Any) -> Any:
        del self.registry[key]
