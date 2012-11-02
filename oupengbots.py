# -*- coding: utf8 -*-
import re

from ircbots import IRCBot 
from settings import global_conf as gc
from addons import gitlab


class OupengBot(IRCBot):
    def __init__(self, nick):
        super(OupengBot, self).__init__(nick)

        self.gitlab_api = gitlab.GitLabApi(gc.gitlab['api_baseurl'],
            gc.gitlab['private_token'])

        self.register_order(
            (re.compile(r'^\s*git projects\s*$'), self.get_gitlab_projects, 
            'Get all git projects: git projects'
            ),
        )

    def get_gitlab_projects(self):
        msg = []

        projects = self.gitlab_api.get_projects()
        for proj in projects.json:
            _msg = 'project name: %s, id: %s, owner: %s' % (proj['name'],
                proj['id'], proj['owner']['name'])
            msg.append(_msg)

        return msg

    

if '__main__' == __name__:
    bot = OupengBot(gc.irc['nickname'])
    bot.connect_ircserver(gc.irc['server'], gc.irc['port'])
    bot.join_channel(gc.irc['channel'])
