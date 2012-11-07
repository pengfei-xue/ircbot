# -*- coding: utf8 -*-
import re

from ircbots import IRCBot 
from settings import global_conf as gc
from addons import gitlab
from addons import cache


class OupengBot(IRCBot):
    def __init__(self, nick):
        super(OupengBot, self).__init__(nick)

        self.gitlab_api = gitlab.GitLabApi(gc.gitlab['api_baseurl'],
            gc.gitlab['private_token'])

        self.register_order([
            (re.compile(r'^\s*git projects\s*$'), self.get_gitlab_projects, 
            'Get all git projects: git projects'),

            (re.compile(r'^\s*project\s(?P<project_id>.*?)\scommit'), self.get_project_commit,
            'Get project\'s latest commit by project id: project 123 commit'),
        ])

        self.cache = cache.Cacher()
        self.init_projects_commits_cache()

    def get_gitlab_projects(self, raw=False):
        msg = []

        projects = self.gitlab_api.get_projects()
        if raw:
            return projects

        for proj in projects.json:
            _msg = 'project name: %s, id: %s, owner: %s' % (proj['name'],
                proj['id'], proj['owner']['name'])
            msg.append(_msg)

        return msg

    def get_project_commit(self, project_id):
        commits = self.gitlab_api.get_project_commits(project_id)
        latest_commit = commits.json[0]
        self.cache.set(project_id, commits.json[0])

        project_name = self.gitlab_api.get_project_name_by_pid(project_id)

        msg = 'project: %s, commiter: %s, message: %s' % (
            project_name, latest_commit['author_name'],
            latest_commit['title'])

        return msg

    def init_projects_commits_cache(self):
        projects = self.get_gitlab_projects(raw=True)
        
        for proj in projects.json:
            commits = self.gitlab_api.get_project_commits(proj['id'])
            # get the latest commit
            self.cache.set(proj['id'], commits.json[0])

    
if '__main__' == __name__:
    bot = OupengBot(gc.irc['nickname'])
    bot.connect_ircserver(gc.irc['server'], gc.irc['port'])
    bot.join_channel(gc.irc['channel'])
