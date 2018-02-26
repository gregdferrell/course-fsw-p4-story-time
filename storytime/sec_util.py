#
# Story Time App
# Auth & Session helper methods
#

from enum import Enum
from functools import wraps
from urllib.parse import urlparse

from flask import request, session as login_session
from werkzeug.exceptions import Forbidden, Unauthorized


class AuthProvider(Enum):
    """
    Enum representing authentication providers.
    """
    GOOGLE = 1
    FACEBOOK = 2


class LoginSessionKeys(Enum):
    """
    Enum representing the keys for session variables.
    """
    CSRF_TOKEN = 'csrf_token'
    USER_ID = 'user_id'
    USERNAME = 'username'
    EMAIL = 'email'
    PICTURE = 'picture'
    PROVIDER = 'provider'
    GOOGLE_CREDENTIALS_JSON = 'google_credentials_json'
    GOOGLE_ID = 'google_id'
    FACEBOOK_ID = 'facebook_id'


def store_user_session(user_id: int, username: str, email: str, picture: str, provider: AuthProvider,
                       google_credentials_json=None, google_id: int = None, facebook_id: int = None):
    """
    Stores a user session by adding each of the given parameters to the session.
    :param user_id: the (SecUser) user id of the logged in user
    :param username: the username of the logged in user (from the authentication provider)
    :param email: the email of the logged in user
    :param picture: the url to a photo of the logged in user
    :param provider: the authentication provider type
    :param google_credentials_json: the google json credentials object for the user
    :param google_id: the google id for the user
    :param facebook_id: the facebook id for the user
    :return:
    """
    # Validation
    if provider == AuthProvider.GOOGLE:
        if google_credentials_json is None or google_id is None:
            raise ValueError('google_credentials_json and google_id must be provided with Google auth provider')
    elif provider == AuthProvider.FACEBOOK:
        if facebook_id is None:
            raise ValueError('facebook_id must be provided with Facebook auth provider')

    # Save
    login_session[LoginSessionKeys.USER_ID.value] = user_id
    login_session[LoginSessionKeys.USERNAME.value] = username
    login_session[LoginSessionKeys.EMAIL.value] = email
    login_session[LoginSessionKeys.PICTURE.value] = picture
    login_session[LoginSessionKeys.PROVIDER.value] = provider.value
    login_session[LoginSessionKeys.GOOGLE_CREDENTIALS_JSON.value] = google_credentials_json
    login_session[LoginSessionKeys.GOOGLE_ID.value] = google_id
    login_session[LoginSessionKeys.FACEBOOK_ID.value] = facebook_id


def reset_user_session():
    """
    Reset the current session by removing the session variables from the session.
    """
    login_session.pop(LoginSessionKeys.USER_ID.value, None)
    login_session.pop(LoginSessionKeys.USERNAME.value, None)
    login_session.pop(LoginSessionKeys.EMAIL.value, None)
    login_session.pop(LoginSessionKeys.PICTURE.value, None)
    login_session.pop(LoginSessionKeys.PROVIDER.value, None)
    login_session.pop(LoginSessionKeys.GOOGLE_CREDENTIALS_JSON.value, None)
    login_session.pop(LoginSessionKeys.GOOGLE_ID.value, None)
    login_session.pop(LoginSessionKeys.FACEBOOK_ID.value, None)


def is_user_authenticated():
    """
    Checks to see if the user is authenticated by looking for a user_id in the login_session.
    :return: a boolean indicating if the user is authenticated
    """
    return LoginSessionKeys.USER_ID.value in login_session


def do_authorization(valid_user_id=0):
    """
    Checks to see if the user is authenticated and optionally checks to see if the user id in the session
    matches the user id passed in. Raises Unauthorized if any of the checks do not pass.
    :param valid_user_id: the user id to look for in the session
    :return:
    """
    if not is_user_authenticated():
        raise Unauthorized
    if valid_user_id > 0 and valid_user_id != login_session[LoginSessionKeys.USER_ID.value]:
        raise Unauthorized


def login_required(func):
    """
    Decorator for app.route functions to require a valid login session in order to proceed. Raises Unauthorized
    error if the user is not authenticated.
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        do_authorization()
        return func(*args, **kwargs)

    return decorated_function


def csrf_protect(xhr_only: bool = False):
    """
    Decorator for app.route functions to add CSRF protection to them. Raises Forbidden error if any of the
    checks do not pass.
    :param xhr_only: true if we want to enforce that this request be an XMLHttpRequest
    """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            # Check if this function should only accept XHR
            if xhr_only and not request.is_xhr:
                raise Forbidden

            # Check for presence of `X-Requested-With` header in all XHR
            if request.is_xhr and not request.headers.get('X-Requested-With'):
                raise Forbidden

            # Confirm that the origin/referer matches the requested URL
            if request.headers['origin']:
                if not request.url.startswith(request.headers['origin']):
                    raise Forbidden
            elif request.headers['referer']:
                parsed_uri = urlparse(request.headers['referer'])
                referer_domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                if not request.url.startswith(referer_domain):
                    raise Forbidden
            else:
                # Either Origin or Referer header must be present to proceed
                raise Forbidden

            # Validate state token
            if request.values.get('csrf-token') != login_session.get(LoginSessionKeys.CSRF_TOKEN.value):
                raise Forbidden

            return func(*args, **kwargs)

        return decorated_function

    return decorator
