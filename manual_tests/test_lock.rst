The ``test_lock_worker1.py`` and ``test_lock_worker2.py`` scripts are testing for concurrent write lock.

worker1 script will reset the index folder, try to index 1M documents and lock the tracker. It should take 60+ seconds to finish. The worker2 script will index only 1000 documents. You should run worker1 first, once you see "start building index ...", you can run worker2, and worker2 should raise ``TrackerIsLockedError``.
