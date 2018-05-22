# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import functools

import attr
import trio
import asks
import requests

from ._common import BaseDownloader
from ..content import Content


@attr.s
class HTTPDownloader(BaseDownloader):
    """The downloader for HTTP served content.
    """

    def __attrs_post_init__(self):
        """Initializes trio for the ``asks`` framework.
        """

        asks.init("trio")

    @classmethod
    def can_handle(cls, content: Content) -> bool:
        """Determines if a given content can be handled by the http downloader.

        Args:
            content (Content): The content the check.

        Returns:
            bool: True if the content can be handled, otherwise False.
        """

        return all(
            requests.head(fragment).status_code == 200 for fragment in content.fragments
        )

    async def handle_chunk(
        self,
        session: asks.Session,
        download_id: str,
        url: str,
        to_path: trio.Path,
        start: int,
        end: int,
        accept_ranges: bool = True,
    ):
        """Handles downloading a specific range of bytes for a url.

        Args:
            session: (asks.Session): The session to use for the http requests.
            download_id (str): The unique id of the download request.
            url (str): The url to download.
            to_path (str): The local path to save the download.
            start (int): The starting byte position to download.
            end (int): The ending byte position to download.
            accept_ranges (bool, optional): Indicates if byte ranges are supported.
        """
        async with await to_path.open("wb") as stream:
            await stream.seek(start)
            if accept_ranges:
                session.headers["range"] = f"bytes={start}-{end}"
            response = await session.get(url, stream=True)
            async with response.body:
                async for chunk in response.body:
                    await stream.write(chunk)

                    if download_id not in self.progress_state:
                        self.progress_state[download_id] = 0
                    self.progress_state[download_id] += len(chunk)

    async def handle_download(
        self, download_id: str, url: str, to_path: trio.Path, connections: int = 8
    ) -> trio.Path:
        """Handles downloading a specific url.

        Note:
            ``max_connections`` defaults to 8 because many content hosting \
            sites will typically flag/ban IPs that use over 10 connections.

        Args:
            download_id (str): The unique id of the download request.
            url (str): The url to download.
            to_path (trio.Path): The local path object to save the download.
            connections (int, optional): The number of allowed connections for \
                parallel downloading of the url.
        """
        response = await asks.head(url)
        headers = response.headers
        content_length = int(headers["Content-Length"])

        # preallocate file with content size
        async with await to_path.open("wb") as stream:
            await stream.seek(content_length - 1)
            await stream.write(b"\x00")

        accept_ranges = True
        if headers.get("Accept-Ranges").lower() != "bytes":
            connections = 1
            accept_ranges = False

        session = asks.Session(connections=connections)
        # start nested nursery for multi-connection download handler
        async with trio.open_nursery() as nursery:
            for (start, end) in self.calculate_ranges(content_length, connections):
                nursery.start_soon(
                    functools.partial(
                        self.handle_chunk,
                        session,
                        download_id,
                        url,
                        to_path,
                        start,
                        end,
                        accept_ranges=accept_ranges,
                    )
                )

        return to_path
