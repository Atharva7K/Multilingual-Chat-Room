import eventlet
import eventlet.wsgi

from app import app

eventlet.wsgi.server(eventlet.listen(('', 8000)), app)

# if __name__ == '__main__':
#     app.run()
