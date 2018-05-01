# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import inspect

from . import extractors, downloaders
from .content import Content

IGNORED_EXTRACTORS = (extractors._common.BaseExtractor, extractors.GenericExtractor)
IGNORED_DOWNLOADERS = (downloaders._common.BaseDownloader,)


def get_extractor(
    url: str, init: bool = False, *args, **kwargs
) -> extractors._common.BaseExtractor:
    """ Gets the first extractor that can handle a given url.

    Args:
        url (str): The url that needs to be extracted
        init (bool, optional): If True initializes the class, otherwise returns
            the class

    Returns:
        extractors._common.BaseExtractor: The extractor that can
            handle the url.

    Examples:
        Basic usage...

        >>> import qetch
        >>> extractor = qetch.get_extractor(GFYCAT_URL, init=True)
        >>> print(extractor)
        <GfycatExtractor "gfycat">
    """

    for (extractor_name, extractor_class) in inspect.getmembers(
        extractors, predicate=inspect.isclass
    ):
        if extractor_class not in IGNORED_EXTRACTORS:
            if extractor_class.can_handle(url):
                return (
                    extractor_class if not init else extractor_class(*args, **kwargs)
                )
    # if no extractor can handle, just return GenericExtractor
    return (
        extractors.GenericExtractor if not init else extractor_class(*args, **kwargs)
    )


def get_downloader(
    content: Content, init: bool = False, *args, **kwargs
) -> downloaders._common.BaseDownloader:
    """ Gets the first downloader that can handle a given content.

    Args:
        content (Content): The content that needs to be downloaded
        init (bool, optional): If True initializes the class, otherwise
            returns the class

    Returns:
        downloaders._common.BaseDownloader: The downloader that can handle the
            content.

    Examples:
        Basic usage...

        >>> import qetch
        >>> content = next(qetch.get_extractor(GFYCAT_URL, init=True)
        ...     .extract(GFYCAT_URL))[0]
        >>> downloader = qetch.get_downloader(content, init=True)
        >>> print(downloader)
        <HTTPDownloader at 0xABCDEF1234567890>
    """

    for (downloader_name, downloader_class) in inspect.getmembers(
        downloaders, predicate=inspect.isclass
    ):
        if downloader_class not in IGNORED_DOWNLOADERS:
            if downloader_class.can_handle(content):
                return (
                    downloader_class if not init else downloader_class(*args, **kwargs)
                )
