#
# Story Time App
# Auth & Session helper methods
#

from enum import Enum
from functools import wraps

from flask import abort, session as login_session


class AuthProvider(Enum):
    GOOGLE = 1
    FACEBOOK = 2


class LoginSessionKeys(Enum):
    STATE = 'state'
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
    login_session.pop(LoginSessionKeys.USER_ID.value, None)
    login_session.pop(LoginSessionKeys.USERNAME.value, None)
    login_session.pop(LoginSessionKeys.EMAIL.value, None)
    login_session.pop(LoginSessionKeys.PICTURE.value, None)
    login_session.pop(LoginSessionKeys.PROVIDER.value, None)
    login_session.pop(LoginSessionKeys.GOOGLE_CREDENTIALS_JSON.value, None)
    login_session.pop(LoginSessionKeys.GOOGLE_ID.value, None)
    login_session.pop(LoginSessionKeys.FACEBOOK_ID.value, None)


def is_user_authenticated():
    return LoginSessionKeys.USER_ID.value in login_session


def do_authorization(valid_user_id=0):
    if not is_user_authenticated():
        abort(401)
    if valid_user_id > 0 and valid_user_id != login_session[LoginSessionKeys.USER_ID.value]:
        abort(401)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        do_authorization()
        return func(*args, **kwargs)

    return wrapper
