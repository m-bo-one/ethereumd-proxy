import asyncio
import plyvel


class CacheLevelDB:

    def __init__(self, name, *, loop=None, executor=None):
        self._loop = loop or asyncio.get_event_loop()
        self._db = plyvel.DB(name, create_if_missing=True)
        self._executor = executor

    def get(self, key, default=None):
        return self._loop.run_in_executor(self._executor, self._db.get,
                                          key, default)

    def set(self, key, value):
        return self._loop.run_in_executor(self._executor, self._db.put,
                                          key, value)

    def close(self):
        return self._loop.run_in_executor(self._executor, self._db.close)
