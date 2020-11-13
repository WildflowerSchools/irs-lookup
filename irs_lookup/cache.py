import cachetools
from threading import RLock

from .singleton import Singleton


@Singleton
class Cache(object):
    def __init__(self):
        self._cache = cachetools.TTLCache(maxsize=1000, ttl=60*60*24*7)
        self._lock = RLock()

    @property
    def cache(self):
        return self._cache

    @property
    def lock(self):
        return self._lock

    def clear(self):
        with self._lock:
            self._cache.clear()


cache = Cache.Instance()
