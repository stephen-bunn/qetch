# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import os
import pathlib
import importlib.util


def normalize_path(filepath: str, expand_vars: bool=False) -> str:
    """ Fully normalize a given filepath.

    Args:
        filepath (str): The filepath to normalize.
        expand_vars (bool, optional): If True, expands variables like
            ``$HOME`` or ``$USER``.

    Returns:
        str: The fully normalized filepath.
    """

    filepath = str(pathlib.Path(filepath).expanduser().resolve())
    if expand_vars:
        filepath = os.path.expandvars(filepath)
    return filepath


def is_importable(name: str) -> bool:
    """ Determines if a given module name can be imported.

    Args:
        name (str): The name of the module to check.

    Returns:
        bool: True if possible to be imported, otherwise False.
    """

    return bool(importlib.util.find_spec(name))
