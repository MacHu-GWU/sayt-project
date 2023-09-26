.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

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
