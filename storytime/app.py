#
# Story Time App
# Main flask app
#
import datetime

from flask import Flask, abort, render_template, request

from storytime import story_time_service
from storytime.web_api import web_api

# Setup Flask App
app = Flask(__name__)
app.url_map.strict_slashes = False
app.register_blueprint(web_api)


@app.template_filter('format_date')
def format_date(date: datetime):
    return date.strftime('%B %d, %Y')


@app.route('/', methods=['GET'])
def index():
    category_id = request.args.get('category')
    if category_id:
        stories = story_time_service.get_stories_by_category_id(category_id=category_id)
    else:
        stories = story_time_service.get_stories()
    return render_template('index.html', stories=stories)


@app.route('/stories/<int:story_id>', methods=['GET'])
def view_story(story_id):
    story = story_time_service.get_story_by_id(story_id=story_id)

    # Resource check - 404
    if not story:
        abort(404)

    return render_template('view_story.html', story=story)


# -------------------- MAIN
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.jinja_env.auto_reload = True
    app.run(host='localhost', port=8000)
    # app.run(host='0.0.0.0', port=8000) # Use to make available on network
