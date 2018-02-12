# Copyright (c) 2017 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import enum
from typing import (Any, Tuple, Dict,)


class AuthTypes(enum.Enum):
    """ An enumeration of available authentication types.

    Values:
        - ``NONE``: No authentication required
        - ``BASIC``: Basic (username, password) authentication required
        - ``OAUTH``: Standard oauth (key, secret) authentication required
    """

    NONE = None
    BASIC = ('USERNAME', 'PASSWORD',)
    OAUTH = ('KEY', 'SECRET',)


class AuthRegistry(dict):
    """ Custom borg style registry dictionary.

    This registry dictionary utilizes the borg design pattern and maintains
    the same state across multiple instances.
    This means that multiple instances of this object can exist, but the values
    between them will stay syncronized.

    Examples:
        Basic usage...

        >>> from qetch.auth import (AuthRegistry,)
        >>> from qetch.extractors import (GfycatExtractor,)
        >>> registry_1 = AuthRegistry()
        >>> registry_1[GfycatExtractor.name] = ('KEY', 'SECRET',)
        >>> print(registry_1[GfycatExtractor.name])
        ('KEY', 'SECRET')
        >>> registry_2 = AuthRegistry()
        >>> print(registry_2[GfycatExtractor.name])
        ('KEY', 'SECRET')
        >>> registry_1[GfycatExtractor.name] = ('USERNAME', 'PASSWORD',)
        >>> print(registry_2[GfycatExtractor.name])
        ('USERNAME', 'PASSWORD')
    """

    __shared_state = {}

    def __init__(self, **kwargs):
        self.__dict__ = self.__shared_state
        self.__dict__.update(**kwargs)

    def __setitem__(self, key: Any, value: Any):
        self.__dict__[key] = value

    def __getitem__(self, key: Any) -> Any:
        return self.__dict__[key]

    def __delitem__(self, key: Any):
        del self.__dict__[key]

    def __repr__(self):
        return (
            f'<{self.__class__.__name__} ({hex(id(self))}) '
            f'"{len(self.__dict__)} entr'
            f'{"ies" if len(self.__dict__) > 1 else "y"}">'
        )

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    def __cmp__(self, registry):
        return self.__cmp__(self.__dict__, registry.__dict__)

    def __contains__(self, value: Any):
        return value in self.__dict__

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def copy(self):
        return self.__dict__.copy()

    def clear(self):
        return self.__dict__.clear()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)
