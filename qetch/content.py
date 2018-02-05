# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import (Any, List, Dict,)

from .extractors._common import (BaseExtractor,)

import furl


class Content(object):
    """ The resulting content instance yielded by extractors.
    """

    def __init__(
        self, uid: str, source: str, fragments: List[str],
        extractor: BaseExtractor,
        title: str=None, description: str=None, quality: float=0.0,
        uploaded_by: str=None, uploaded_date: datetime.datetime=None,
        metadata: Dict[str, Any]={}
    ):
        """ Initializes the Content instance.

        uid (str): The unique id for the discovered content.
        source (str): The source url given to the extractor.
        fragments (list[str]): A list of urls which represent the raw content.
        extractor (BaseExtractor): The extractor which discovered the content.
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
    def uid(self) -> str:
        """ The unique id of the discovered content.

        Returns:
            str: The unique id of the discovered content.
        """

        if not hasattr(self, '_uid'):
            self._uid = None
        return self._uid

    @uid.setter
    def uid(self, uid: str):
        if isinstance(uid, str) and len(uid) > 0:
            self._uid = uid

    @property
    def source(self) -> furl.furl:
        """ The given source url from where the content came from.

        Returns:
            furl.furl: The given source url from where the content came from.
        """

        if not hasattr(self, '_source'):
            self._source = None
        return self._source

    @source.setter
    def source(self, url: str):
        if isinstance(url, str) and len(url) > 0:
            self._source = furl.furl(url=url)

    @property
    def fragments(self) -> List[str]:
        """ A list of urls which represent the raw content.

        Returns:
            list[str]: A list of urls which represent the raw content.
        """

        if not hasattr(self, '_fragments'):
            self._fragments = []
        return self._fragments

    @fragments.setter
    def fragments(self, fragments: List[str]):
        if isinstance(fragments, list) and len(fragments) > 0 and \
                all(isinstance(fragment, str) for fragment in fragments):
            self._fragments = fragments

    @property
    def extractor(self) -> BaseExtractor:
        """ The extractor which discovered the content.

        Returns:
            BaseExtractor: The extractor which discovered the content.
        """

        if not hasattr(self, '_extractor'):
            self._extractor = None
        return self._extractor

    @extractor.setter
    def extractor(self, extractor: BaseExtractor):
        if isinstance(extractor, BaseExtractor):
            self._extractor = extractor

    @property
    def title(self) -> str:
        """ The title of the content.

        Returns:
            str: The title of the content.
        """

        if not hasattr(self, '_title'):
            self._title = None
        return self._title

    @title.setter
    def title(self, title: str):
        if isinstance(title, str) and len(title) > 0:
            self._title = title

    @property
    def description(self) -> str:
        """ The description of the content.

        Returns:
            str: The description of the content.
        """

        if not hasattr(self, '_description'):
            self._description = None
        return self._description

    @description.setter
    def description(self, description: str):
        if isinstance(description, str) and len(description) > 0:
            self._description = description

    @property
    def quality(self) -> float:
        """ The contextual quality for the current content.

        Returns:
            float: The contextual quality for the current content.
        """

        if not hasattr(self, '_quality'):
            self._quality = 0.0
        return self._quality

    @quality.setter
    def quality(self, quality: float):
        if isinstance(quality, float) and 0.0 <= quality <= 1.0:
            self._quality = quality

    @property
    def uploaded_by(self) -> str:
        """ A string of the uploader's name.

        Returns:
            str: A string of the uploader's name.
        """

        if not hasattr(self, '_uploaded_by'):
            self._uploaded_by = None
        return self._uploaded_by

    @uploaded_by.setter
    def uploaded_by(self, uploaded_by: str):
        if isinstance(uploaded_by, str) and len(uploaded_by) > 0:
            self._uploaded_by = uploaded_by

    @property
    def uploaded_date(self) -> datetime.datetime:
        """ The datetime the content was uploaded.

        Returns:
            datetime.datetime: The datetime the content was uploaded.
        """

        if not hasattr(self, '_uploaded_date'):
            self._uploaded_date = None
        return self._uploaded_date

    @uploaded_date.setter
    def uploaded_date(self, uploaded_date: datetime.datetime):
        if isinstance(uploaded_date, datetime.datetime):
            self._uploaded_date = uploaded_date

    @property
    def metadata(self) -> Dict[str, Any]:
        """ Any metadata for the current content.

        Returns:
            dict[str,....]: Any metadata for the current content.
        """

        if not hasattr(self, '_metadata'):
            self._metadata = {}
        return self._metadata

    @metadata.setter
    def metadata(self, metadata: Dict[str, Any]):
        if isinstance(metadata, dict):
            self._metadata = metadata

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
