# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import (Any, List, Dict,)

from .extractors._common import (BaseExtractor,)

import furl


class Content(object):
    """ The content object.
    """

    def __init__(
        self, uid: str, source: str, fragments: List[str],
        extractor: BaseExtractor,
        title: str=None, description: str=None, quality: float=None,
        uploaded_by: str=None, uploaded_date: datetime.datetime=None,
        metadata: Dict[str, Any]={}
    ):
        """ Initializes the Content instance.


        """

        (
            self.uid, self.source, self.fragments, self.extractor,
            self.title, self.description, self.quality,
            self.uploaded_by, self.uploaded_date, self.metadata,
        ) = (
            uid, source, fragments, extractor,
            title, description, quality,
            uploaded_by, uploaded_date, metadata
        )

    def __repr__(self):
        """ Returns a string representation of the content.

        Returns:
            str: The string representation of the instance.
        """

        return (
            f'<{self.__class__.__name__} ({self.quality}) "{self.uid}">'
        )


    @property
    def source(self):
        """ The given source url from where the content came from.

        Returns:
            :obj:`furl.furl`: The furl instance from the source url.
        """

        if not hasattr(self, '_source'):
            self._source = None
        return self._source

    @source.setter
    def source(self, url: str):
        """ Sets the source url.

        Decorators:
            source.setter

        Args:
            url (str): The new source url from where the content came from.
        """

        if isinstance(url, str) and len(url) > 0:
            self._source = furl.furl(url=url)

    def get_size(self) -> int:
        """ Returns the sum of the length of the fragments.

        Returns:
            int: The sum of the length of the fragments.
        """

        return sum(
            int(self.extractor.session.head(
                fragment
            ).headers['Content-Length'])
            for fragment in self.fragments
        )
