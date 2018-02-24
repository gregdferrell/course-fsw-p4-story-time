#
# Story Time App
# Main flask app configuration and website route definitions
#

import datetime
import json
import random
import string

import httplib2
import requests
from flask import Flask, flash, jsonify, make_response, redirect, render_template, request, \
    session as login_session, url_for
from flask_uploads import IMAGES, UploadSet, configure_uploads
from oauth2client.client import FlowExchangeError, OAuth2Credentials, flow_from_clientsecrets
from werkzeug.exceptions import Forbidden, HTTPException, NotFound, Unauthorized, default_exceptions

from storytime import story_time_service
from storytime.sec_util import AuthProvider, LoginSessionKeys, do_authorization, is_user_authenticated, login_required, \
    reset_user_session, store_user_session
from storytime.story_time_db_init import Story, User
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

# Setup File Handling with Flask & Flask-Uploads
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024  # 512 KB
app.config['UPLOADED_PHOTOS_DEST'] = 'static/upload/img'
upload_set_photos = UploadSet('photos', IMAGES)
configure_uploads(app, upload_set_photos)


# Configure Template Filters
@app.template_filter('format_date')
def format_date(date: datetime):
    return date.strftime('%B %d, %Y')


# Configure Global Exception Handling for website and API
def handle_exception(exc):
    """
    Global exception handler for exceptions raised from website and API.
    :param exc: the exception being raised
    :return: the response which is either 1) a rendered HTML template or 2) a JSON response
    in the case of a call to the API
    """
    code = 500
    message = 'An unexpected error occurred while processing your request.'
    url = request.url

    if isinstance(exc, HTTPException):
        code = exc.code
        message = exc.description

    # Return JSON if they were trying to access the api
    if request.path.startswith('/api'):
        message = {
            'status': code,
            'message': message,
            'url': url
        }

        return jsonify(message), code

    return render_template('error.html', error_code=code, error_message=message), code


# Register handle_exception with all error handlers
for exc in default_exceptions:
    app.register_error_handler(exc, handle_exception)


# WEBSITE ROUTE DEFINITIONS
@app.route('/', methods=['GET'])
def index():
    stories_count = story_time_service.get_published_stories_count()
    stories = story_time_service.get_published_stories(count=12)
    return render_template('index.html', stories=stories, stories_count=stories_count)


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
        raise Forbidden

    # 2. Validate state token
    if request.args.get('state') != login_session.get(LoginSessionKeys.STATE.value):
        raise Unauthorized

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
    stored_credentials = None if not stored_credentials_json else OAuth2Credentials.from_json(stored_credentials_json)
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


@app.route('/stories/create', methods=['GET'])
@login_required
def get_create_story_page():
    categories = story_time_service.get_categories()
    return render_template('create_story.html', categories=categories)


@app.route('/stories/<int:story_id>/edit', methods=['GET'])
@login_required
def get_edit_story_page(story_id):
    story = story_time_service.get_story_by_id(story_id)

    # Resource check - 404
    if not story:
        raise NotFound

    # Auth check - 401
    do_authorization(story.user_id)

    if story:
        categories = story_time_service.get_categories()
        return render_template('edit_story.html', story=story, categories=categories)
    else:
        return redirect(url_for('user_dashboard'))


@app.route('/stories/<int:story_id>/delete', methods=['POST'])
def delete_story(story_id):
    story = story_time_service.get_story_by_id(story_id=story_id)

    # Resource check - 404
    if not story:
        raise NotFound

    # Auth check - 401
    do_authorization(story.user_id)

    # Delete story and file
    story_time_service.delete_story(story.id)

    success_message = 'Successfully deleted story "{}".'.format(story.title)
    flash(success_message, 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/stories/<int:story_id>', methods=['GET'])
def view_story(story_id):
    story = story_time_service.get_story_by_id(story_id=story_id)

    # Resource check - 404
    if not story:
        raise NotFound

    story_text_paragraphs = story.story_text.splitlines()
    return render_template('view_story.html', story=story, story_text_paragraphs=story_text_paragraphs)


@app.route('/stories/random', methods=['GET'])
def view_story_random():
    story = story_time_service.get_story_random()
    return redirect(url_for('view_story', story_id=story.id))


@app.route('/stories/create', methods=['POST'])
@login_required
def create_story():
    # Get story categories from form input
    category_ids = request.form.getlist('categories', type=int)
    categories = story_time_service.get_categories_by_ids(category_ids=category_ids)

    # Create story object from form input
    story = Story(title=request.form.get('title', None),
                  description=request.form.get('description', None),
                  story_text=request.form.get('text', None),
                  published=bool(request.form.get('published')),
                  categories=categories,
                  user_id=login_session[LoginSessionKeys.USER_ID.value])

    # Validate required fields
    if not (story.title, story.description, story.story_text):
        error_message = 'You must specify the title, description and text for your story.'
        flash(error_message, 'danger')
        return redirect(url_for('get_create_story_page'))

    # Get the attached file if present
    file = None
    if 'story-thumbnail' in request.files:
        if request.files.get('story-thumbnail').filename:
            file = request.files['story-thumbnail']

    # Save Story and file
    story_time_service.create_story(story=story, image_file=file)

    # Render view
    success_message = 'Created {} successfully.'.format(story.title)
    flash(success_message, 'success')
    return redirect(url_for('view_story', story_id=story.id))


@app.route('/stories/<int:story_id>/edit', methods=['POST'])
@login_required
def edit_story(story_id):
    raise ValueError

    story = story_time_service.get_story_by_id(story_id)

    # Resource check - 404
    if not story:
        raise NotFound

    # Auth check - 401
    do_authorization(story.user_id)

    # Get the attached file if present
    file = None
    if 'story-thumbnail' in request.files:
        if request.files.get('story-thumbnail').filename:
            file = request.files['story-thumbnail']

    # Get remove existing image flag from form input or existence of new file
    remove_existing_image = bool(request.form.get('remove-existing-thumbnail')) or bool(file)

    # Update Story object from form input
    story.title = request.form.get('title', story.title)
    story.description = request.form.get('description', story.description)
    story.story_text = request.form.get('text', story.story_text)
    category_ids = request.form.getlist('categories', type=int)
    story.categories = story_time_service.get_categories_by_ids(category_ids=category_ids)
    story.published = bool(request.form.get('published'))

    # Validate required fields
    if not (story.title, story.description, story.story_text):
        error_message = 'You must specify the title, description and text for your story!'
        flash(error_message, 'danger')
        return redirect(url_for('get_edit_story_page'))

    # Save Story and File
    story_time_service.update_story(story=story, remove_existing_image=remove_existing_image, new_image_file=file)

    # Render View
    success_message = 'Updated {} successfully.'.format(story.title)
    flash(success_message, 'success')
    return redirect(url_for('view_story', story_id=story_id))


# -------------------- MAIN
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.jinja_env.auto_reload = True
    app.run(host='localhost', port=8000)
