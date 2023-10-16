# -*- coding: utf-8 -*-

from sayt import api


def test():
    _ = api
    _ = api.BaseField
    _ = api.StoredField
    _ = api.IdField
    _ = api.IdListField
    _ = api.KeywordField
    _ = api.TextField
    _ = api.NumericField
    _ = api.DatetimeField
    _ = api.BooleanField
    _ = api.NgramField
    _ = api.NgramWordsField
    _ = api.T_DOCUMENT
    _ = api.T_DOWNLOADER
    _ = api.T_Field
    _ = api.T_Hit
    _ = api.T_Result
    _ = api.DataSet
    _ = api.exc
    _ = api.exc.MalformedDatasetSettingError


if __name__ == "__main__":
    from sayt.tests import run_cov_test

    run_cov_test(__file__, "sayt.api", preview=False)
