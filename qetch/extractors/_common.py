# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import re
import abc
from typing import Any, List, Match, Tuple, Generator

import attr
from furl import furl
from requests_html import HTMLSession

from .. import exceptions, auth


@attr.s
class BaseExtractor(abc.ABC):
    """The base extractor.
    `All extractors should extend this.`
    """

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
        """The default session for the extractor.

        Returns:
            HTMLSession: The default session for the extractor.
        """

        if not hasattr(self, "_session"):
            self._session = HTMLSession()
        return self._session

    @classmethod
    def get_handle(cls, url: str) -> Tuple[str, Match]:
        """Gets the handle match for a given url.

        Args:
            url (str): The url to get the handle match for.

        Returns:
            tuple[str, Match]: A tuple of handle and the match for the url.
        """

        for (handle_name, handle_pattern) in cls.handles.items():
            match = re.match(handle_pattern, url)
            if match:
                return (handle_name, match)

    @classmethod
    def can_handle(cls, url: str):
        """Determines if an extractor can handle a url.

        Args:
            url (str): The url to check

        Returns:
            bool: True if the extractor can handle, otherwise False
        """

        return cls.get_handle(url) is not None

    def authenticate(self, auth_tuple: Tuple[str, str]):
        """Handles authenticating the extractor if necessary.

        Args:
            auth_tuple (tuple[str, str]): The authentication tuple is available.
        """

        pass

    def merge(self, ordered_filepaths: List[str]) -> str:
        """Handles merging downloaded fragments into a resulting file.

        Args:
            ordered_filepaths (list[str]): The list of ordered filepaths to \
                downloaded fragments.

        Returns:
            str: The resulting merged file's filepath.
        """

        return (ordered_filepaths[0] if len(ordered_filepaths) > 0 else None)

    def extract(
        self, url: str, auth_tuple: Tuple[str, str] = None
    ) -> Generator[List[Any], None, None]:
        """Extracts lists of content from a url.

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
            auth_tuple (tuple[str, str], optional): The auth tuple if available.

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

        (handle_name, handle_match) = self.get_handle(url)
        handle_method = f"handle_{handle_name}"
        if not hasattr(self, handle_method):
            raise NotImplementedError(
                (
                    f"no handled method named {handle_method!r} is implemented for "
                    f"{self!r}"
                )
            )

        if self.authentication != auth.AuthTypes.NONE:
            if not isinstance(auth_tuple, tuple):
                registry = auth.AuthRegistry()
                # try to get authentication entry from registry
                if self.name not in registry:
                    raise exceptions.AuthenticationError(
                        (
                            f"no valid authentication found for {self!r}, received "
                            f"{auth_tuple!r} and no registry entry for key "
                            f"{self.name!r}"
                        )
                    )
                auth_tuple = registry[self.name]
                del registry

            # validate authentication format
            if len(auth_tuple) != len(self.authentication.value):
                raise exceptions.AuthenticationError(
                    (
                        f"invalid authentication format for {self!r}, got values "
                        f"{auth!r} but expects format {self.authentication.value!r}"
                    )
                )
            self.authenticate(auth_tuple)

        # handle extracting content using appropriate extraction method
        for content in getattr(self, handle_method)(url, handle_match):
            yield content
