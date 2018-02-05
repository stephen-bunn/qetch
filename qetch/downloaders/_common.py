# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import os
import abc
import enum
import time
import uuid
import shutil
import itertools
from typing import (Any, List, Tuple, Callable,)
from tempfile import (TemporaryDirectory,)
from concurrent.futures import (ThreadPoolExecutor,)

from .. import (__version__,)
from ..content import (Content,)

import blinker


class DownloadState(enum.Enum):
    """ An enum of allowed download states.

    Values:
        - ``STOPPED``: indicates the download is stopped (error occured)
        - ``RUNNING``: indicates the download is running
        - ``PREPARING``: indicates the download is starting up
        - ``FINISHED``: indicates the download is finished (successfully)
    """

    STOPPED = 'stopped'
    RUNNING = 'running'
    PREPARING = 'preparing'
    FINISHED = 'finished'


class BaseDownloader(abc.ABC):
    """ The base abstract base downloader.
    `All downloaders must extend from this class.`
    """

    on_progress = blinker.Signal()

    @property
    def download_state(self):
        """ dict[str,DownloadState]: The download state dictionary.
        """

        if not hasattr(self, '_download_state'):
            self._download_state = {}
        return self._download_state

    @property
    def progress_store(self):
        """ dict[str,int]: The downloaded content size for progress reporting.
        """

        if not hasattr(self, '_progress_store'):
            self._progress_store = {}
        return self._progress_store

    @abc.abstractclassmethod
    def can_handle(cls, content: Content):
        raise NotImplementedError()

    @abc.abstractmethod
    def handle_download(self, source: str, url: str, to_path: str) -> str:
        raise NotImplementedError()

    def _calc_ranges(
        self, content_length: int, max_connections: int
    ) -> List[Tuple[int, int]]:
        """ Calculates byte ranges given a content size and the number of \
            allowed connections.

        Args:
            content_length (int): The total size of the content to download.
            max_connections (int): The maximum allowed connections to use.

        Returns:
            list[tuple[int, int]]: A list of size ``max_connections`` tuple \
                ``(start, end)`` byte ranges.
        """

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

    def handle_progress(
        self, download_id: str, content_length: int,
        update_delay: float=0.1
    ):
        """ The progress reporting handler.

        Args:
            download_id (str): The unique id of the download request.
            content_length (int): The total size of the downloading content.
            update_delay (float, optional): The frequency (in seconds) which \
                progress updates are emitted.
        """

        try:
            # setup sync values if they don't exists (race-condition fix)
            if download_id not in self.download_state:
                self.download_state[download_id] = DownloadState.PREPARING
            if download_id not in self.progress_store:
                self.progress_store[download_id] = 0

            while True:
                if self.progress_store[download_id] < content_length:
                    self.on_progress.send(
                        download_id,
                        current=self.progress_store[download_id],
                        total=content_length
                    )
                elif self.progress_store[download_id] >= content_length or \
                        self.download_state[download_id] == \
                        DownloadState.STOPPED:
                    break

                time.sleep(update_delay)
        finally:
            del self.progress_store[download_id]
            self.on_progress.send(
                download_id,
                current=content_length,
                total=content_length
            )

    def download(
        self, content: Content, to_path: str,
        max_fragments: int=1, max_connections: int=8,
        progress_hook: Callable[[Any], None]=None, update_delay: float=0.1,
    ) -> str:
        """ The simplified download method.

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
            max_fragments (int, optional): The number of fragments to process
                in parallel.
            max_connections (int, optional): The number of connections to
                allow for downloading a single fragment.
            progress_hook (callable, optional): A progress hook that accepts
                the arguments ``(download_id, current_size, total_size)`` for
                progress updates.
            update_delay (float, optional): The frequency (in seconds) where
                progress updates are sent to the given ``progress_hook``.

        Returns:
            str: The downloaded file's local path.

        Examples:
            Basic usage where ``$HOME`` is the home directory of the
            currently executing user.

            >>> import os
            >>> from qetch.extractors import (GfycatExtractor,)
            >>> from qetch.downloaders import (HTTPDownloader,)
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
            ...     update_delay=0.1)
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

        assert (max_fragments > 0), (
            f"'max_fragments' must be at least 1, received {max_fragments!r}"
        )
        assert (max_connections > 0), (
            f"'max_connections' must be at least 1, received "
            f"{max_connections!r}"
        )

        # generate unique download id for state & progress syncing
        download_id = str(uuid.uuid4())
        with TemporaryDirectory(
            prefix=f'{__version__.__name__}[{download_id}]-',
        ) as temporary_dir:
            # +1 worker is for progress handler
            with ThreadPoolExecutor(
                max_workers=(max_fragments + 1)
            ) as executor:
                if callable(progress_hook):
                    self.on_progress.connect(progress_hook)
                    executor.submit(
                        self.handle_progress,
                        *(download_id, content.get_size()),
                        **{'update_delay': update_delay}
                    )

                download_futures = []
                for (fragment_idx, fragment,) in enumerate(content.fragments):
                    download_futures.append(executor.submit(
                        self.handle_download,
                        *(
                            download_id, fragment,
                            os.path.join(temporary_dir, str(fragment_idx))
                        ),
                        **{'max_connections': max_connections}
                    ))

                # FIXME: handle KeyboardInterrupt with parent thread correctly
                try:
                    while all(future.running() for future in download_futures):
                        time.sleep(update_delay)
                    self.download_state[download_id] = DownloadState.FINISHED
                except Exception as exc:
                    self.download_state[download_id] = DownloadState.STOPPED
                    raise exc

                # apply content extractors merge and move result (one step)
                shutil.move(
                    content.extractor.merge([
                        future.result()
                        for future in download_futures
                    ]),
                    to_path
                )
                return to_path
