# -*- coding: utf8 -*-

import requests

def raiseExceptionOn40X(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if not res.ok:
            if res.status_code == 401:
                raise UnauthorizeException('401 Unauthorized')
            elif res.status_code == 404:
                raise NotFoundException('404 Not Found')
        return res
    return wrapper


class NotFoundException(BaseException):
    ''' {"message":"404 Not Found"} '''
    pass


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

    def get_single_project(self, project_id):
        '''
            Get a specific project, identified by project ID, 
            which is owned by the authentication user.
            api: GET /projects/:id 
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s' % project_id)
        return res

    def get_project_name_by_pid(self, project_id):
        project = self.get_single_project(project_id)

        return project.json['name']

    def get_project_members(self, project_id):
        '''
            Get a list of project team members.
            api: GET /projects/:id/members
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s/members' % project_id)

    # NOTE : repository apis #
    def get_project_branches(self, project_id):
        '''
            Get a list of repository branches from a project, 
            sorted by name alphabetically.
            api: GET /projects/:id/repository/branches
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s/repository/branches' % project_id)
        return res

    def get_project_single_branch(self, project_id, branch):
        '''
            Get a single project repository branch.
            api: GET /projects/:id/repository/branches/:branch
            parameters: 
                id (required) - The ID or code name of a project
                branch (required) - The name of the branch
        '''
        res = self.call('projects/%s/repository/branches/%s' % (project_id, branch))
        return res

    def get_project_tags(self, project_id):
        '''
            Get a list of repository tags from a project, 
            sorted by name in reverse alphabetical order.
            api: GET /projects/:id/repository/tags
            parameters: id (required) - The ID or code name of a project
        '''
        res = self.call('projects/%s/repository/tags' % project_id)
        return res

    def get_project_commits(self, project_id, ref_name=None):
        '''
            Get a list of repository commits in a project.
            api: GET /projects/:id/repository/commits
            parameters: 
                id (required) - The ID or code name of a project
                ref_name (optional) - The name of a repository branch or tag
        '''
        res = self.call('projects/%s/repository/commits' % project_id)
        return res

    def get_raw_blob_content(self, project_id, sha, filepath):
        '''
            Get the raw file contents for a file. 
            api: GET /projects/:id/repository/commits/:sha/blob
            parameters:
                id (required) - The ID or code name of a project
                sha (required) - The commit or branch name
                filepath (required) - The path the file
        '''
        res = self.call('projects/%s/repository/commits/%s/blob' % (project_id, sha))
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

    def get_single_user(self, uid):
        ''' 
            Get a single user
            api: GET /users/:id 
            parameters: id (required) - The ID of a user
        '''
        res = self.call('users/%s' % uid)
        return res

    @raiseExceptionOn40X
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
