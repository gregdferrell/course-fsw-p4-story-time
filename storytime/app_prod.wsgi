import sys
sys.path.insert(0, '/var/www/fsw-p4-story-time')

from storytime.app import app as application

# TODO Configure
application.config['DEMO'] = True
application.secret_key = 'CHANGEME!'
