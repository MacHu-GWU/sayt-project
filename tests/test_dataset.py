# -*- coding: utf-8 -*-

import typing as T
import uuid
import time
import random

import faker
from diskcache import Cache
from rich import print as rprint

from sayt.logger import logger
from sayt.paths import dir_project_root
from sayt.dataset import (
    BaseField,
    StoredField,
    IdField,
    IdListField,
    KeywordField,
    TextField,
    NumericField,
    DatetimeField,
    BooleanField,
    NgramField,
    NgramWordsField,
    DataSet,
)


fake = faker.Faker()


class TestField:
    def test_error(self):
        field = BooleanField(name="bool_field")
        assert field._is_sortable() is False
        assert field._is_ascending() is False

    def test_seder(self):
        fields = [
            IdField(name="id", stored=True),
            TextField(name="title", stored=True),
            NgramField(name="author", stored=True, minsize=2, maxsize=6),
            NumericField(name="year", stored=True, sortable=True, ascending=False),
        ]
        for field in fields:
            dct = field.to_dict()
            obj = BaseField.from_dict(dct)
            assert obj == field



def downloader_one_book():
    return [
        {
            "id": "id-1234",
            "title": "Sustainable Energy - without the hot air",
            "author": "MacKay, David JC",
            "year": 2009,
        },
    ]


def downloader_1000_books():
    return [
        {
            "id": uuid.uuid4().hex,
            "title": fake.sentence(),
            "author": fake.name(),
            "year": random.randint(1980, 2020),
        }
        for _ in range(1000)
    ]


def create_book_dataset():
    return DataSet(
        dir_index=dir_project_root.joinpath(".index"),
        index_name="book-dataset",
        fields=[
            IdField(name="id", stored=True),
            TextField(name="title", stored=True),
            NgramField(name="author", stored=True, minsize=2, maxsize=6),
            NumericField(name="year", stored=True, sortable=True, ascending=False),
        ],
        cache=Cache(str(dir_project_root.joinpath(".cache")), tag_index=True),
        cache_key="book-dataset",
        cache_expire=1,
        cache_tag="book-dataset",
    )


def downloader_50_machines() -> T.List[T.Dict[str, T.Any]]:
    n = 50
    envs = ["dev", "test", "prod"]
    return [
        {"id": ith, "name": f"{ith}th-{random.choice(envs)}-machine"}
        for ith in range(1, 1 + n)
    ]


def create_machine_dataset():
    return DataSet(
        dir_index=dir_project_root.joinpath(".index"),
        index_name="machine-dataset",
        fields=[
            NgramWordsField(name="name", stored=True, minsize=2, maxsize=6),
            StoredField(name="raw"),
        ],
        cache=Cache(str(dir_project_root.joinpath(".cache")), tag_index=True),
        cache_key="machine-dataset",
        cache_expire=1,
        cache_tag="machine-dataset",
        downloader=downloader_50_machines,
    )


class TestDataset:
    def _test_search(self):
        ds = create_book_dataset()
        ds.remove_all_index()
        ds.remove_all_cache()
        ds.build_index(data=downloader_one_book())

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

    def _test_performance(self):
        ds = create_book_dataset()
        ds.remove_all_index()
        ds.remove_all_cache()
        ds.downloader = downloader_1000_books

        query = "police"
        res = ds.search(query)
        # rprint(res)
        assert isinstance(res, list)

        res = ds.search(query, simple_response=False)
        # rprint(res)
        assert isinstance(res, dict)
        assert res["cache"] is False

        res = ds.search(query, simple_response=False)
        # rprint(res)
        assert isinstance(res, dict)
        assert res["cache"] is True

    def _test_downloader(self):
        ds = create_machine_dataset()
        ds.remove_all_index()
        ds.remove_all_cache()

        def verify_result(res):
            assert len(res["hits"]) == 3
            for hit in res["hits"]:
                name = hit["_source"]["name"]
                assert "dev" in name

        # event it is the first time, we force to refresh data
        res = ds.search(
            refresh_data=True, query="dev", limit=3, simple_response=False, verbose=True
        )
        # rprint(res)
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False

        # this time it should use cache and the data is not fresh
        res = ds.search(query="dev", limit=3, simple_response=False, verbose=True)
        # rprint(res)
        verify_result(res)
        assert res["fresh"] is False
        assert res["cache"] is True

        # now we force to refresh the data
        res = ds.search(refresh_data=True, query="dev", limit=3, simple_response=False)
        # rprint(res)
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False

        # let's wait 1 second, the cache should expire
        time.sleep(1)
        res = ds.search(refresh_data=True, query="dev", limit=3, simple_response=False)
        # rprint(res)
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False

    def test(self):
        print("")
        self._test_search()
        self._test_performance()
        self._test_downloader()


if __name__ == "__main__":
    from sayt.tests.helper import run_cov_test

    run_cov_test(__file__, "sayt.dataset", preview=False)
