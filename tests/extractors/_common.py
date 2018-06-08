# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import abc

from qetch.content import (Content,)

import requests_html


class ExtractorTest(abc.ABC):
    """ The base extractor for all extractor tests.
    """

    @abc.abstractproperty
    def extractor(self):
        """ The extractor to use for testing.

        Decorators:
            abc.abstractproperty

        Raises:
            NotImplementedError:
                - Should be overriden by subclasses.
        """

        raise NotImplementedError()


    @abc.abstractproperty
    def should_handle(self):
        """ A dictionary of (url, [group_1, group_2,....]).

        Decorators:
            abc.abstractproperty

        Raises:
            NotImplementedError:
                - Should be overriden by subclasses.
        """

        raise NotImplementedError()

    @abc.abstractproperty
    def should_extract(self):
        """ A list of urls to check extraction with.

        Decorators:
            abc.abstractproperty

        Raises:
            NotImplementedError:
                - Should be overriden by subclasses.
        """

        raise NotImplementedError()

    def test_up(self):
        """ Tests if any of the supported extractors domains are running.
        """

        is_up = False
        for domain in self.extractor.domains:
            is_up = requests_html.head(f'https://{domain}').status_code == 200

        assert is_up, (
            f'no domains for extractor {self.extractor!r} '
            f'{tuple(self.extractor.domains)!r} appear to be running'
        )


    def test_handles(self):
        """ Tests the handles for an extractor with the test's should_handle.
        """

        for (url, groups,) in self.should_handle.items():
            groups = tuple(groups)
            match_pair = self.extractor.get_handle(url)
            assert match_pair is not None, (
                f'extractor {self.extractor!r} cannot handle url {url!r}'
            )

            (handle_name, handle_match,) = match_pair
            assert isinstance(handle_name, str) and len(handle_name) > 0, (
                f'extractor {self.extractor!r} returned empty handle name '
                f'({handle_name!r}) for match {handle_match!r}'
            )
            assert hasattr(handle_match, 'groups'), (
                f'extractor {self.extractor!r} returned non-match '
                f'({handle_match!r}) for handle name ({handle_name!r})'
            )
            assert handle_match.groups() == groups, (
                f'extractor {self.extractor!r} did not return expected groups '
                f'{groups!r}, returned {handle_match.groups()!r} for url '
                f'{url!r}'
            )

    def test_extract(self):
        """ Tests the bas extract of the extractor with test's should_extract.
        """

        for url in self.should_extract:
            assert isinstance(url, str) and len(url) > 0, (
                f'given url {url!r} for extractor {self.extractor!r} '
                f'is not a non-zero length string'
            )

            extractor = self.extractor()
            for content_list in extractor.extract(url):
                # check that content list is a list of at least 1 Content isnt.
                assert isinstance(content_list, list) and \
                    len(content_list) > 0 and all(
                        isinstance(content, Content)
                        for content in content_list
                    ), (
                    f'extracted content list {content_list!r} from extractor '
                    f'{extractor!r} is not a non-zero length list of Content'
                )
