# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import inspect

import qetch
from . import (extractors,)

import pytest


class TestQetch(object):
    """ Test the main features of the Qetch framework.
    """

    def test_extractors_names(self):
        """ Test the names of all extractors.
        """

        seen = set()
        for (_, extractor_class,) in inspect.getmembers(
            qetch.extractors,
            predicate=inspect.isclass
        ):
            assert extractor_class.name not in seen
            seen.add(extractor_class.name)
