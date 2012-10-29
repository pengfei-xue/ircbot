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
    '''
        api wrapper for gitlab:
        https://github.com/gitlabhq/gitlabhq/tree/master/doc/api
    '''
    def __init__(self, api_baseurl, private_token):
        self.private_token = private_token
        self.api_baseurl = api_baseurl
    
    # NOTE: project apis #
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

    # NOTE : repository apis #
    def get_project_branches(self, id):
        '''
            Get a list of repository branches from a project, 
            sorted by name alphabetically.
            api: GET /projects/:id/repository/branches
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s/repository/branches' % id)
        return res

    def get_project_single_branch(self, id, branch):
        '''
            Get a single project repository branch.
            api: GET /projects/:id/repository/branches/:branch
            parameters: 
                id (required) - The ID or code name of a project
                branch (required) - The name of the branch
        '''
        res = self.call('projects/%s/repository/branches/%s' % (id, branch))
        return res

    def get_project_tags(self, id):
        '''
            Get a list of repository tags from a project, 
            sorted by name in reverse alphabetical order.
            api: GET /projects/:id/repository/tags
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s/repository/tags' % id)
        return res

    def get_project_commits(self, id, ref_name):
        '''
            Get a list of repository commits in a project.
            api: GET /projects/:id/repository/commits
            parameters: 
                id (required) - The ID or code name of a project
                ref_name (optional) - The name of a repository branch or tag
        '''
        res = self.call('projects/%s/repository/commits' % id)
        return res

    def get_raw_blob_content(self, id, sha, filepath):
        '''
            Get the raw file contents for a file. 
            api: GET /projects/:id/repository/commits/:sha/blob
            parameters:
                id (required) - The ID or code name of a project
                sha (required) - The commit or branch name
                filepath (required) - The path the file
        '''
        res = self.call('projects/%s/repository/commits/%s/blob' % (id, sha))
        return res

    # NOTE : users related apis #
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
