from flask import Flask, render_template, request, redirect, url_for, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager, current_user, login_user
from googletrans import Translator
from forms import LoginForm
from config import Config
from models import User
translator = Translator()

app = Flask(__name__)
login = LoginManager(app)
app.config.from_object(Config)
db = SQLAlchemy(app)
socketio = SocketIO(app)

sid2lang = {}

def broadcast(sender_sid, msg, sid2lang, translator, socket):
    src = sid2lang[sender_sid]
    for client, lang in sid2lang.items():
        dest = lang
        if client != sender_sid:
            translated = translator.translate(msg, src=src, dest=dest).text
            socket.emit('recieve', data=(translated, client), room=client)

@socketio.on('client_disconnected')
def client_disconnected():
    print(f'disconnected {request.sid}')
    del(sid2lang[request.sid])
    print(sid2lang)

@socketio.on('client_connected')
def client_connected(data):
    print(f'connected {request.sid} {data["lang"]}')
    sid2lang[request.sid] = data['lang']

@socketio.on('send')
def event(data):
    print(f'from send. {request.sid}')
    broadcast(request.sid, data['msg'], sid2lang, translator, socketio)
    #socketio.emit('recieve', data['msg'], broadcast=True)


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('lang.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lang'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('lang'))
    return render_template('login.html', form=form)
@app.route('/lang', methods=['GET', 'POST'])
def lang():
    return render_template('lang.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    return render_template('chat.html')
