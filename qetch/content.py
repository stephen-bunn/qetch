# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import Any, Dict, List

import attr
from furl import furl

from .extractors._common import BaseExtractor


@attr.s
class Content(object):
    """ The resulting content instance yielded by extractors.

    Attributes:
        uid (str): The unique id for the discovered content.
        source (str): The source url given to the extractor.
        fragments (list[str]): A list of urls which represent the raw content.
        extractor (BaseExtractor): The extractor which discovered the content.
        extension (str): The extension for the resulting file.
        title (str, optional): A title for the content.
        description (str, optional): A description for the content.
        quality (float, optional): A level of quality for the content in
            relation to other content with the same source.
        uploaded_by (str, optional): A string of the uploader's name.
        uploaded_date (datetime.datetime, optional): A datetime instance for
            when the content was uploaded.
        metadata (dict[str,....], optional): Any additional metadata about
            the discovered content.
    """
    uid = attr.ib(type=str)
    source = attr.ib(type=str, converter=furl, repr=False)
    fragments = attr.ib(type=List[str], repr=False)
    extractor = attr.ib(type=BaseExtractor, repr=False)
    extension = attr.ib(type=str, default=None, repr=False)
    title = attr.ib(type=str, default=None, repr=False)
    description = attr.ib(type=str, default=None, repr=False)
    quality = attr.ib(type=float, default=0.0)
    uploaded_by = attr.ib(type=str, default=None, repr=False)
    uploaded_date = attr.ib(type=datetime.datetime, default=None, repr=False)
    metadata = attr.ib(type=dict, default={}, repr=False)

    def get_size(self):
        """ Returns the sum of the length of the fragments.

        Returns:
            int: The sum of the length of the fragments.
        """
        return sum(
            int(self.extractor.session.head(fragment).headers["Content-Length"])
            for fragment in self.fragments
        )
