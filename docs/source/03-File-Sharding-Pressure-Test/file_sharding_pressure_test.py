# -*- coding: utf-8 -*-

"""
Environment: MacOS M1 Pro 32G RAM

Result:

- Reset dir_temp: from 2023-09-25 02:48:06.710175 to 2023-09-25 02:48:16.270893 elapsed 9.560718 second.
- cpu count: 10
- first: 736d81ffd6f549f3b9e78812c6d5b7f6.txt
- Create many files: from 2023-09-25 02:48:16.271288 to 2023-09-25 02:48:22.483035 elapsed 6.211747 second.
- last: 5b12dd8262784d8eab6001f4c069f708.txt
- Count files: from 2023-09-25 02:48:22.484286 to 2023-09-25 02:48:22.967109 elapsed 0.482823 second.
- n files: 100002
- read first file: from 2023-09-25 02:48:22.967166 to 2023-09-25 02:48:22.982786 elapsed 0.015620 second.
- read last file: from 2023-09-25 02:48:22.982826 to 2023-09-25 02:48:22.998569 elapsed 0.015743 second.
"""

import os
import shutil
import uuid
from pathlib import Path
from fixa.timer import DateTimeTimer
from mpire import WorkerPool

dir_temp = Path.home().joinpath("tmp")


def reset_dir_temp():
    """
    清空临时文件夹中的所有文件. 用于模拟清空一个里面有巨多小文件的文件夹的情况.
    """
    with DateTimeTimer("Reset dir_temp"):
        shutil.rmtree(dir_temp, ignore_errors=True)
        dir_temp.mkdir(parents=True, exist_ok=True)


def _create_many_files(n: int):
    for _ in range(n):
        p = dir_temp / f"{uuid.uuid4().hex}.txt"
        p.write_text("hello world")


def create_many_files():
    """
    创建超级多的小文件, 用于模拟一个文件夹中有巨多小文件的情况.

    5.626452 second.
    """
    n_batch = 10
    n_file_per_batch = 10000
    args = [dict(n=n_file_per_batch) for _ in range(n_batch)]

    print(f"cpu count: {os.cpu_count()}")

    first_id = uuid.uuid4().hex
    p = dir_temp / f"{first_id}.txt"
    p.write_text("hello world")
    print(f"first: {p.name}")

    with DateTimeTimer("Create many files"):
        with WorkerPool() as pool:
            pool.map(_create_many_files, args)

    last_id = uuid.uuid4().hex
    p = dir_temp / f"{last_id}.txt"
    p.write_text("hello world")
    print(f"last: {p.name}")

    return first_id, last_id


def count_files():
    """
    统计文件夹中有多少个文件.

    0.393739 second.
    """
    with DateTimeTimer("Count files"):
        for i, _ in enumerate(dir_temp.glob("**/*"), start=1):
            pass
    print(f"n files: {i}")


def test_read_first_and_last_file(first_id, last_id):
    """
    测试在已知文件夹中第一个和最后一个文件的情况下, 读取这两个文件的时间是否有差异, 平均速度多少.

    from 2023-09-25 02:41:23.647906 to 2023-09-25 02:41:23.659767 elapsed 0.011861 second.
    from 2023-09-25 02:41:23.659789 to 2023-09-25 02:41:23.671414 elapsed 0.011625 second.
    """
    n_times = 1000
    with DateTimeTimer("read first file"):
        for _ in range(n_times):
            p = dir_temp / f"{first_id}.txt"
            p.read_text()

    with DateTimeTimer("read last file"):
        for _ in range(n_times):
            p = dir_temp / f"{last_id}.txt"
            p.read_text()


if __name__ == "__main__":
    reset_dir_temp()
    first_id, last_id = create_many_files()
    count_files()
    test_read_first_and_last_file(first_id, last_id)
