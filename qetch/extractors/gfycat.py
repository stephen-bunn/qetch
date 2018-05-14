# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import Any, Dict, List, Match, Tuple, Generator

from furl import furl

import ujson

from .. import exceptions
from ..auth import AuthTypes
from ._common import BaseExtractor
from ..content import Content


class GfycatExtractor(BaseExtractor):
    """The extractor for links to media from ``gfycat.com``.
    """

    name = "gfycat"
    description = "Site which hosts short high-quality video for sharing."
    authentication = AuthTypes.NONE
    domains = ["gfycat.com"]
    handles = {
        "basic": (
            r"^https?://(?:www\.)?gfycat\.com/(?:gifs/detail/)?(?P<id>[a-zA-Z]+)/?$"
        ),
        "raw": (
            r"^https?://(?:[a-z]+\.)gfycat\.com/(?P<id>[a-zA-Z]+)(?:\.[a-zA-Z0-9]+)$"
        ),
    }

    _api_base = "http://gfycat.com/cajax/get/"
    _content_urls = (
        "mp4Url",
        "webmUrl",
        "webpUrl",
        "mobileUrl",
        "mobilePosterUrl",
        "posterUrl",
        "thumb360Url",
        "thumb360PosterUrl",
        "thumb100PosterUrl",
        "max5mbGif",
        "max2mbGif",
        "mjpgUrl",
        "miniUrl",
        "miniPosterUrl",
        "gifUrl",
    )
    _quality_map = {"mp4Url": 1.0, "webmUrl": 0.5, "gifUrl": 0.25}

    def _get_data(self, id: str) -> Dict[str, Any]:
        """Gets API data for a specific gfycat id.

        Args:
            id (str): The id of the gfycat content to retrieve.

        Raises:
            exceptions.ExtractionError: When API call results in non 200 status

        Returns:
            dict[str,...]: API data dictionary response.
        """

        query_url = furl(self._api_base).add(path=id)

        response = self.session.get(query_url.url)
        if response.status_code not in (200,):
            raise exceptions.ExtractionError(
                (
                    f"error retrieving source for {query_url.url!r}, "
                    f"recieved status {response.status_code}"
                )
            )
        return ujson.loads(response.text).get("gfyItem")

    def handle_raw(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``raw`` links to gfycat media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        data = self._get_data(match.groupdict()["id"])
        yield [
            Content(
                uid=f'{self.name}-{data["gfyId"]}-{source.split(".")[-1]}',
                source=source,
                fragments=[source],
                extractor=self,
                extension=source.split(".")[-1],
                title=data.get("title"),
                description=data.get("description"),
                quality=1.0,
                uploaded_by=(
                    data.get("userName")
                    if data.get("userName") != "anonymous"
                    else None
                ),
                uploaded_date=datetime.datetime.fromtimestamp(
                    int(data.get("createDate"))
                ),
                metadata=data,
            )
        ]

    def handle_basic(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``basic`` links to gfycat media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        data = self._get_data(match.groupdict()["id"])
        # build and yield content list
        content_list = []
        for url_type in self._content_urls:
            if url_type in data:
                content_list.append(
                    Content(
                        uid=f'{self.name}-{data["gfyId"]}-{url_type}',
                        source=source,
                        fragments=[data.get(url_type)],
                        extractor=self,
                        extension=data.get(url_type).split(".")[-1],
                        title=data.get("title"),
                        description=data.get("description"),
                        quality=self._quality_map.get(url_type, 0.0),
                        uploaded_by=(
                            data.get("userName")
                            if data.get("userName") != "anonymous"
                            else None
                        ),
                        uploaded_date=datetime.datetime.fromtimestamp(
                            int(data.get("createDate"))
                        ),
                        metadata=data,
                    )
                )
        yield content_list
