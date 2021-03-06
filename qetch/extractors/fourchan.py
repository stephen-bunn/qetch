# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import Any, Dict, List, Match, Tuple, Generator

from furl import furl
from requests_html import HTML

import ujson

from .. import exceptions
from ..auth import AuthTypes
from ._common import BaseExtractor
from ..content import Content


class FourChanExtractor(BaseExtractor):
    """The extractor for links to media from ``4chan.org``.
    """

    name = "4chan"
    description = "A no-limits and lightly categorized temporary image host."
    authentication = AuthTypes.NONE
    domains = ["4chan.org", "i.4chan.org"]
    handles = {
        "thread": (
            r"^https?://(?:www\.)?(?:boards\.)?4chan\.org/(?P<board>.*)/"
            r"thread/(?P<id>.*)/?.*$"
        ),
        "raw": (
            r"^https?://(?:www\.)?i\.4cdn\.org/(?P<board>.*)/"
            r"(?P<id>.*)\.(?:[a-zA-Z0-9]+)$"
        ),
    }

    _api_base = "https://a.4cdn.org/"
    _img_base = "https://i.4cdn.org/"
    _content_configs = [
        (None, "{board}/{post[tim]}{post[ext]}", 1.0, None),
        ("thumb", "{board}/{post[tim]}s.jpg", 0.0, "jpg"),
    ]

    def _get_data(self, board: str, id: str) -> Dict[str, Any]:
        """Gets API data for a specific 4chan board and thread id.

        Args:
            board (str): The id of the passed board
            id (str): The id of the passed thread

        Raises:
            exceptions.ExtractionError: When API call results in non 200 status

        Returns:
            dict[str,....]: API data dictionary response
        """

        query_url = furl(self._api_base).add(path=f"{board}/thread/{id}.json")
        response = self.session.get(query_url.url)
        if response.status_code not in (200,):
            raise exceptions.ExtractionError(
                (
                    f"error retrieving source for {query_url.url!r} recieved status "
                    f"{response.status_code}"
                )
            )
        return ujson.loads(response.text)

    def handle_thread(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``thread`` links to 4chan media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        matchdict = match.groupdict()
        data = self._get_data(matchdict["board"], matchdict["id"])
        for post in data.get("posts", []):
            if "md5" in post:
                content_list = []
                for (
                    post_type, url_path, quality, extension_type
                ) in self._content_configs:
                    # build post_type depending on existing post_type
                    post_type = (f"-{post_type}" if post_type else "")
                    content_uid = (
                        f'{self.name}-{matchdict["board"]}-'
                        f'{matchdict["id"]}-{post["tim"]}{post_type}'
                    )
                    content_fragments = [
                        furl(self._img_base).add(
                            path=url_path.format(board=matchdict["board"], post=post)
                        ).url
                    ]
                    content_extension = (
                        extension_type if extension_type else post["ext"].split(".")[-1]
                    )
                    content_description = None
                    if "com" in post and len(post["com"]) > 0:
                        content_description = HTML(html=post.get("com")).text

                    content_list.append(
                        Content(
                            uid=content_uid,
                            source=source,
                            fragments=content_fragments,
                            extractor=self,
                            extension=content_extension,
                            title=post.get("filename"),
                            description=content_description,
                            quality=quality,
                            uploaded_by=post.get("name"),
                            uploaded_date=datetime.datetime.fromtimestamp(
                                int(post.get("time"))
                            ),
                            metadata=post,
                        )
                    )
                yield content_list

    def handle_raw(
        self, source: str, match: Match
    ) -> Generator[List[Content], None, None]:
        """Handles ``raw`` links to 4chan media.

        Args:
            source (str): The source url
            match (Match): The source match regex

        Yields:
            list[Content]: A list of various levels of quality content for \
                the same source url
        """

        matchdict = match.groupdict()
        content_list = []
        for (post_type, url_path, quality) in self._content_configs:
            content_list.append(
                Content(
                    uid=(
                        f'{self.name}-{matchdict["board"]}-raw-{matchdict["id"]}'
                        f"{post_type}"
                    ),
                    source=source,
                    fragments=[source],
                    extractor=self,
                    title=None,
                    description=None,
                    quality=quality,
                    uploaded_by=None,
                    uploaded_date=None,
                    metadata=None,
                )
            )
        yield content_list
