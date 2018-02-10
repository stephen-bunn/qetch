===============
Getting Started
===============

    This framework is my attempt at modernizing the type of content extraction that `youtube-dl <https://rg3.github.io/youtube-dl/>`_ performs.
    It's called "Qetch" because I couldn't think of anything better...

I started this because I needed a way of extracting and downloading raw content from just a user dropping in a url.
The issue with current solutions is that they have an unintuitive API and an overcomplicated implementation (no offense intended, I really appreciate the work that went into the current solutions).

*But I'm a stickler* and wanted a cleaner more modular way of building extractors and quicker downloaders; also something that doesn't strive to be "Pure Python" **because pure Python isn't real Python**.


.. note:: **Qetch requires Python 3.6+.** Because of support dropping for Python 2.7 and so many various improvments from 3.5, it was decided unanimously (meaning just me) that this project will only support 3.6+.

.. _getting-started_installation:

Installation
------------
Since Qetch is in pre-development/proof-of-concept stages, it is not yet on `PyPi <https://pypi.org/>`_.
You can install Qetch by cloning the repository at `stephen-bunn/qetch <https://github.com/stephen-bunn/qetch>`_ and installing the dependencies.

.. code-block:: bash

    git clone https://github.com/stephen-bunn/qetch.git
    cd ./qetch
    pip install -r ./requirements.txt


`Pipenv <http://pipenv.readthedocs.io/en/latest/>`_ is also an option! *If you don't yet know about Pipenv, you should definitely start using it!*


.. _getting-started_basic-usage:

Basic Usage
-----------

The quickest way to utilize Qetch is to just allow Qetch to discover what extractors/downloaders are required for a URL you give it.

.. code-block:: python

    import os
    import qetch

    # discover what extractor can handle a URL and initialize it
    extractor = qetch.get_extractor(URL, init=True)

    # extract the first discovered content
    content = next(extractor.extract(URL))[0]

    # discover what downloader can handle the extracted content and initialize it
    downloader = qetch.get_downloader(content, init=True)

    # download the content to a given filepath
    downloader.download(content, os.path.expanduser('~/Downloads/downloaded_file'))


As shown in the example above, there are several objects that make up Qetch.
You can learn more about them in the :doc:`./project-structure` documentation and the :doc:`./qetch` reference.
