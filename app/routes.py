from crypt import methods
from flask import render_template, flash, redirect, request, url_for, session
import flask_login
from flask_login import current_user, login_user, logout_user, login_required
from app import app
from app.models import User, Chat
from app import db
db.create_all()
from app.forms import LoginForm, RegistrationForm
from app import socketio
from googletrans import Translator
from datetime import datetime
from dateutil import tz
from sqlalchemy import or_, asc
import json
from app.client_manager import ClientManager
sid2user = {}
translator = Translator()
clients = []
map = {}
manager = ClientManager()

with open('assetMap.json', 'r', encoding='utf-8') as file:
    map = json.load(file)

@socketio.on('client_connected')
def connect():
    print(current_user)
    sid2user[request.sid] = vars(current_user)
    manager.add_client(request.sid, current_user)
    manager.notify_client_join(request.sid, socketio)

@socketio.on('client_disconnected')
def client_disconnected():
    print(f'Disconnected {current_user.username} with sid {request.sid}')
    manager.notify_client_leave(request.sid, socketio)
    manager.remove_client(request.sid)

@socketio.on('send')
def event(data):
    manager.broadcast(request.sid, data['msg'],
              translator, socketio)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    # if current_user.is_authenticated:
    #     return redirect(url_for('chat'))

    return render_template('lang.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        lang = request.form.get('lang')
        #print(lang)
        return render_template('index.html', map=map[lang])
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                    lang=form.lang.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, map=map[request.cookies.get('lang')])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('chat'))
    return render_template('login.html', form=form, map=map[request.cookies.get('lang')])


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/lang', methods=['GET', 'POST'])
@login_required
def lang():
    return render_template('lang.html')

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    id = current_user.id
    chats = Chat.query.filter(Chat.reciever_id==current_user.id) \
    .order_by(asc(Chat.timestamp)).all()

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    for chat in chats:
        chat.timestamp = chat.timestamp.replace(tzinfo=from_zone).astimezone(to_zone)
    if len(chats) != 0:
        return render_template('chat.html', chats = chats, map=map)
    else:
        return render_template('chat.html', map=map)
