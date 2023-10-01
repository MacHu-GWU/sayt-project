# -*- coding: utf-8 -*-

import typing as T
import uuid
import random

import faker
import pytest
from diskcache import Cache
from fixa.timer import DateTimeTimer
from rich import print as rprint

from sayt.paths import dir_project_root
from sayt.dataset import (
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
    get_cache_key,
    RefreshableDataSet,
    MalformedDatasetSettingError,
    T_RECORD,
    T_KWARGS,
    T_DOWNLOADER,
    T_CACHE_KEY_DEF,
    T_CONTEXT,
    T_EXTRACTOR,
    T_RefreshableDataSetResult,
)


fake = faker.Faker()


class TestField:
    def test_error(self):
        field = BooleanField(name="bool_field")
        assert field._is_sortable() is False
        assert field._is_ascending() is False


class TestDataset:
    def test(self):
        ds = DataSet(
            dir_index=dir_project_root.joinpath(".index"),
            index_name="my-dataset",
            fields=[
                IdField(name="id", stored=True),
                TextField(name="title", stored=True),
                NgramField(
                    name="author",
                    stored=True,
                    minsize=2,
                    maxsize=6,
                ),
                NumericField(
                    name="year",
                    stored=True,
                    sortable=True,
                    ascending=False,
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


def test_get_cache_key():
    assert get_cache_key(
        cache_key_def=["hello", "world"],
        download_kwargs={},
        context={},
    ) == ["hello", "world"]


class TestRefreshableDataset:
    def test(self):
        def downloader(env: str) -> T.List[T.Dict[str, T.Any]]:
            # print("get_data() called")
            n = 10
            return [
                {"id": ith, "name": f"{ith}th-{env}-machine"} for ith in range(1, 1 + n)
            ]

        def cache_key_def(
            download_kwargs: T_KWARGS,
            context: T_CONTEXT,
        ):
            return [download_kwargs["env"]]

        def extractor(
            record: T_RECORD,
            download_kwargs: T_KWARGS,
            context: T_CONTEXT,
        ) -> T_RECORD:
            greeting = context["greeting"]
            name = record["name"]
            return {"message": f"{greeting} {name}", "raw": record}

        fields = [
            NgramWordsField(
                name="message",
                stored=True,
                minsize=2,
                maxsize=6,
            ),
            StoredField(
                name="raw",
            ),
        ]
        rds = RefreshableDataSet(
            downloader=downloader,
            cache_key_def=cache_key_def,
            extractor=extractor,
            fields=fields,
            dir_index=dir_project_root.joinpath(".index"),
            cache=Cache(str(dir_project_root.joinpath(".cache")), tag_index=True),
            cache_expire=1,
            context={"greeting": "Hello"},
        )
        rds.remove_all_index()
        rds.remove_all_cache()

        def verify_result(res: T_RefreshableDataSetResult):
            assert len(res["hits"]) == 3
            for hit in res["hits"]:
                message = hit["_source"]["message"]
                assert "dev" in message

        # version 1
        res = rds.search_v1(
            download_kwargs={"env": "dev"},
            refresh_data=True,
            query="dev",
            limit=3,
        )
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False

        res = rds.search_v1(
            download_kwargs={"env": "dev"},
            query="dev",
            limit=3,
        )
        verify_result(res)
        assert res["fresh"] is False
        assert res["cache"] is True

        res = rds.search_v1(
            download_kwargs={"env": "dev"},
            refresh_data=True,
            query="dev",
            limit=3,
        )
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False

        # version 2
        res = rds.search_v2(
            download_kwargs={"env": "dev"},
            refresh_data=True,
            query="dev",
            limit=3,
        )
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False

        res = rds.search_v2(
            download_kwargs={"env": "dev"},
            query="dev",
            limit=3,
        )
        verify_result(res)
        assert res["fresh"] is False
        assert res["cache"] is True

        res = rds.search_v2(
            download_kwargs={"env": "dev"},
            refresh_data=True,
            query="dev",
            limit=3,
        )
        verify_result(res)
        assert res["fresh"] is True
        assert res["cache"] is False


if __name__ == "__main__":
    from sayt.tests.helper import run_cov_test

    run_cov_test(__file__, "sayt.dataset", preview=False)
