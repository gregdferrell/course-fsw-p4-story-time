#
# Story Time App
# Web JSON API
#

from flask import Blueprint, jsonify, request

from storytime import story_time_service
from storytime.exceptions import AppException, AppExceptionNotFound

web_api = Blueprint('web_api', __name__, template_folder='templates')


@web_api.errorhandler(Exception)
def handle_exception(e):
    # Set default code and message
    code = 500
    url = request.url
    message = "Server error."

    if isinstance(e, AppException):
        # Extract code and message from AppException, if present
        if e.code and e.message:
            code = e.code
            message = e.message
        elif isinstance(e, AppExceptionNotFound):
            code = 404
            message = "Resource not found."

    message = {
        'status': code,
        'message': message,
        'url': url
    }
    resp = jsonify(message)
    resp.status_code = code
    return resp


@web_api.route('/api/stories')
def api_stories():
    category_id = request.args.get('category')
    if category_id:
        stories = story_time_service.get_stories_by_category_id(category_id)
    else:
        stories = story_time_service.get_stories()
    return jsonify(Stories=[story.serialize for story in stories])


@web_api.route('/api/stories/<int:story_id>')
def api_story(story_id):
    story = story_time_service.get_story_by_id(story_id)
    if not story:
        raise AppExceptionNotFound

    return jsonify(Story=story.serialize)


@web_api.route('/api/categories')
def api_categories():
    categories = story_time_service.get_categories()
    return jsonify(Categories=[category.serialize for category in categories])


@web_api.route('/api/categories/<int:category_id>')
def api_category(category_id):
    category = story_time_service.get_category_by_id(category_id)
    if not category:
        raise AppExceptionNotFound

    return jsonify(Category=category.serialize)
