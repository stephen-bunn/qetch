# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import (Any, Tuple, List, Dict, Match, Generator,)

from .. import (exceptions,)
from ..auth import (AuthTypes,)
from ..content import (Content,)
from ._common import (BaseExtractor,)

import bs4
import furl
import ujson


class GenericExtractor(BaseExtractor):
    """ A basic generic extractor that simply extracts to the same url.
    """

    name = 'generic'
    description = (
        'This extractor is a generic extractor only to be used with raw '
        'or unhandled links.'
    )
    authentication = AuthTypes.NONE
    domains = []
    handles = {
        'all': (r'^https?://(?:www\.)?.*$')
    }

    def handle_all(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """ Handles ``all`` links to any media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        yield [Content(
            uid=f'{self.name}-{source}',
            source=source,
            fragments=[source],
            extractor=self,
            title=None,
            description=None,
            quality=0.0,
            uploaded_by=None,
            uploaded_date=None,
            metadata=None
        )]
