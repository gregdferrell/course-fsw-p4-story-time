#
# Story Time App
# Web JSON API
#

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import NotFound

from storytime import story_time_service

web_api = Blueprint('web_api', __name__, template_folder='templates')


@web_api.route('/api/stories')
def api_stories():
    category_id = request.args.get('category')
    if category_id:
        stories = story_time_service.get_published_stories_by_category_id(category_id)
    else:
        stories = story_time_service.get_published_stories()
    return jsonify(Stories=[story.serialize for story in stories])


@web_api.route('/api/stories/<int:story_id>')
def api_story(story_id):
    story = story_time_service.get_story_by_id(story_id)
    if not story:
        raise NotFound

    return jsonify(Story=story.serialize)


@web_api.route('/api/categories')
def api_categories():
    categories = story_time_service.get_categories()
    return jsonify(Categories=[category.serialize for category in categories])


@web_api.route('/api/categories/<int:category_id>')
def api_category(category_id):
    category = story_time_service.get_category_by_id(category_id)
    if not category:
        raise NotFound

    return jsonify(Category=category.serialize)
