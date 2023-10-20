.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.6.2 (2023-10-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Be able to serialize and deserialize ``BaseField`` object.

**Miscellaneous**

- Add downloading block to logging message.


0.6.1 (2023-10-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**💥 Breaking change**

- Rework the ``DataSet`` class, merge features in ``RefreshableDataSet`` into the ``DataSet`` class.
- ``RefreshableDataSet`` is removed.


0.5.3 (2023-10-14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Fix a bug that the ``query`` parameter in ``RefreshableDataSet.search`` should be mandatory.


0.5.2 (2023-10-13)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- Add the ``DataSet.is_data_cache_exists()`` method.

**Miscellaneous**

- Improve code coverage test.


0.5.1 (2023-10-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add concurrency lock mechanism to prevent refreshing the index if there is another thread already working on it.

**Minor Improvements**

- Add the ``DataSet.is_indexing()`` and ``RefreshableDataSet.is_indexing()`` method.

**Bugfixes**

- Fix a bug that the cache is not correctly removed when rebuild the dataset.


0.4.1 (2023-09-30)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add ``RefreshableDataSet`` a new class that extend the ``DataSet``, it allows user to refresh the index automatically when necessary.
- Add the following public api:
    - ``sayt.api.T_Hit``
    - ``sayt.api.T_Result``
    - ``sayt.api.T_RECORD``
    - ``sayt.api.T_KWARGS``
    - ``sayt.api.T_DOWNLOADER``
    - ``sayt.api.T_CACHE_KEY_DEF``
    - ``sayt.api.T_CONTEXT``
    - ``sayt.api.T_EXTRACTOR``
    - ``sayt.api.T_RefreshableDataSetResult``
    - ``sayt.api.RefreshableDataSet``

**Miscellaneous**

- since this library only supports Python3.8+, we removed the optional ``cached-property`` and ``dataclasses`` dependencies.


0.3.2 (2023-09-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- the final whoosh index name is the ``DataSet.index_name`` as it is. we no longer automatically hash the index name

**Bugfixes**

- fix a bug the cache_tag is not correctly set in ``DataSet.search(...)`` method.


0.3.1 (2023-09-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**💥 Breaking change**

- Drop support for Python3.7 because of the ``TypedDict`` type hint.

**Features and Improvements**

- Add ``simple_response: bool = True`` option to ``DataSet.search(...)`` method, allow to return elasticsearch HTTP response styled result.


0.2.3 (2023-09-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Fix a bug that when ``DataSet.search(...)`` method forget to set the result cache along with the tag. So that this cache cannot be cleared by ``DataSet.clear_cache`` method.


0.2.2 (2023-09-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- Allow user to use pass in ``dir_cache`` when constructing ``DataSet`` object. It gives user more control on creating the cache object.

**Bugfixes**

- Fix a bug that ``NgramWordsField`` should not have ``phrase`` attribute.

**Miscellaneous**


0.2.1 (2023-09-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**💥 Breaking change**

- Rework the field system, make it fully compatible with the underlying ``whoosh.fields`` system.

**Features and Improvements**

- Rework the field system, there was only one ``Field`` class that can create a varieties of whoosh fields object. Now we use full list of whoosh compatible ``XyzField`` classes.
- Add the following public api:
    - ``sayt.api.BaseField``
    - ``sayt.api.StoredField``
    - ``sayt.api.IdField``
    - ``sayt.api.IdListField``
    - ``sayt.api.KeywordField``
    - ``sayt.api.TextField``
    - ``sayt.api.NumericField``
    - ``sayt.api.DatetimeField``
    - ``sayt.api.BooleanField``
    - ``sayt.api.NgramField``
    - ``sayt.api.NgramWordsField``
    - ``sayt.api.T_Field``


0.1.1 (2023-09-25)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- First release
- Add the following public API:
    - ``sayt.api.Field``
    - ``sayt.api.DataSet``
    - ``sayt.api.exc``
