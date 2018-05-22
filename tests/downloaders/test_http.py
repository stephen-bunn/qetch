# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import hashlib
import tempfile
from pathlib import Path


def test_download(http_downloader, sample_http_content, connection_count):
    (content, checksum) = sample_http_content
    with tempfile.TemporaryDirectory() as tempdir:
        to_path = Path(tempdir) / str(connection_count)
        http_downloader.download(
            content, to_path.as_posix(),
            connections=connection_count
        )

        md5 = hashlib.md5()
        with to_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4096), b""):
                md5.update(chunk)

        assert md5.hexdigest().lower() == checksum.lower()
