# Copyright (c) 2017 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import enum
from typing import Any, Dict, Tuple

from multidict import CIMultiDict


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


class AuthRegistry(CIMultiDict):

    __shared_state = {}

    def __init__(self, *args, **kwargs):
        self.__dict__ = self.__shared_state
        super().__init__(self, *args, **kwargs)
