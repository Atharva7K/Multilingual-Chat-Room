from crypt import methods
from flask import render_template, flash, redirect, request, url_for, session
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

sid2username = {}
sid2lang = {}
translator = Translator()

map = {}
with open('assetMap.json', 'r', encoding='utf-8') as file:
    map = json.load(file)
def broadcast(sender_sid, sender_id, msg, sid2lang, translator, sid2username, user_id, socket):
    self_chat = Chat(body = msg,
                     timestamp = datetime.utcnow(),
                     sender_id = sender_id,
                     reciever_id = sender_id)
    db.session.add(self_chat)
    db.session.commit()
    #print(sid2username)
    src = sid2lang[sender_sid]
    for reciever_sid, lang in sid2lang.items():
        dest = lang
        if reciever_sid != sender_sid:
            #print(f'reciever_sid is {sid2username[reciever_sid]}')
            translated = translator.translate(msg, src=src, dest=dest).text
            socket.emit('recieve', data=(translated, sid2username[sender_sid]), room=reciever_sid)
            print(f'Msg from {sid2username[sender_sid]} to {sid2username[reciever_sid]}')
            reciever_id = User.query.filter_by(username=sid2username[reciever_sid]).first().id
            chat = Chat(body = translated,
                        timestamp = datetime.utcnow(),
                        sender_id = user_id,
                        reciever_id = reciever_id)
            db.session.add(chat)
            db.session.commit()

@socketio.on('client_disconnected')
def client_disconnected():
    print(f'disconnected {request.sid}')
    del(sid2lang[request.sid])
    del(sid2username[request.sid])

@socketio.on('client_connected')
def client_connected(data):
    sid2lang[request.sid] = data['lang']
    sid2username[request.sid] = current_user.username
    print(sid2lang)
    print(sid2username)

@socketio.on('send')
def event(data):
    broadcast(request.sid, current_user.id,
             data['msg'], sid2lang,
             translator, sid2username,
             current_user.id, socketio)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
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
    print('yo', request.cookies.get('lang'))
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
        return render_template('chat.html', chats = chats)
    else:
        return render_template('chat.html')
