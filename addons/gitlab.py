# -*- coding: utf8 -*-

import requests

def raiseExceptionOn401(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if not res.ok and res.status_code == 401:
            raise UnauthorizeException('401 Unauthorized')
        return res
    return wrapper

class UnauthorizeException(BaseException):
    ''' 
        If no, or an invalid, private_token is provided then an 
        error message will be returned with status code 401:
        {"message":"401 Unauthorized"} 
    '''
    pass

class GitLabApi(object):
    def __init__(self, api_baseurl, private_token):
        self.private_token = private_token
        self.api_baseurl = api_baseurl
    
    def get_projects(self):
        '''
            Get a list of projects owned by the authenticated user.
            api: GET /projects
        '''
        res = self.call('projects')
        return res

    def get_single_project(self, id):
        '''
            Get a specific project, identified by project ID, 
            which is owned by the authentication user.
            api: GET /projects/:id 
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s' % id)
        return res

    def get_project_members(self, id):
        '''
            Get a list of project team members.
            api: GET /projects/:id/members
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s/members' % id)

    def about_me(self):
        '''       
            Get currently authenticated user. 
            api: GET /user
        '''
        res = self.call('user')
        return res

    def get_users(self):
        '''
            Get a list of users.
            api: GET /users
        '''
        res = self.call('users')

    def get_single_user(self, id):
        ''' 
            Get a single user
            api: GET /users/:id 
            parameters: id (required) - The ID of a user
        '''
        res = self.call('users/%s' % id)
        return res

    @raiseExceptionOn401
    def call(self, api_url, http_method='GET', **kwargs):
        res = None
        url = self.api_baseurl + api_url + '?private_token=' + self.private_token

        if http_method == 'GET':
            res = requests.get(url)

        elif http_method == 'POST':
            res = requests.post(url, data=kwargs['data'])

        else:
            result = 'Http Method' + http_method + ' unsupported'
            raise Exception(result)

        return res
