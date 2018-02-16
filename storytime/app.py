#
# Story Time App
# Main flask app
#

import datetime
import json
import random
import string

import httplib2
import requests
from flask import Flask, abort, flash, make_response, redirect, render_template, request, session as login_session, \
    url_for
from oauth2client.client import FlowExchangeError, OAuth2Credentials, flow_from_clientsecrets

from storytime import story_time_service
from storytime.exceptions import AppException, AppExceptionNotFound
from storytime.sec_util import AuthProvider, LoginSessionKeys, is_user_authenticated, login_required, \
    reset_user_session, store_user_session
from storytime.story_time_db_init import User
from storytime.web_api import web_api

# Auth
GOOGLE_CLIENT_SECRETS_JSON = 'config/client_secrets_google.json'
GOOGLE_CLIENT_ID = json.loads(open(GOOGLE_CLIENT_SECRETS_JSON, 'r').read())['web']['client_id']
FACEBOOK_CLIENT_SECRETS_JSON = 'config/client_secrets_facebook.json'
FACEBOOK_APP_ID = json.loads(open(FACEBOOK_CLIENT_SECRETS_JSON, 'r').read())['web']['app_id']
FACEBOOK_APP_SECRET = json.loads(open(FACEBOOK_CLIENT_SECRETS_JSON, 'r').read())['web']['app_secret']

# Setup Flask App
app = Flask(__name__)
app.url_map.strict_slashes = False
app.register_blueprint(web_api)


@app.template_filter('format_date')
def format_date(date: datetime):
    return date.strftime('%B %d, %Y')


# @app.errorhandler(Exception)
def handle_exception(e):
    # Set default code and message
    code = 500
    message = "An unexpected error has occurred on the server. Please wait a short time, then try again."

    print('Caught exception: ' + str(e))
    print(e.st)

    if isinstance(e, AppException):
        # Extract code and message from AppException, if present
        if e.code and e.message:
            code = e.code
            message = e.message
        elif isinstance(e, AppExceptionNotFound):
            code = 404
            message = "The resource you're looking for can't be found."

    return render_template('error.html', error_code=code, error_message=message), code


@app.route('/', methods=['GET'])
def index():
    category_id = request.args.get('category')
    if category_id:
        stories = story_time_service.get_stories_by_category_id(category_id=category_id)
    else:
        stories = story_time_service.get_stories()
    return render_template('index.html', stories=stories)


@app.route('/login', methods=['GET'])
def login():
    # Create a state token to prevent request forgery.
    # Store it in the session for later verification
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session[LoginSessionKeys.STATE.value] = state
    return render_template('login.html', state=state)


@app.route('/login-google', methods=['POST'])
def login_google():
    # Two checks against CSRF
    # 1. If header `X-Requested-With` not present, this could be a CSRF
    if not request.headers.get('X-Requested-With'):
        abort(403)

    # 2. Validate state token
    if request.args.get('state') != login_session.get(LoginSessionKeys.STATE.value):
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain one-time-use authorization code
    one_time_auth_code = request.data

    # Upgrade the authorization code into a credentials object
    try:
        oauth_flow = flow_from_clientsecrets(GOOGLE_CLIENT_SECRETS_JSON, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(one_time_auth_code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token''s user ID doesn''t match given user ID.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != GOOGLE_CLIENT_ID:
        response = make_response(json.dumps('Token''s client ID does not match app''s'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if a user is already logged in
    stored_credentials_json = login_session.get(LoginSessionKeys.GOOGLE_CREDENTIALS_JSON.value)
    stored_credentials = None if not stored_credentials_json else OAuth2Credentials.from_json(
        stored_credentials_json)
    stored_gplus_id = login_session.get(LoginSessionKeys.GOOGLE_ID.value)

    if stored_credentials is not None:
        if gplus_id == stored_gplus_id:
            # If the user is already logged in
            response = make_response(json.dumps('Current user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response
        else:
            # TODO Test this scenario
            # If a new user is logging in before the previous user logged out,
            # then reset the session before creating a new one
            reset_user_session()

    # Get user info
    user_info_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(user_info_url, params=params)

    data = json.loads(answer.text)
    username = data['name']
    email = data['email']
    picture = data['picture']

    # Store user_id in session by saving new user or getting id if existing
    user_id = story_time_service.get_user_id_by_email(email)
    if not user_id:
        user_id = story_time_service.create_user(User(name=username, email=email, active=True))

    # Store the session information
    store_user_session(user_id=user_id, username=username, email=email, picture=picture, provider=AuthProvider.GOOGLE,
                       google_credentials_json=credentials.to_json(), google_id=gplus_id)

    return 'Login successful'


@app.route('/login-facebook', methods=['POST'])
def login_facebook():
    # Validate state token
    if request.args.get('state') != login_session[LoginSessionKeys.STATE.value]:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain one-time-use authorization code
    one_time_auth_code = request.get_data(as_text=True)

    # Exchange client token for long lived server side token
    url = 'https://graph.facebook.com/v2.12/oauth/access_token?grant_type=fb_exchange_token&client_id={}&client_secret={}&fb_exchange_token={}'.format(
        FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, one_time_auth_code)

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    token_json = json.loads(result)
    token = token_json['access_token']

    url = 'https://graph.facebook.com/v2.12/me?access_token={}&fields=name,email,id'.format(token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data_me = json.loads(result)

    # Get user picture
    url = 'https://graph.facebook.com/v2.12/me/picture?access_token={}&redirect=0&height=200&width=200'.format(token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data_picture = json.loads(result)

    facebook_id = data_me['id']
    username = data_me['name']
    email = data_me['email']
    picture = data_picture['data']['url']

    # Store user_id in session by saving new user or getting id if existing
    user_id = story_time_service.get_user_id_by_email(email)
    if not user_id:
        user_id = story_time_service.create_user(User(name=username, email=email, active=True))

    # Store the session information
    store_user_session(user_id=user_id, username=username, email=email, picture=picture, provider=AuthProvider.FACEBOOK,
                       facebook_id=facebook_id)

    return 'Login successful'


@app.route('/logout')
def logout():
    # Redirect to index if user not logged in
    if not is_user_authenticated():
        return redirect(url_for('index'))

    auth_provider = login_session.get(LoginSessionKeys.PROVIDER.value)

    if auth_provider == AuthProvider.GOOGLE.value:
        # Get oauth2 credentials and only disconnect a connected user
        credentials = OAuth2Credentials.from_json(login_session.get(LoginSessionKeys.GOOGLE_CREDENTIALS_JSON.value))

        # Tell Google to revoke current token
        access_token = credentials.access_token
        url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(access_token)
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]

        if result['status'] != '200':
            # For whatever reason, the given token was invalid
            print('google revoke token failed; received {}'.format(result['status']))
    elif auth_provider == AuthProvider.FACEBOOK.value:
        # Tell FB to reject access token
        facebook_id = login_session[LoginSessionKeys.FACEBOOK_ID.value]
        url = 'https://graph.facebook.com/{}/permissions'.format(facebook_id)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]

    # Reset the user's session
    reset_user_session()
    flash('You have logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET'])
@login_required
def user_dashboard():
    stories = story_time_service.get_stories_by_user_id(login_session[LoginSessionKeys.USER_ID.value])
    return render_template('user_dashboard.html', stories=stories,
                           username=login_session.get(LoginSessionKeys.USERNAME.value),
                           email=login_session.get(LoginSessionKeys.EMAIL.value),
                           picture=login_session.get(LoginSessionKeys.PICTURE.value))


@app.route('/stories/<int:story_id>', methods=['GET'])
def view_story(story_id):
    story = story_time_service.get_story_by_id(story_id=story_id)
    story_text_paragraphs = story.story_text.splitlines()

    # Resource check - 404
    if not story:
        raise AppExceptionNotFound

    return render_template('view_story.html', story=story, story_text_paragraphs=story_text_paragraphs)


@app.route('/stories/random', methods=['GET'])
def view_story_random():
    story = story_time_service.get_story_random()
    return redirect(url_for('view_story', story_id=story.id))


# -------------------- MAIN
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.jinja_env.auto_reload = True
    app.run(host='localhost', port=8000)
    # app.run(host='0.0.0.0', port=8000) # Use to make available on network
