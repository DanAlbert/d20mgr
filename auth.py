"""Wrappers for authentication and authorization system.

Author: Dan Albert <dan@gingerhq.net>

Wrappers are used for authorization and authentication code in case we need to
introduce a different mechanism in the future.
"""
from google.appengine.api import users

def current_user():
    """Returns the User object for the signed in user or None."""
    return users.get_current_user()

def user_is_admin():
    """Returns True if the current user is an administrator."""
    return users.is_current_user_admin()

def logged_in():
    """Returns true if a user is currently logged in."""
    return current_user() is not None

def login_logout(request):
    """Generates text and a URL for a login/logout link.

    If a user is currently logged in, this returns a logout string and URL. If
    no user is logged in, this returns a login string and URL.

    Returns: a tuple of the form (text, URL)
    """
    if logged_in():
        url = users.create_logout_url(request.uri)
        text = 'Logout'
    else:
        url = users.create_login_url(request.uri)
        text = 'Login'

    return (text, url)

def user_from_email(email):
    return users.User(email=email)
