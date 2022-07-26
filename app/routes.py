from crypt import methods

import flask_login
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import app, db
from app.models import Chat, User

db.create_all()
import json
from datetime import datetime

from dateutil import tz
from googletrans import Translator
from sqlalchemy import asc, or_

from app import socketio
from app.client_manager import ClientManager
from app.forms import LoginForm, RegistrationForm

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
    manager.add_new_client(request.sid, current_user, socketio)


@socketio.on('client_disconnect')
def client_disconnect():
    print(f'{current_user.username} Disconnected')


def disconnect():
    print(f'Disconnected {current_user.username} with sid {request.sid}')
    manager.remove_client(request.sid, socketio)


@socketio.on('disconnect')
def disconnect():
    print(f'Disconnected {current_user.username} with sid {request.sid}')
    manager.remove_client(request.sid, socketio)


@socketio.on('send')
def event(data):
    manager.broadcast(request.sid, data['msg'],
              translator, socketio)


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    return render_template('lang.html')


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        lang = request.form.get('lang')
        return render_template('index.html', map=map[lang])
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
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
        return render_template('chat.html', chats=chats, map=map)
    else:
        return render_template('chat.html', map=map)
