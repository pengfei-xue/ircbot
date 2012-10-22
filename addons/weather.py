#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import httplib2

class InvalidCityCodeException(Exception):
    ''' invalid city code exception '''


class CityCode(object):
    valid_code = {
        101010300: 1, #朝阳
    }

    def __init__(self, city_code):
        self.city_code = city_code

        # make sure city code is valid when creating CityCode
        if not self.is_city_code_valid():
            raise InvalidCityCodeException('City code is invalid')

    def is_city_code_valid(self):
        if self.valid_code.get(self.city_code, 0):
            return True

    # we can make sure that city code is valid
    def get_url(self):
        return "http://www.weather.com.cn/data/sk/%s.html" % self.city_code


# get current weather info by city code
def get_weather_json(city_code):
    vcd = CityCode(city_code)

    httpAgent =  httplib2.Http()
    url = vcd.get_url()
    response, content = httpAgent.request(url, 'GET')

    if not response.status == 200:
        print "Please try it again later"

    content_json = json.loads(content)['weatherinfo']

    return content_json

if __name__ == '__main__':
    # Chaoyang district, Beijing, CN
    chaoyang = 101010300
    
    print get_weather_json(chaoyang)
