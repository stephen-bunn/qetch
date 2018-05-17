# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

from concurrent.futures import ThreadPoolExecutor

import attr
import blinker
from requests_html import HTMLSession

from ._common import DownloadState, BaseDownloader
from ..content import Content


@attr.s
class HTTPDownloader(BaseDownloader):
    """The downloader for HTTP served content.
    """

    _session = HTMLSession()

    @classmethod
    def can_handle(cls, content: Content) -> bool:
        """Determines if a given content can be handled by this downloader.

        Args:
            content (Content): The content the check.

        Returns:
            bool: True if the content can be handled, otherwise False.
        """

        return all(
            cls._session.head(fragment).status_code == 200
            for fragment in content.fragments
        )

    def handle_chunk(
        self,
        download_id: str,
        url: str,
        to_path: str,
        start: int,
        end: int,
        chunk_size: int = 1024,
    ):
        """Handles downloading a specific range of bytes for a url.

        Args:
            download_id (str): The unique id of the download request.
            url (str): The url to download.
            to_path (str): The local path to save the download.
            start (int): The starting byte position to download.
            end (int): The ending byte position to download.
            chunk_size (int, optional): The size of the chunks to stream in.
        """

        with open(to_path, "wb") as file_:
            file_.seek(start)
            with self._session.get(
                url, headers={"range": f"bytes={start}-{end}"}, stream=True
            ) as request_stream:
                for segment in request_stream.iter_content(chunk_size=chunk_size):
                    if self.download_state[download_id] == DownloadState.STOPPED:
                        return

                    file_.write(segment)

                    if download_id not in self.progress_store:
                        self.progress_store[download_id] = 0
                    self.progress_store[download_id] += len(segment)

    def handle_download(
        self, download_id: str, url: str, to_path: str, max_connections: int = 8
    ):
        """Handles downloading a specific url.

        Note:
            ``max_connections`` defaults to 8 because many content hosting \
            sites will typically flag/ban IPs that use over 10 connections.

        Args:
            download_id (str): The unique id of the download request.
            url (str): The url to download.
            to_path (str): The local path to save the download.
            max_connections (int, optional): The number of allowed \
                connections for parallel downloading of the url.
        """

        self.download_state[download_id] = DownloadState.PREPARING
        headers = self._session.head(url).headers
        content_length = int(headers["Content-Length"])

        # preallocate file with content size
        with open(to_path, "wb") as file_:
            file_.seek(content_length - 1)
            file_.write(b"\x00")

        if headers.get("Accept-Ranges").lower() != "bytes":
            max_connections = 1

        chunk_futures = []
        # start thread pool for chunks url with max connections
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            for (start, end) in self._calc_ranges(content_length, max_connections):
                if self.download_state[download_id] != DownloadState.RUNNING:
                    self.download_state[download_id] = DownloadState.RUNNING
                chunk_futures.append(
                    executor.submit(
                        self.handle_chunk, *(download_id, url, to_path, start, end)
                    )
                )
            [future.result() for future in chunk_futures]
            return to_path
