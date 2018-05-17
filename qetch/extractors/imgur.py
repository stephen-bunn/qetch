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


class ImgurExtractor(BaseExtractor):
    """The extractor for links to media from ``imgur.com``.
    """

    name = "imgur"
    description = "Dedicated image host originally built for Reddit."
    authentication = AuthTypes.OAUTH
    domains = ["imgur.com", "i.imgur.com"]
    handles = {
        "basic": r"^https?://(?:www\.)?imgur\.com/(?P<id>[a-zA-Z0-9]+)/?$",
        "album": (
            r"^https?://(?:www\.)?imgur\.com/" r"(?:a|gallery)/(?P<id>[a-zA-Z0-9]+)/?$"
        ),
        "raw": (
            r"^https?://(?:www\.)?(?:[a-z]\.)imgur\.com/" r"(?P<id>[a-zA-Z0-9]+)\..*$"
        ),
    }

    _api_base = "https://api.imgur.com/3"
    _content_urls = ("mp4", "gifv", "link")
    _quality_map = {"mp4": 1.0, "gifv": 0.5, "link": 0.0}

    def _get_data(
        self, id: str, is_album: bool = False, is_raw: bool = False
    ) -> Dict[str, Any]:
        """Gets API data for a specific imgur id.

        Args:
            id (str): The id of the imgur content to retrieve.
            is_album (bool, optional): If True, indicates that id is that of
                an album.
            is_raw (bool, optional): If True, indicates that id is that of
                some raw imgur link.

        Raises:
            exceptions.ExtractionError: When API call results in non 200 status

        Returns:
            dict[str,....]: API data dictionary response
        """

        query_url = furl(self._api_base).add(
            path=(
                f'{"/gallery" if is_raw else ""}'
                f'{"album" if is_album else "image"}/{id}'
            )
        )
        response = self.session.get(query_url.url)
        if response.status_code not in (200,):
            raise exceptions.ExtractionError(
                (
                    f"error retrieving source for {query_url.url!r} recieved status "
                    f"{response.status_code}"
                )
            )
        return ujson.loads(response.text).get("data")

    def handle_basic(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``basic`` links to imgur media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        data = self._get_data(match.groupdict()["id"])
        content_list = []
        for url_type in self._content_urls:
            if url_type in data:
                content_list.append(
                    Content(
                        uid=f'{self.name}-{data["id"]}-{url_type}',
                        source=source,
                        fragments=[data[url_type]],
                        extractor=self,
                        extension=data[url_type].split(".")[-1],
                        title=data.get("title"),
                        description=data.get("description"),
                        quality=self._quality_map.get(url_type, 0.0),
                        uploaded_by=data.get("account_id"),
                        uploaded_date=datetime.datetime.fromtimestamp(
                            int(data.get("datetime"))
                        ),
                        metadata=data,
                    )
                )
        yield content_list

    def handle_album(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``album`` links to imgur media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        try:
            data = self._get_data(match.groupdict()["id"], is_album=True)
            for image in data.get("images", []):
                content_list = []
                for url_type in self._content_urls:
                    if url_type in image:
                        content_list.append(
                            Content(
                                uid=f'{self.name}-{image["id"]}-{url_type}',
                                source=source,
                                fragments=[image[url_type]],
                                extractor=self,
                                extension=image[url_type].split(".")[-1],
                                title=data.get("title"),
                                description=data.get("description"),
                                quality=self._quality_map.get(url_type, 0.0),
                                uploaded_by=data.get("account_id"),
                                uploaded_date=datetime.datetime.fromtimestamp(
                                    int(data.get("datetime"))
                                ),
                                metadata=image,
                            )
                        )
                yield content_list
        except exceptions.ExtractionError as exc:
            for content_list in self.handle_basic(source, match):
                yield content_list

    def handle_raw(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``raw`` links to imgur media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        data = self._get_data(match.groupdict()["id"], is_raw=True)
        content_list = []
        for url_type in self._content_urls:
            if url_type in data:
                content_list.append(
                    Content(
                        uid=f'{self.name}-{data["id"]}-{url_type}',
                        source=source,
                        fragments=[data[url_type]],
                        extractor=self,
                        extension=data[url_type].split(".")[-1],
                        title=data.get("title"),
                        description=data.get("description"),
                        quality=self._quality_map.get(url_type, 0.0),
                        uploaded_by=data.get("account_id"),
                        uploaded_date=datetime.datetime.fromtimestamp(
                            int(data.get("timestamp"))
                        ),
                        meatdata=data,
                    )
                )
        yield content_list

    def authenticate(self, auth_tuple: Tuple[str, str]):
        """Handles authenticating the extractor if necessary.

        Args:
            auth_tuple (tuple[str, str]): The authentication tuple is available.
        """

        self.session.headers.update({"Authorization": f"Client-ID {auth_tuple[0]}"})
