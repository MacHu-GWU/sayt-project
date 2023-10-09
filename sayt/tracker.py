# -*- coding: utf-8 -*-

"""
This module implements the last operational time tracker and concurrency locker
mechanism.
"""

import typing as T
import json
import contextlib
import dataclasses
from pathlib import Path
from datetime import datetime, timedelta


class TrackerIsLockedError(EnvironmentError):
    pass


@dataclasses.dataclass
class Tracker:
    """
    Usage:

        # suppose you have many worker may work on the same job
        # this is the code for first worker
        # before it run the job, it checks if it is locked
        # and moves forward only if it is not locked
        # wrap the work logic in a try finally and unlock it anyway
        >>> tracker = Tracker.new("/path/to/tracker.json")
        >>> if tracker.is_locked() is False:
        ...     tracker.lock_it(expire=10)
        ...     try:
        ...         # do something
        ...     finally:
        ...         tracker.unlock_it()

        # this is the code for other workers attempt to work on the same job
        >>> tracker = Tracker.new("/path/to/tracker.json")
        # it will return True, so the second worker won't do anything
        >>> if tracker.is_locked() is False:
        >>>     ...

    :param path: path to the local tracker json file.
    :param start: work start datetime in ISO format, also the lock time.
    :param end: work end datetime in ISO format.
    :param locked: boolean value to indicate whether it is locked, if it is True,
        it doesn't mean that it is locked, you also have to check the expire time
    :param expire: the lock expire datetime in ISO format.
    """

    path: Path = dataclasses.field()
    start: T.Optional[str] = dataclasses.field(default=None)
    end: T.Optional[str] = dataclasses.field(default=None)
    locked: T.Optional[bool] = dataclasses.field(default=None)
    expire: T.Optional[str] = dataclasses.field(default=None)

    @classmethod
    def new(cls, path: T.Union[Path, str, T.Any]):
        path = Path(path)
        try:
            data = json.loads(path.read_text())
            data["path"] = path
            return cls(**data)
        except FileNotFoundError:
            return cls(path=path)

    def is_locked(self) -> bool:
        if self.locked:
            if datetime.utcnow() <= datetime.fromisoformat(self.expire):
                return True
        return False

    def _write(self):
        data = dataclasses.asdict(self)
        data.pop("path")
        try:
            self.path.write_text(json.dumps(data))
        except FileNotFoundError:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data))

    def lock_it(self, expire: int):
        """ """
        now = datetime.utcnow()
        self.start = now.isoformat()
        self.end = None
        self.locked = True
        self.expire = (now + timedelta(seconds=expire)).isoformat()
        self._write()

    def unlock_it(self):
        self.end = datetime.utcnow().isoformat()
        self.locked = False
        self._write()

    @classmethod
    @contextlib.contextmanager
    def lock(cls, path: Path, expire: int):
        tracker = cls.new(path)
        try:
            if tracker.is_locked() is True:
                raise TrackerIsLockedError
            else:
                tracker.lock_it(expire)
                yield tracker
        except TrackerIsLockedError as e:
            raise e
        except Exception as e:
            tracker.unlock_it()
            raise e
        tracker.unlock_it()
