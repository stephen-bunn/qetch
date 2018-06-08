# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import abc
import uuid
import shutil
import itertools
import functools
from typing import Any, List, Tuple, Callable
from tempfile import TemporaryDirectory

import attr
import trio

from .. import __version__
from ..content import Content


@attr.s
class BaseDownloader(abc.ABC):
    """The base abstract base downloader.

    `All downloaders must extend from this class.`
    """

    download_state = attr.ib(type=dict, default={}, init=False, repr=False)
    progress_state = attr.ib(type=dict, default={}, init=False, repr=False)

    @abc.abstractclassmethod
    def can_handle(cls, content: Content) -> bool:
        """Determines if a given content can be handled by the downloader.

        Args:
            content (Content): The content the check.

        Returns:
            bool: True if the content can be handled, otherwise False.
        """
        raise NotImplementedError()

    @abc.abstractclassmethod
    async def handle_download(
        self, download_id: str, url: str, to_path: str, connections: int = 1
    ) -> trio.Path:
        """Handles downloading a specific url.

        Args:
            download_id (str): The unique id of the download request.
            url (str): The url to download.
            to_path (trio.Path): The local path object to save the download.
            connections (int, optional): The number of allowed connections for \
                parallel downloading of the url.

        Returns:
            trio.Path: The downloaded file path object
        """
        raise NotImplementedError()

    @classmethod
    def calculate_ranges(
        cls, content_size: int, connection_count: int
    ) -> List[Tuple[int, int]]:
        """Calculates byte ranges given a content size and the number of \
            allowed connections.

        Args:
            content_size (int): The total size of the content to download.
            connection_count (int): The number of allowed connections to use.

        Returns:
            list[tuple[int, int]]: A list of size ``connection_count`` tuple \
                ``(start, end)`` byte ranges.
        """
        (start, end) = itertools.tee(
            list(range(0, content_size, (content_size // connection_count)))
            + [content_size]
        )
        next(end, None)
        ranges = list(zip(start, end))
        if len(ranges) > connection_count:
            ranges[-2] = (ranges[-2][0], ranges[-1][-1])
            del ranges[-1]
        return ranges

    async def _download(
        self,
        content: Content,
        to_path: str,
        fragments: int = 1,
        connections: int = 1,
        progress_hook: Callable[[Any], None] = None,
        progress_delay: float = 0.1,
    ):
        """The hidden async functionality of :func:`~http.HTTPDownloader.download`.
        """

        download_id = str(uuid.uuid4())
        with TemporaryDirectory(
            prefix=f"{__version__.__name__}-{download_id}"
        ) as tempdir:
            tempdir = trio.Path(tempdir)

            fragment_paths = []
            async with trio.open_nursery() as nursery:
                if callable(progress_hook):
                    await nursery.start(
                        functools.partial(
                            self.handle_progress,
                            download_id,
                            content.get_size(),
                            progress_hook=progress_hook,
                            progress_delay=progress_delay,
                        )
                    )
                for (fragment_index, fragment) in enumerate(content.fragments):
                    download_to = tempdir / str(fragment_index)
                    fragment_paths.append(download_to)
                    nursery.start_soon(
                        functools.partial(
                            self.handle_download,
                            download_id,
                            fragment,
                            download_to,
                            connections=connections,
                        )
                    )

            merged_path = content.extractor.merge(
                [fragment for fragment in fragment_paths]
            )
            shutil.move(merged_path, to_path)

    async def handle_progress(
        self,
        download_id: str,
        content_size: int,
        progress_hook: Callable[[Any], None] = None,
        progress_delay: float = 0.1,
        task_status: Any = None,
    ):
        """The progress reporting handler.

        Args:
            download_id (str): The unique id of the download request.
            content_size (int): The total size of the downloading content.
            progress_hook (callable, optional): A progress hook that accepts the \
                arguments ``(download_id, current_size, total_size)`` for progress \
                updates.
            progress_delay (float, optional): The frequency (in seconds) which \
                progress updates are emitted.
        """

        while True:
            if callable(progress_hook) and download_id in self.progress_state:
                current_size = self.progress_state[download_id]
                if self.progress_state[download_id] >= content_size:
                    progress_hook(download_id, content_size, content_size)
                    break
                else:
                    progress_hook(download_id, current_size, content_size)

            if task_status and not task_status._called_started:
                task_status.started()
            await trio.sleep(progress_delay)

    def download(self, *args, **kwargs) -> str:
        """The simplified download method.

        Note:
            The ``max_fragments`` and ``max_connections`` rules imply that
            potentially ``(max_fragments * max_connections)`` connections
            from the local system's IP can exist at any time.

            Many hosts will flag/ban IPs which utilize more than 10
            connections for a single resource.
            **For this reason**, ``max_fragments`` and ``max_connections`` are
            set to 1 and 8 respectively by default.


        Args:
            content (Content): The content instance to download.
            to_path (str): The path to save the resulting download to.
            fragments (int, optional): The number of fragments to process
                in parallel.
            connections (int, optional): The number of connections to
                allow for downloading a single fragment.
            progress_hook (callable, optional): A progress hook that accepts
                the arguments ``(download_id, current_size, total_size)`` for
                progress updates.
            progress_delay (float, optional): The frequency (in seconds) where
                progress updates are sent to the given ``progress_hook``.

        Returns:
            str: The downloaded file's local path.

        Examples:
            Basic usage where ``$HOME`` is the home directory of the
            currently executing user.

            >>> import os
            >>> from qetch.extractors import GfycatExtractor
            >>> from qetch.downloaders import HTTPDownloader
            >>> content = next(GfycatExtractor().extract(GFYCAT_URL))[0]
            >>> saved_to = HTTPDownloader().download(
            ...     content,
            ...     os.path.expanduser('~/Downloads/saved_content.mp4'))
            >>> print(saved_to)
            $HOME/Downloads/saved_content.mp4

            Similar basic usage, but with a given progress hook sent updates
            every 0.1 seconds.

            >>> def progress(download_id, current, total):
            ...     print(f'{((current / total) * 100.0):6.2f}')
            >>> saved_to = HTTPDownloader().download(
            ...     content,
            ...     os.path.expanduser('~/Downloads/saved_content.mp4'),
            ...     progress_hook=progress,
            ...     progress_delay=0.1)
              0.00
              0.00
             23.01
             54.32
             73.09
             90.49
             97.12
            100.00
            >>> print(saved_to)
            $HOME/Downloads/saved_content.mp4
        """

        trio.run(functools.partial(self._download, *args, **kwargs))
