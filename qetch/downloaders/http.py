# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import time
import itertools
from concurrent.futures import (ThreadPoolExecutor,)

from ..content import (Content,)
from ._common import (BaseDownloader, DownloadState,)

import requests
import blinker


class HTTPDownloader(BaseDownloader):

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
        return self._session

    def _calc_ranges(self, content_length: int, max_connections: int):
        (start, end,) = itertools.tee(list(range(
            0, content_length,
            (content_length // max_connections)
        )) + [content_length])
        next(end, None)
        ranges = list(zip(start, end))
        if len(ranges) > max_connections:
            ranges[-2] = (ranges[-2][0], ranges[-1][-1],)
            del ranges[-1]
        return ranges

    def _handle_chunk(
        self, download_id: str, url: str, to_path: str, start: int, end: int,
        chunk_size: int=1024
    ):
        with open(to_path, 'wb') as file_:
            file_.seek(start)
            with self.session.get(
                url,
                headers={'range': f'bytes={start}-{end}'},
                stream=True
            ) as request_stream:
                for segment in request_stream.iter_content(
                    chunk_size=chunk_size
                ):
                    if self.download_state[download_id] == \
                            DownloadState.STOPPED:
                        return

                    file_.write(segment)

                    if download_id not in self.progress_store:
                        self.progress_store[download_id] = 0
                    self.progress_store[download_id] += len(segment)

    def _handle_download(
        self, download_id: str, url: str, to_path: str,
        max_connections: int=8
    ):
        self.download_state[download_id] = DownloadState.PREPARING
        headers = self.session.head(url).headers
        content_length = int(headers['Content-Length'])

        # preallocate file with content size
        with open(to_path, 'wb') as file_:
            file_.seek(content_length - 1)
            file_.write(b'\x00')

        if headers.get('Accept-Ranges').lower() != 'bytes':
            max_connections = 1

        chunk_futures = []
        # start thread pool for chunks url with max connections
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            for (start, end,) in \
                    self._calc_ranges(content_length, max_connections):
                if self.download_state[download_id] != DownloadState.RUNNING:
                    self.download_state[download_id] = DownloadState.RUNNING
                chunk_futures.append(executor.submit(
                    self._handle_chunk,
                    *(download_id, url, to_path, start, end)
                ))
            [future.result() for future in chunk_futures]
            return to_path
