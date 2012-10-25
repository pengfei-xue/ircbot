# -*- coding: utf8 -*-

# patches stdlib (including socket and ssl modules) 
# to cooperate with other greenlets
from gevent import monkey; monkey.patch_all()

from irc import IRCBot, run_bot, SimpleSerialize
from settings import global_conf as g
from addons import weather
from addons import gitlab


class OupengBot(IRCBot):
    def __init__(self, conn):
        super(OupengBot, self).__init__(conn)
        self.gitlab_api = gitlab.GitLabApi(g.gitlab['api_baseurl'], \
            g.gitlab['private_token'])

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

    def get_gitlab_projects(self, nick, message, channel):
        res = []

        projects = self.gitlab_api.get_projects()
        for proj in projects.json:
            res.append('project name: ' + proj['name'])
            res.append('owner email: ' + proj['owner']['email'])

        return res
    
    def command_patterns(self):
        return (
            self.ping('^hello', self.greet),
            self.ping('^weather', self.get_weather_chaoyang),
            self.ping('^help', self.help),
            self.ping('^git projects', self.get_gitlab_projects),
        )

server, port, nick, channel = (g.irc[value] \
    for value in ['server', 'port', 'nickname', 'channel'])

run_bot(OupengBot, server, port, nick, [channel])
