# -*- coding: utf-8 -*-

from sayt import api


def test():
    _ = api


if __name__ == "__main__":
    from sayt.tests import run_cov_test

    run_cov_test(__file__, "sayt.api", preview=False)
