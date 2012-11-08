# -*- coding: utf8 -*-

import time
import unittest

class Cacher(object):
    def __init__(self, expired=3600):
        self._cached_data = {}
        self.expired = expired

    def get(self, key):
        if key not in self._cached_data:
            return None

        now = time.time()
        old_ts = self._cached_data[key]['timestamp']

        # after we retired a key, now - None will raise an Exception
        if old_ts and (now - old_ts >= self.expired):
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


class testCacher(unittest.TestCase):
    def setUp(self):
        """
            set up data used in the tests.
            setUp is called before each test function execution.
        """
        self.expire_time = 1
        self.cache = Cacher(self.expire_time)
        self.key = 'test'
        self.value = {1:2}

    def wait(self):
        time.sleep(self.expire_time+1)

    def testSet(self):
        self.cache.set(self.key, self.value)
        self.assertEqual(self.cache._cached_data[self.key]['value'],
            self.value)

    def testGet(self):
        self.cache.set(self.key, self.value)
        value = self.cache.get(self.key)
        self.assertEqual(value, self.value)

        invalid_key = 'iaminvalidkey'
        self.assertIsNone(self.cache.get(invalid_key))

    def testRefresh(self):
        self.cache.refresh()
        self.assertEqual(self.cache._cached_data, {})
        
    def testRetire(self):
        self.cache.set(self.key, self.value)
        self.cache.retire(self.key)
        self.assertIsNone(self.cache.get(self.key))


if __name__ == '__main__':
    unittest.main()
