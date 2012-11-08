# -*- coding: utf8 -*-

import time

class Cacher(object):
    def __init__(self, expired=3600):
        self._cached_data = {}
        self.expired = expired

    def get(self, key):
        if key not in self._cached_data:
            return None

        now = time.time()
        old_ts = self._cached_data[key]['timestamp']

        if now - old_ts >= self.expired:
            return None
        
        cached_value = self._cached_data[key]['value']
        return cached_value

    def set(self, key, value):
        self._cached_data[key] = {}
        self._cached_data[key]['value'] = value
        self._cached_data[key]['timestamp'] = time.time()

    def refresh(self):
        self._cached_data = {}

    def retire(self, key):
        self._cached_data[key] = dict.fromkeys(['value', 'timestamp'])
