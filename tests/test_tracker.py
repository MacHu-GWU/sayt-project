# -*- coding: utf-8 -*-

import time
import shutil
from pathlib import Path

import pytest

from sayt.tracker import Tracker, TrackerIsLockedError

path = Path(__file__).absolute().parent.joinpath("tracker", "tracker.json")
shutil.rmtree(path.parent, ignore_errors=True)


def _test_case_1():
    path.unlink(missing_ok=True)

    tracker = Tracker.new(path)
    tracker.lock_it(expire=1)
    assert tracker.is_locked() is True

    tracker1 = Tracker.new(path)
    assert tracker1.is_locked() is True

    tracker.unlock_it()
    tracker1 = Tracker.new(path)
    assert tracker1.is_locked() is False


def _test_case_2():
    path.unlink(missing_ok=True)

    tracker = Tracker.new(path)
    tracker.lock_it(expire=1)
    assert tracker.is_locked() is True

    tracker1 = Tracker.new(path)
    assert tracker1.is_locked() is True

    time.sleep(1)
    tracker1 = Tracker.new(path)
    assert tracker1.is_locked() is False


def _test_case_3():
    with Tracker.lock(path, expire=1):
        assert Tracker.new(path=path).is_locked() is True
    time.sleep(1)
    assert Tracker.new(path=path).is_locked() is False

    with pytest.raises(ValueError):
        with Tracker.lock(path, expire=1):
            raise ValueError
    assert Tracker.new(path=path).is_locked() is False

    Tracker.new(path=path).lock_it(expire=1)
    with pytest.raises(TrackerIsLockedError):
        with Tracker.lock(path, expire=1):
            print("this won't execute")
    assert Tracker.new(path=path).is_locked() is True


def test():
    _test_case_1()
    _test_case_2()
    _test_case_3()


if __name__ == "__main__":
    from sayt.tests import run_cov_test

    run_cov_test(__file__, "sayt.tracker", preview=False)
