# -*- coding: utf8 -*-

class Cacher(object):
    def __init__(self):
        self._cached_data = {}

    def get(self, key):
        cached_value = self._cached_data.get(key, None)
        return cached_value

    def set(self, key, value):
        self._cached_data[key] = value
