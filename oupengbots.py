# -*- coding: utf8 -*-

from irc import IRCBot, run_bot, SimpleSerialize
from addons import weather
from settings import global_conf as g


class OupengBot(IRCBot):
    def greet(self, nick, message, channel):
        return 'Hi, %s' % nick

    def get_weather_chaoyang(self, nick, message, channel):
        content_dict = {
            'city' : u'城市', 
            'temp' : u'温度',
            'WS'   : u'WS',
        }

        chaoyang = 101010300
        weather_json = weather.get_weather_json(chaoyang)
        weather_info = [(value.encode('utf8'), weather_json[key].encode('utf8')) \
             for key, value in content_dict.iteritems()]
        msg = ' '.join("%s: %s" % info for info in weather_info)

        return msg

    def help(self, nick, message, channel):
        res = []
        res.append('**** avaliable commands ****')
        res.extend(self.get_capabilities())
        res.append('**** End of help ****')

        return res
    
    def command_patterns(self):
        return (
            self.ping('^hello', self.greet),
            self.ping('^weather', self.get_weather_chaoyang),
            self.ping('^help', self.help),
        )

server, port, nick, channel = (g.irc[value] \
    for value in ['server', 'port', 'nickname', 'channel'])

run_bot(OupengBot, server, port, nick, [channel])
