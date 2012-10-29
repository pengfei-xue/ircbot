# -*- coding: utf8 -*-
import re

from ircbots import IRCBot 
from settings import global_conf as gc
from addons import gitlab


class OupengBot(IRCBot):
    def __init__(self, nick):
        super(OupengBot, self).__init__(nick)

        self.capabilities = []
        self.gitlab_api = gitlab.GitLabApi(gc.gitlab['api_baseurl'], \
            gc.gitlab['private_token'])

        self.register_callbacks()

    def greet(self, nick, message, channel):
        return 'Hi, %s' % nick

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
            self.ping('^help', self.help),
            self.ping('^git projects', self.get_gitlab_projects),
        )

    def register_callbacks(self):
        """
        Hook for registering callbacks with connection -- handled by __init__()
        """
        for pattern, callback in self.command_patterns():
            super(OupengBot, self).register_callbacks([(re.compile(pattern), callback), ])
            self.capabilities.append(re.sub('.*(\*+)', '', pattern))
    
    def _ping_decorator(self, func):
        def inner(nick, message, channel, **kwargs):
            message = re.sub('^%s[:,\s]\s*' % self.nick, '', message)
            return func(nick, message, channel, **kwargs)
        return inner
    
    def ping(self, pattern, callback):
        return (
            '^%s[:,\s]\s*%s' % (self.nick, pattern.lstrip('^')),
            self._ping_decorator(callback),
        )
    
    def get_capabilities(self):
        return self.capabilities

if '__main__' == __name__:
    bot = OupengBot(gc.irc['nickname'])
    bot.connect_ircserver(gc.irc['server'], gc.irc['port'])
    bot.join_channel(gc.irc['channel'])
