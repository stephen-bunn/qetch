# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

from qetch.downloaders import HTTPDownloader
from qetch.extractors import GenericExtractor

import pytest


HTTP_CONTENT = {
    "http://ipv4.download.thinkbroadband.com/5MB.zip": "b3215c06647bc550406a9c8ccc378756"
}
CONNECTION_COUNTS = list(range(1, 9))


@pytest.fixture(scope="session")
def http_downloader(request):
    downloader = HTTPDownloader()
    yield downloader
    del downloader


@pytest.fixture(scope="session", params=HTTP_CONTENT.items())
def sample_http_content(request):
    return (next(GenericExtractor().extract(request.param[0]))[0], request.param[1])


@pytest.fixture(scope="session", params=CONNECTION_COUNTS)
def connection_count(request):
    return request.param
