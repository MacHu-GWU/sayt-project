
.. image:: https://readthedocs.org/projects/sayt/badge/?version=latest
    :target: https://sayt.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/sayt-project/workflows/CI/badge.svg
    :target: https://github.com/MacHu-GWU/sayt-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/sayt-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/sayt-project

.. image:: https://img.shields.io/pypi/v/sayt.svg
    :target: https://pypi.python.org/pypi/sayt

.. image:: https://img.shields.io/pypi/l/sayt.svg
    :target: https://pypi.python.org/pypi/sayt

.. image:: https://img.shields.io/pypi/pyversions/sayt.svg
    :target: https://pypi.python.org/pypi/sayt

.. image:: https://img.shields.io/badge/Release_History!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/sayt-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/sayt-project

------

.. image:: https://img.shields.io/badge/Link-Document-blue.svg
    :target: https://sayt.readthedocs.io/en/latest/

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://sayt.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/sayt-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/sayt-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/sayt-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/sayt#files


Welcome to ``sayt`` (Search as you type) Documentation
==============================================================================
``sayt`` (Search as you type) is a Python library provide Google liked searching experience using your own dataset. It focus on quickly indexing your own dataset and start searching on it. ``sayt`` is not a full text search database, it doesn't support update/delete operation on your dataset, if your dataset is changed, ``sayt`` will delete the old one and re-index everything.

Features:

1. Support id search, ngram search, full text search, fuzzy search, range search.
2. Query results are automatically cached, and will expire based on your configuration.


.. _install:

Install
------------------------------------------------------------------------------

``sayt`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install sayt

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade sayt
