# -*- coding: utf-8 -*-

"""
See test_lock.rst
"""

from diskcache import Cache
from sayt.paths import dir_project_root
from sayt.dataset import DataSet, NgramField


def main():
    ds = DataSet(
        dir_index=dir_project_root.joinpath(".index"),
        index_name="my-dataset",
        fields=[
            NgramField(name="title", minsize=2, maxsize=10, stored=True),
        ],
        cache=Cache(str(dir_project_root.joinpath(".cache")), tag_index=True),
        cache_key="my-dataset",
        cache_expire=1,
        cache_tag="dev",
    )
    data = [
        {
            "title": f"Sustainable Energy - without the hot air {id}",
        }
        for id in range(1000)
    ]
    ds.build_index(data, raise_lock_error=True)


if __name__ == "__main__":
    main()
