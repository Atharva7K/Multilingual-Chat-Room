from app import app

import eventlet
import eventlet.wsgi
eventlet.wsgi.server(eventlet.listen(('', 8000)), app)

# if __name__ == '__main__':
#     app.run()
