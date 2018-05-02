import sys
sys.path.insert(0, '/var/www/fsw-p4-story-time')

from storytime import app as application
application.secret_key = 'CHANGEME!'
