from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_session import Session
from flask_ngrok import run_with_ngrok

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

login = LoginManager(app)
login.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True)
run_with_ngrok(app)


from app import routes, models
