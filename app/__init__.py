from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_socketio import SocketIO
from flask_login import LoginManager


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

print(f' From __init__ {id(db)}')
login = LoginManager(app)
socketio = SocketIO(app)


from app import routes, models
