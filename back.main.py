"""Entry point for D20 Character Manager.

Author: Dan Albert <dan@gingerhq.net>
"""
import webapp2

import os

import auth
import settings

from messages import Messages 
from models import Group, Idea, Project, Submission

from google.appengine.ext.webapp import template


class RequestHandler(webapp2.RequestHandler):
    """Base request handler that handles site wide handling tasks."""
    def render(self, template_name, data={}):
        """Renders the template in the site wide manner.
        
        Retrieves the template data needed for the base template (login URL and
        text, user information, etc.) and merges it with the data passed to the
        method. Templates are retrieved from the template directory specified in
        the settings and appended with the suffix ".html"
        
        Arguments:
        template_name: the name of the template. this is the file name of the
                       template without the .html extension.

        data: a dictionary containing data to be passed to the template.
        """
        (login_text, login_url) = auth.login_logout(self.request)
        
        if auth.logged_in():
            data['user'] = auth.User(auth.current_user())

        data['admin'] = auth.user_is_admin()
        data['login_url'] = login_url
        data['login_text'] = login_text
        data['messages'] = Messages.get()
        
        path = os.path.join(settings.BASE_DIR, settings.TEMPLATE_DIR,
                        "%s.html" % template_name)
        
        return self.response.out.write(template.render(path, data))


class ProjectsHandler(RequestHandler):
    def get(self):
        return self.render('projects', { 'projects': Project.all() })

    def claim(self, key):
        user = auth.User(auth.current_user())
        group = user.group
        if group.owner.user_id() == auth.current_user().user_id():
            project = Project.get(key)
            group.project = project
            group.put()
            return self.redirect('/groups/%s' % group.key())
        else:
            Messages.add('You are not the owner of your group. Only the ' +
                         'owner of the group may select a project.')
            return self.redirect('/projects')

    def vote(self, key):
        if not auth.logged_in():
            return self.redirect('/projects')
        project = Project.get(key)
        if project.has_voted(auth.current_user()):
            project.remove_vote(auth.current_user())
            project.put()
        else:
            project.vote(auth.current_user())
            project.put()
        return self.redirect('/projects')

    def delete(self, key):
        if auth.user_is_admin():
            Project.get(key).delete()
        else:
            Messages.add('Only and administrator may delete projects. This ' +
                         'incident has been logged.')
        return self.redirect('/projects')


class IdeasHandler(RequestHandler):
    def get(self):
        return self.render('ideas', { 'ideas': Idea.all() })

    def post(self):
        name = self.request.get('name')
        description = self.request.get('description')
        Idea(name=name,
            description=description,
            author=auth.current_user()).put()
        return self.redirect('/ideas')

    def approve(self, key):
        if auth.user_is_admin():
            idea = Idea.get(key)
            Project(name=idea.name,
                    description=idea.description,
                    author=idea.author,
                    post_time=idea.post_time).put()
            idea.delete()
            return self.redirect('/projects')
        else:
            Messages.add('Only and administrator may approve submitted ' +
                         'ideas. This incident has been logged.')
            return self.redirect('/ideas')

    def delete(self, key):
        if auth.user_is_admin():
            Idea.get(key).delete()
        else:
            Messages.add('Only and administrator may delete submitted ideas. ' +
                         'This incident has been logged.')
        return self.redirect('/ideas')


class GroupsHandler(RequestHandler):
    def get(self):
        return self.render('groups_list', { 'groups': Group.all() })

    def show(self, key):
        if self.request.method == 'GET':
            return self.render('groups_show', { 'group': Group.get(key)})
        elif self.request.method == 'POST':
            self.update_group(key)
        else:
            return self.abort(405)  # all other methods not allowed
    
    def join(self, key):
        group = Group.get(key)
        user = auth.User(auth.current_user())
        if user.in_group():
            Messages.add('You are already in a group')
            return self.redirect('/groups/%s' % key)
        if user.pending_join():
            Messages.add('You have already applied to join a group')
            return self.redirect('/groups/%s' % key)
        if group.public:
            group.members.append(auth.current_user())
            Messages.add('You have joined the group')
        else:
            group.pending_users.append(auth.current_user())
            Messages.add('You have requested to join the group')
        group.put()
        return self.redirect('/groups/%s' % key)
    
    def leave(self, key):
        group = Group.get(key)
        user = auth.User(auth.current_user())
        
        if user.group != group:
            Messages.add('You cannot leave a group you are not in')
            return self.redirect('/groups/%s' % key)
        
        group.members.remove(user.gae_user)
        group.put()
        return self.redirect('/groups')

    def signup(self):
        user = auth.User(auth.current_user())
        if user.in_group():
            Messages.add('You are already in a group')
            return self.redirect('/groups')
        else:
            return self.render('groups_signup')

    def create(self):
        """Handles the POST data for creating a group.

        Form Variables:
            name:   the name of the new group
            public: true if the group should be joinable by the public
        """
        if auth.logged_in():
            name = self.request.get('name')
            public = self.request.get('public') == 'public'
            owner = auth.current_user()
            
            if Group.exists(name):
                Messages.add('A group with that name already exists')
                return self.redirect('/groups/signup')
            
            Group(name=name,
                  public=public,
                  owner=owner,
                  members=[owner]).put()

            return self.redirect('/groups')
        else:
            Messages.add('You must be logged in to create a group')
            return self.redirect('/groups/signup')
    
    def edit(self, key):
        if not auth.logged_in():
            return self.redirect('/groups')
        
        user = auth.current_user()
        group = Group.get(key)
        if group.owner.user_id() == user.user_id() or auth.user_is_admin():
            return self.render('groups_edit', { 'group': group })
        else:
            Messages.add('Only the owner of this group may edit it')
            return self.redirect('/groups/%s' % key)
    
    def delete(self, key):
        if auth.user_is_admin():
            Group.get(key).delete()
        else:
            Messages.add('Only an administrator may delete groups. This ' +
                         'incident has been logged.')
        return self.redirect('/groups')
    
    def update_group(self, key):
        if not auth.logged_in():
            return self.redirect('/groups')
        
        user = auth.current_user()
        group = Group.get(key)
        if group.owner.user_id() != user.user_id() and not auth.user_is_admin():
            Messages.add('Only the owner of the group owner may modify it')
            return self.redirect('/groups')
        
        name = self.request.get('name')
        public = self.request.get('public') == 'public'
        abandon = self.request.get('abandon-project')
        sub_text = self.request.get('submission-text')
        sub_url = self.request.get('submission-url')
        remove_submission = self.request.get_all('remove-submission')
        remove = self.request.get_all('remove')
        owner = self.request.get('owner')
        delete = self.request.get('delete')
        
        if delete:
            group.delete()
            return self.redirect('/groups')
        
        group.name = name
        group.public = public
        
        if abandon:
            group.project = None
        
        if sub_text and sub_url:
            Submission(text=sub_text, url=sub_url, group=group).put()

        for sub in Submission.get(remove_submission):
            sub.delete()

        pending  = list(group.pending_users)
        for user in pending:
            approve = self.request.get("approve-%s" % user)
            if approve == "approve":
                group.members.append(user)
                group.pending_users.remove(user)
            elif approve == "refuse":
                group.pending_users.remove(user)
        
        group.owner = auth.user_from_email(owner)
        
        for user in remove:
            if auth.user_from_email(user) == group.owner:
                Messages.add('Cannot remove the group owner')
                return self.redirect('/groups/%s/edit' % key)
            else:
                group.members.remove(auth.user_from_email(user))
        
        group.put()
        return self.redirect('/groups/%s' % key)


class LiveHandler(RequestHandler):
    def get(self):
        return self.render('live')


class AboutHandler(RequestHandler):
    def get(self):
        return self.render('about')


class FAQHandler(RequestHandler):
    def get(self):
        return self.render('faq')


app = webapp2.WSGIApplication([
    ('/', ProjectsHandler),
    ('/projects', ProjectsHandler),
    webapp2.Route(r'/projects/<key>/delete', name='projects_delete',
                  handler=ProjectsHandler, handler_method='delete'),
    webapp2.Route(r'/projects/<key>/vote', name='projects_vote',
                  handler=ProjectsHandler, handler_method='vote'),
    webapp2.Route(r'/projects/<key>/claim', name='projects_claim',
                  handler=ProjectsHandler, handler_method='claim'),
    ('/ideas', IdeasHandler),
    webapp2.Route(r'/ideas/<key>/approve', name='ideas_approve',
                  handler=IdeasHandler, handler_method='approve'),
    webapp2.Route(r'/ideas/<key>/delete', name='ideas_delete',
                  handler=IdeasHandler, handler_method='delete'),
    ('/groups', GroupsHandler),
    webapp2.Route(r'/groups/signup', name='groups_signup',
                  handler=GroupsHandler, handler_method='signup'),
    webapp2.Route(r'/groups/create', name='groups_create',
                  handler=GroupsHandler, handler_method='create',
                  methods=['POST']),
    webapp2.Route(r'/groups/<key>', name='groups_show',
                  handler=GroupsHandler, handler_method='show'),
    webapp2.Route(r'/groups/<key>/edit', name='groups_edit',
                  handler=GroupsHandler, handler_method='edit'),
    webapp2.Route(r'/groups/<key>/delete', name='groups_delete',
                  handler=GroupsHandler, handler_method='delete'),
    webapp2.Route(r'/groups/<key>/join', name='groups_join',
                  handler=GroupsHandler, handler_method='join'),
    webapp2.Route(r'/groups/<key>/leave', name='groups_leave',
                  handler=GroupsHandler, handler_method='leave'),
    ('/live', LiveHandler),
    ('/about', AboutHandler),
    ('/faq', FAQHandler),
], debug=True)
