# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

from ._common import (ExtractorTest,)
from qetch.extractors import (GfycatExtractor,)

import furl
import requests


class TestGfycatExtractor(ExtractorTest):

    extractor = GfycatExtractor
    should_handle = {
        'https://www.gfycat.com/abc': ['abc'],
        'https://www.gfycat.com/ABC': ['ABC'],
        'https://www.gfycat.com/aBc': ['aBc'],
        'https://www.gfycat.com/abc/': ['abc'],
        'https://www.gfycat.com/gifs/detail/abc': ['abc'],
        'https://www.gfycat.com/gifs/detail/ABC': ['ABC'],
        'https://www.gfycat.com/gifs/detail/aBc': ['aBc'],
        'https://www.gfycat.com/gifs/detail/abc/': ['abc'],
        'https://xyz.gfycat.com/abc.ext': ['abc'],
        'https://xyz.gfycat.com/ABC.ext': ['ABC'],
        'https://xyz.gfycat.com/aBc.ext': ['aBc'],
        'https://xyz.gfycat.com/abc.000': ['abc'],
        'https://xyz.gfycat.com/ABC.000': ['ABC'],
        'https://xyz.gfycat.com/aBc.000': ['aBc'],
    }
    should_extract = [
        'https://www.gfycat.com/impracticalremotecentipede',
        'https://www.gfycat.com/gifs/detail/impracticalremotecentipede',
        'https://giant.gfycat.com/impracticalremotecentipede.mp4',
    ]
