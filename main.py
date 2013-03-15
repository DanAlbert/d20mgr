"""Entry point for D20 Character Manager.

Author: Dan Albert <dan@gingerhq.net>
"""
import webapp2
from webapp2 import uri_for

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2

import json
import logging
import os
import urllib2

import auth
import settings

from messages import Messages 
from models import Character

jinja = jinja2.Environment(
            loader=jinja2.FileSystemLoader(settings.TEMPLATE_DIR))


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
        
        data['uri_for'] = webapp2.uri_for

        data['user'] = auth.current_user()
        data['admin'] = auth.user_is_admin()
        data['login_url'] = login_url
        data['login_text'] = login_text
        data['messages'] = Messages.get()
        
        template = jinja.get_template(template_name + '.html')
        return self.response.out.write(template.render(data))


class CharacterListHandler(RequestHandler):
    def get(self):
        chars_tmp = Character.query().fetch()
        characters = []
        for character in chars_tmp:
            if character.owner.user_id() == auth.current_user().user_id():
                characters.append(character)
        return self.render('character-list', {'characters': characters})


class CharacterHandler(RequestHandler):
    def get(self, key):
        if not auth.logged_in():
            return self.redirect(users.create_login_url(self.request.url))
        character = ndb.Key(urlsafe=key).get()
        if character.owner.user_id() != auth.current_user().user_id():
            return webapp2.abort(401)
        return self.render('character', {'character': character})

    def create(self):
        if not auth.logged_in():
            return self.redirect(users.create_login_url(self.request.url))
        character = Character(owner=auth.current_user())
        character.put()
        return self.redirect(uri_for('character',
                                     key=character.key.urlsafe()))

    def post(self, key):
        character = ndb.Key(urlsafe=key).get()
        if character.owner.user_id() != auth.current_user().user_id():
            return webapp2.abort(401)
        form = json.loads(self.request.get('form'))
        character.name = form['name']
        character.race = form['race']
        character.strength = int(form['str'])
        character.dexterity = int(form['dex'])
        character.constitution = int(form['con'])
        character.intelligence = int(form['int'])
        character.wisdom = int(form['wis'])
        character.charisma = int(form['cha'])

        try:
            if isinstance(form['class-name'], list):
                character.classes = dict(zip(form['class-name'],
                                             form['class-level']))
            else:
                character.classes = {form['class-name']: form['class-level']}
        except KeyError:
            pass

        character.put()

    def delete(self, key):
        key = ndb.Key(urlsafe=key)
        character = key.get()
        if character.owner.user_id() != auth.current_user().user_id():
            return webapp2.abort(401)
        key.delete()


class ApiListHandler(RequestHandler):
    def get(self):
        characters = Character.query().fetch()
        character_dicts = []
        for character in characters:
            if character.owner.user_id() == auth.current_user().user_id():
                character_dict = character.to_dict(exclude=['owner'])
                character_dict['key'] = character.key.urlsafe()
                character_dicts.append(character_dict)

        self.response.headers['Content-Type'] = 'text/json'
        self.response.out.write(json.dumps(character_dicts))

    def put(self):
        character = Character(owner=auth.current_user())
        character.put()
        self.response.out.write(json.dumps({'key': character.key.urlsafe()}))


class ApiHandler(RequestHandler):
    def get(self, key):
        character = ndb.Key(urlsafe=key).get()
        if character.owner.user_id() != auth.current_user().user_id():
            return webapp2.abort(401)
        character_dict = character.to_dict(exclude=['owner'])
        character_dict['key'] = character.key.urlsafe()
        self.response.headers['Content-Type'] = 'text/json'
        self.response.out.write(json.dumps(character_dict))

    def post(self, key):
        character = ndb.Key(urlsafe=key).get()
        if character.owner.user_id() != auth.current_user().user_id():
            return webapp2.abort(401)
        form = json.loads(self.request.get('form'))
        try:
            character.name = form['name']
        except KeyError:
            pass

        try:
            character.race = form['race']
        except KeyError:
            pass

        try:
            character.strength = int(form['str'])
        except KeyError:
            pass

        try:
            character.dexterity = int(form['dex'])
        except KeyError:
            pass

        try:
            character.constitution = int(form['con'])
        except KeyError:
            pass

        try:
            character.intelligence = int(form['int'])
        except KeyError:
            pass

        try:
            character.wisdom = int(form['wis'])
        except KeyError:
            pass

        try:
            character.charisma = int(form['cha'])
        except KeyError:
            pass

        try:
            if isinstance(form['class-name'], list):
                character.classes = dict(zip(form['class-name'],
                                             form['class-level']))
            else:
                character.classes = {form['class-name']: form['class-level']}
        except KeyError:
            pass

        character.put()

    def delete(self, key):
        key = ndb.Key(urlsafe=key)
        character = key.get()
        if character.owner.user_id() != auth.current_user().user_id():
            webapp2.abort(401)
        key.delete()


app = webapp2.WSGIApplication([
    ('/', CharacterListHandler),
    webapp2.Route(r'/character', name='character-list',
                  handler=CharacterListHandler),
    webapp2.Route(r'/character/create', name='character-create',
                  handler=CharacterHandler, handler_method='create'),
    webapp2.Route(r'/character/<key>', name='character',
                  handler=CharacterHandler, methods=['GET', 'POST', 'DELETE']),
    webapp2.Route(r'/api/character', name='api-character-list',
                  handler=ApiListHandler, methods=['GET', 'PUT']),
    webapp2.Route(r'/api/character/<key>', name='api-character',
                  handler=ApiHandler, methods=['GET', 'POST', 'DELETE']),
], debug=True)
