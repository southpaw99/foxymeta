try:
    from urllib.parse import urlencode, urlparse, parse_qsl
except ImportError:
    from urllib import urlencode
    from urlparse import urlparse, parse_qsl
import hashlib
import inspect
import json
import os
import os.path
import sys
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin



ADDON_URL, ADDON_HANDLE, ADDON_QS = sys.argv[:3]


class Router(object):
    def __init__(self):
        self.paths = {}
        self.addon = xbmcaddon.Addon()
        self.id_ = self.addon.getAddonInfo('id')
        self.handle = int(ADDON_HANDLE)
        self.cache_dir = xbmc.translatePath(
            'special://temp/{}'.format(self.id_))
        try:
            os.makedirs(self.cache_dir)
        except os.error as e:
            pass
        # store cache on (funname, hash(args + sorted_kwargs))
        self._cache = {}
        self.cache_keys_updated = set()

    @staticmethod
    def cache_hash(*args, **kwargs):
        h_list = list(args)
        h_list.extend(sorted(kwargs.items()))
        return hashlib.md5(str(h_list)).hexdigest()

    def memcache(self, func):
        cache = {}
        def wrapper(*args, **kwargs):
            _hash = self.cache_hash(*args, **kwargs)
            cached = cache.get(_hash)
            if cached:
                return cached
            result = func(*args, **kwargs)
            cache[_hash] = result
            return result
        return wrapper

    def load_cache(self, name):
        cache_path = '{}/{}.json'.format(self.cache_dir, name)
        if os.path.isfile(cache_path):
            with open(cache_path, 'r') as cache_file:
                try:
                    self._cache[name] = json.load(cache_file)
                except:
                    return None
                else:
                    return True

    def write_cache(self, name):
        cache_path = '{}/{}.json'.format(self.cache_dir, name)
        with open(cache_path, 'w') as cache_file:
            json.dump(self._cache[name], cache_file)

    def cache_get(self, name, *args, **kwargs):
        if name not in self._cache:
            if not self.load_cache(name):
                return None
        _hash = self.cache_hash(*args, **kwargs)
        cached = self._cache[name].get(_hash)
        if cached:
            # Remove excaption handling for old format later
            try:
                expire, data = cached
            except ValueError:
                expire = 0
            if time.time() > expire:
                del self._cache[name][_hash]
                self.cache_keys_updated.add(name)
                return None
            return data
        return None

    def cache_set(self, name, val, ttl, *args, **kwargs):
        _hash = self.cache_hash(*args, **kwargs)
        expire = int(time.time() + ttl)
        self._cache.setdefault(name, dict())[_hash] = (expire, val)
        self.cache_keys_updated.add(name)

    def cache(self, ttl=86400):
        def outer(func):
            def wrapper(*args, **kwargs):
                cache_name = '{}.{}'.format(inspect.getmodule(func).__name__,
                                            func.__name__)
                cached = self.cache_get(cache_name, *args, **kwargs)
                if cached is None:
                    result = func(*args, **kwargs)
                    self.cache_set(cache_name, result, ttl, *args, **kwargs)
                    return result
                return cached
            return wrapper
        return outer

    def route(self, path):
        path = path.lstrip('/')
        if path in self.paths:
            raise ValueError('Route already definted')
        def wrapper(func):
            self.paths[path] = func
            return func
        return wrapper

    def run(self):
        full_path = ADDON_URL + ADDON_QS
        parsed = urlparse(full_path)
        path = parsed.path.lstrip('/')
        kwargs = dict(parse_qsl(parsed.query))
        kwargs.pop('reload', None)
        func = self.paths[path]
        func(**kwargs)
        for updated in self.cache_keys_updated:
            self.write_cache(updated)

    def build_url(self, func, **kwargs):
        inverted = {v: k for k, v in self.paths.items()}
        path = inverted[func]
        url = 'plugin://{}/{}'.format(self.id_, path)
        if kwargs:
            query = urlencode(kwargs)
            url += '?' + query
        return url

    def gui_dirlist(self, funcs_names, dirs=False, more=False):
        for func, name in funcs_names:
            xbmcplugin.addDirectoryItem(self.handle,
                                        self.build_url(func),
                                        xbmcgui.ListItem(name),
                                        dirs)
        if not more:
            xbmcplugin.endOfDirectory(router.handle)


router = Router()
