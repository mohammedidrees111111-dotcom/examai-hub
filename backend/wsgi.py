import sys
path = '/home/mohammedidrees/examai-hub/backend'
if path not in sys.path:
    sys.path.insert(0, path)
from app.main import app as application
