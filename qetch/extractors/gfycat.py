# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import datetime
from typing import (List,)

from .. import (exceptions,)
from ..content import (Content,)
from ._common import (BaseExtractor,)

import furl
import ujson


class GfycatExtractor(BaseExtractor):

    name = 'gfycat'
    description = ''
    domains = ['gfycat.com']
    handles = {
        'basic': (
            r'^https?://(?:www.)?gfycat.com/'
            r'(?P<id>[a-zA-Z]+)/?$'
        ),
        'detail': (
            r'^https?://(?:www.)?gfycat.com/gifs/detail/'
            r'(?P<id>[a-zA-Z]+)/?$'
        ),
        'raw': (
            r'^https?://(?:www.)?(?:[a-zA-Z]+).gfycat.com/'
            r'(?P<id>[a-zA-Z]+)/?$'
        )
    }

    _api_base = 'http://gfycat.com/cajax/get/'
    _content_urls = (
        'mp4Url',
        'webmUrl', 'webpUrl',
        'mobileUrl', 'mobilePosterUrl',
        'posterUrl',
        'thumb360Url', 'thumb360PosterUrl', 'thumb100PosterUrl',
        'max5mbGif', 'max2mbGif',
        'mjpgUrl',
        'miniUrl', 'miniPosterUrl',
        'gifUrl',
    )
    _quality_map = {
        'mp4Url': 1.0,
        'webmUrl': 0.5,
        'gifUrl': 0.25,
    }

    def _handle_basic(self, source: str, match):
        return self._handle_extract(source, match)

    def _handle_detail(self, source: str, match):
        return self._handle_extract(source, match)

    def _handle_raw(self, source: str, match):
        return self._handle_extract(source, match)

    def _handle_extract(self, source: str, match):
        # build query url using the cajax api base
        query_url = furl.furl(self._api_base)
        query_url.path.add(match.groupdict()['id'])

        # make a request for the api response
        response = self.session.get(query_url.url)
        if response.status_code not in (200,):
            raise exceptions.ExtractionError((
                f"error retrieving source for {query_url.url!r}, "
                f"recieved status {response.status_code}"
            ))
        data = ujson.loads(response.text).get('gfyItem')

        # build and yield content list
        content_list = []
        for url_type in self._content_urls:
            if url_type in data:
                content_list.append(Content(
                    uid=f'{self.name}-{data["gfyId"]}-{url_type}',
                    source=source,
                    fragments=[data.get(url_type)],
                    extractor=self,
                    title=data.get('title'),
                    description=data.get('description'),
                    quality=self._quality_map.get(url_type, 0.0),
                    uploaded_by=(
                        data.get('userName')
                        if data.get('userName') != 'anonymous' else
                        None
                    ),
                    uploaded_date=datetime.datetime.fromtimestamp(
                        int(data.get('createDate'))
                    ),
                    metadata=data
                ))
        yield content_list

    def merge(self, ordered_filepaths: List[str]):
        return (ordered_filepaths[0] if len(ordered_filepaths) > 1 else None)
