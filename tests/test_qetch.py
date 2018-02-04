# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import contextlib

from qetch.qetch import (Qetch,)

import pytest


@contextlib.contextmanager
def qetch_manager(*args, **kwargs):
    """ A context manager for test objects.
    """

    manager = Qetch(*args, **kwargs)
    try:
        yield manager
    finally:
        del manager


class TestQetch(object):
    """ Base test object.
    """

    def test_initialization(self):
        """ Base initialization test case.
        """

        with qetch_manager() as test_qetch:
            assert isinstance(test_qetch, Qetch)
            # TODO: test initialization
