# -*- coding: utf-8 -*-

import typing as T
import time
import uuid
import random

import faker
import pytest
from diskcache import Cache
from fixa.timer import DateTimeTimer
from rich import print as rprint

from sayt.paths import dir_project_root
from sayt.dataset import (
    DataSet,
    Field,
    MalformedFieldSettingError,
    MalformedDatasetSettingError,
)


fake = faker.Faker()


class TestField:
    def test_error(self):
        with pytest.raises(MalformedFieldSettingError):
            Field(name="myfield", type_is_phrase=True, type_is_numeric=True)

        with pytest.raises(MalformedFieldSettingError):
            Field(name="myfield", is_sortable=True)


class TestDataset:
    def test(self):
        ds = DataSet(
            dir_index=dir_project_root.joinpath(".index"),
            index_name="my-dataset",
            fields=[
                Field(
                    name="id",
                    type_is_store=True,
                    type_is_id=True,
                ),
                Field(
                    name="title",
                    type_is_store=True,
                    type_is_phrase=True,
                ),
                Field(
                    name="author",
                    type_is_store=True,
                    type_is_ngram=True,
                    ngram_minsize=2,
                    ngram_maxsize=6,
                ),
                Field(
                    name="year",
                    type_is_store=True,
                    type_is_numeric=True,
                    is_sortable=True,
                ),
            ],
            cache=Cache(str(dir_project_root.joinpath(".cache")), tag_index=True),
            cache_key="my-dataset",
            cache_expire=1,
            cache_tag="dev",
        )
        ds.remove_all_index()

        # ----------------------------------------------------------------------
        # Test functionality
        # ----------------------------------------------------------------------
        data = [
            {
                "id": "id-1234",
                "title": "Sustainable Energy - without the hot air",
                "author": "MacKay, David JC",
                "year": 2009,
            },
        ]

        ds.build_index(data=data)

        def assert_hit(query):
            res = ds.search(query)
            assert res[0]["id"] == "id-1234"

        def assert_not_hit(query):
            res = ds.search(query)
            assert len(res) == 0

        def simple_case():
            query = "id-1234"
            assert_hit(query)

            # second time will use cache
            query = "id-1234"
            assert_hit(query)

            query = "energy"
            assert_hit(query)

            query = "dav"
            assert_hit(query)

            query = "2009"
            assert_hit(query)

        def field_specific_case():
            query = "id:id-1234"
            assert_hit(query)

            query = "title:energy"
            assert_hit(query)

            query = "author:dav"
            assert_hit(query)

            query = "year:2009"
            assert_hit(query)

        def range_query_case():
            query = "year:>2000"
            assert_hit(query)

            query = "year:<2020"
            assert_hit(query)

            query = "year:>2000 AND year:<2020"
            assert_hit(query)

            query = "year:[2000 TO]"
            assert_hit(query)

            query = "year:[TO 2020]"
            assert_hit(query)

            query = "year:[2000 TO 2020]"
            assert_hit(query)

            query = "year:>2020"
            assert_not_hit(query)

            query = "year:<2000"
            assert_not_hit(query)

        def logical_operator_case():
            query = "title:energy OR author:xyz"
            assert_hit(query)

            query = "title:monster OR author:dav"
            assert_hit(query)

            query = "title:monster AND author:xyz"
            assert_not_hit(query)

        def fuzzy_search_case():
            query = "title:energi~1"
            assert_hit(query)

        simple_case()
        field_specific_case()
        range_query_case()
        logical_operator_case()
        fuzzy_search_case()

        # ----------------------------------------------------------------------
        # Test performance
        # ----------------------------------------------------------------------
        data = [
            {
                "id": uuid.uuid4().hex,
                "title": fake.sentence(),
                "author": fake.name(),
                "year": random.randint(1980, 2020),
            }
            for _ in range(1000)
        ]

        with DateTimeTimer("build index"):
            ds.build_index(data=data)

        query = "police"
        res = ds.search(query)
        rprint(res)


if __name__ == "__main__":
    from sayt.tests.helper import run_cov_test

    run_cov_test(__file__, "sayt.dataset", preview=False)
