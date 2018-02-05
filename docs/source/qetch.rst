=============
Qetch Package
=============

This is the base qetch package.

.. automodule:: qetch
    :members:
    :undoc-members:
    :show-inheritance:

|

qetch.auth
----------

.. automodule:: qetch.auth
    :members:
    :show-inheritance:


qetch.content
-------------

This is the base content instance which is used to normalize hosted media for use between :mod:`~qetch.extractors` and :mod:`~qetch.downloaders`.
The most important attributes of this object are the following:

* :attr:`~qetch.content.Content.uid`: The unique id that identifies the content
    (*even unique between levels of quality*).
* :attr:`~qetch.content.Content.source`: The url that was given to the extractor for extracting.
* :attr:`~qetch.content.Content.fragments`: A list of urls where the raw content can be retrieved from
    (*is a list in case that content is fragmented/segmented*).
* :attr:`~qetch.content.Content.quality`: A float value between 0 and 1, 1 being the best quality format.

.. automodule:: qetch.content
    :members:
    :undoc-members:
    :show-inheritance:


qetch.extractors
----------------

Below are a list of the currently included extractors which all should extend :class:`~qetch.extractors._common.BaseExtractor`.
The purpose of extractors is to take a url and yield lists of similar content instances.

This allows content with various levels of quality to have a relationship with eachother.
For example, gfycat.com hosts various levels and formats of some media (mp4, webm, webp, gif, etc...).
When extracting the content for a gfycat url, an extractor will yield a list containing different content instances for each of these formats and different :attr:`~qetch.content.Content.quality` values.
This allows the developer to `hopefully` correctly choose the desired content for a list of content extracted for a single resource.


BaseExtractor
'''''''''''''
.. automodule:: qetch.extractors._common
    :members:
    :show-inheritance:

gfycat
''''''
.. automodule:: qetch.extractors.gfycat
    :members:
    :undoc-members:
    :show-inheritance:


qetch.downloaders
-----------------

Below are a list of the currently included downloaders which all should extend :class:`~qetch.downloaders._common.BaseDownloader`.
The purpose of downloaders is to take an extracted :class:`~qetch.content.Content` instance in order to download and merge the fragments resulting in the content being downloaded to a given local system path.

Downloaders should be built to allow parrallel fragment downloading and multiple connection downlaods for each fragment.
For example, the :class:`~qetch.downloaders.http.HTTPDownloader` allows both ``max_fragments`` and ``max_connections`` as parameters to the :func:`~qetch.downloaders._common.BaseDownloader.download` method.
This will allow ``max_fragments`` to be processed at the same time and ``max_connections`` to be used for the download of each of those fragments.
**This means that up to** ``(max_fragments * max_connections)`` **between your IP and the host may exist at any point during the download.**

**It is best to scrutinize this to allow only 10 connections at max, since many hosts will flag/ban IPs using more than 10 connections**.
By default, ``max_fragments`` and ``max_connections`` are set to 1 and 8 respectively allowing a maximum of 8 connections from your IP to the host at any point, but only allows 1 fragment to be downloaded at a time.

Downloaders should also support the usage of a ``progress_hook`` which is sent updates on the download progress every ``update_delay`` seconds.
See the example in :func:`~qetch.downloaders._common.BaseDownloader.download` for a very simple example.

BaseDownloader
''''''''''''''
.. automodule:: qetch.downloaders._common
    :members:
    :show-inheritance:

http
''''
.. automodule:: qetch.downloaders.http
    :members:
    :undoc-members:
    :show-inheritance:

