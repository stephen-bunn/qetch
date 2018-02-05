# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import re
import abc
from typing import (Any, List, Tuple, Match, Generator,)

from .. import (exceptions,)
from ..auth import (AuthRegistry, AuthTypes,)

import furl
import requests


class BaseExtractor(abc.ABC):
    """ The base extractor.
    `All extractors should extend this.`
    """

    def __repr__(self):
        """ Returns a string representation of the extractor.

        Returns:
            str: The string representation of the instance.
        """

        return (f'<{self.__class__.__name__} "{self.name}">')

    @abc.abstractproperty
    def name(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def description(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def domains(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def handles(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def authentication(self):
        raise NotImplementedError()

    @property
    def session(self):
        """ The default session for the extractor.

        Returns:
            requests.Session: The default session for the extractor.
        """

        if not hasattr(self, '_session'):
            self._session = requests.Session()
        return self._session

    @classmethod
    def get_handle(cls, url: str) -> Tuple[str, Match]:
        """ Gets the handle match for a given url.

        Args:
            url (str): The url to get the handle match for.

        Returns:
            tuple[str, Match]: A tuple of handle and the match for the url.
        """

        for (handle_name, handle_pattern,) in cls.handles.items():
            match = re.match(handle_pattern, url)
            if match:
                return (handle_name, match,)

    @classmethod
    def can_handle(cls, url: str):
        """ Determines if an extractor can handle a url.

        Args:
            url (str): The url to check

        Returns:
            bool: True if the extractor can handle, otherwise False
        """

        return cls.get_handle(url) is not None

    @abc.abstractmethod
    def merge(self, ordered_filepaths: List[str]) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def authenticate(self, auth: Tuple[str, str]):
        raise NotImplementedError()

    def extract(
        self, url: str, auth: Tuple[str, str]=None
    ) -> Generator[List[Any], None, None]:
        """ Extracts lists of content from a url.

        Note:
            When an extractor can handle a url with a given
            ``{handle_name: regex}`` dictionary, the
            :func:`~qetch.extractors._common.BaseExtractor.extract` method
            assumes that a method ``handle_{handle_name}`` exists to
            handle that specific url.

            If an appropriately named method does not exist, a
            ``NotImplementedError`` is raised.

        Args:
            url (str): The url to extract content from.
            auth (tuple[str, str], optional): The auth tuple if available.

        Raises:
            NotImplementedError: If a given ``handle_{handle_name}``
                method does not exist.

        Yields:
            list[Content]: A list of similar content of different qualities

        Examples:
            Basic usage where ``GFYCAT_ID`` is the id determined from
            ``GFYCAT_URL``.

            >>> from qetch.extractors import (GfycatExtractor,)
            >>> for content_list in GfycatExtractor().extract(GFYCAT_URL):
            ...    for content in content_list:
            ...        print(content)
            <Content (1.0) "gfycat-GFYCAT_ID-mp4Url">
            <Content (0.5) "gfycat-GFYCAT_ID-webmUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-webpUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-mobileUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-mobilePosterUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-posterUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-thumb360Url">
            <Content (0.0) "gfycat-GFYCAT_ID-thumb360PosterUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-thumb100PosterUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-max5mbGif">
            <Content (0.0) "gfycat-GFYCAT_ID-max2mbGif">
            <Content (0.0) "gfycat-GFYCAT_ID-mjpgUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-miniUrl">
            <Content (0.0) "gfycat-GFYCAT_ID-miniPosterUrl">
            <Content (0.25) "gfycat-GFYCAT_ID-gifUrl">
        """

        (handle_name, handle_match,) = self.get_handle(url)
        handle_method = f'handle_{handle_name}'
        if not hasattr(self, handle_method):
            raise NotImplementedError((
                f"no handled method named {handle_method!r} is implemented "
                f"for {self!r}"
            ))
        if self.authentication != AuthTypes.NONE:
            if not isinstance(auth, tuple) or not len(auth) == 2:
                registry = AuthRegistry()
                if self.__class__ not in registry:
                    raise exceptions.AuthenticationError((
                        f"no valid authentication found for "
                        f"{self.__class__!r}, received {auth!r} and no "
                        f"registry entry"
                    ))
                auth = registry[self.__class__]
                del registry
            self.authenticate(auth)
        for content in getattr(self, handle_method)(url, handle_match):
            yield content