# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import os
import abc
import enum
import time
import uuid
import shutil
from typing import (Any, Callable,)
from tempfile import (TemporaryDirectory,)
from concurrent.futures import (ThreadPoolExecutor,)

from .. import (__version__,)
from ..content import (Content,)

import blinker


class DownloadState(enum.Enum):

    STOPPED = 'stopped'
    RUNNING = 'running'
    PREPARING = 'preparing'
    FINISHED = 'finished'


class BaseDownloader(abc.ABC):

    on_progress = blinker.Signal()

    @property
    def download_state(self):
        if not hasattr(self, '_download_state'):
            self._download_state = {}
        return self._download_state

    @property
    def progress_store(self):
        if not hasattr(self, '_progress_store'):
            self._progress_store = {}
        return self._progress_store

    @classmethod
    def can_handle(cls, content: Content):
        raise NotImplementedError()

    @abc.abstractmethod
    def _handle_download(self, source: str, url: str, to_path: str):
        raise NotImplementedError()

    def _handle_progress(
        self, download_id: str, content_length: int,
        update_delay: float=0.1
    ):
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
    ):
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
                        self._handle_progress,
                        *(download_id, content.get_size()),
                        **{'update_delay': update_delay}
                    )

                download_futures = []
                for (fragment_idx, fragment,) in enumerate(content.fragments):
                    download_futures.append(executor.submit(
                        self._handle_download,
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
