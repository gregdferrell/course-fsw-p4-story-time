#
# Story Time App
# Main flask app
#

from flask import Flask

from storytime.web_api import web_api

# Setup Flask App
app = Flask(__name__)
app.url_map.strict_slashes = False
app.register_blueprint(web_api)

# -------------------- MAIN
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='localhost', port=8000)
    # app.run(host='0.0.0.0', port=8000) # Use to make available on network
