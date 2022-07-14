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

# sid2username = {}
# sid2lang = {}
sid2user = {}
translator = Translator()
clients = []
map = {}
with open('assetMap.json', 'r', encoding='utf-8') as file:
    map = json.load(file)

def broadcast(sender_sid, msg, translator, socket):
    self_chat = Chat(body = msg,
                     timestamp = datetime.utcnow(),
                     sender_id = sid2user[sender_sid]["id"],
                     reciever_id = sid2user[sender_sid]["id"])
    db.session.add(self_chat)
    db.session.commit()
    #print(sid2username)
    src = sid2user[sender_sid]['lang']
    sender = sid2user[sender_sid]
    for reciever_sid in sid2user:
        if reciever_sid != sender_sid:
            reciever = sid2user[reciever_sid]
            dest = reciever['lang']
            #print(f'reciever_sid is {sid2username[reciever_sid]}')
            translated = translator.translate(msg, src=src, dest=dest).text
            socket.emit('recieve', data=(translated, sender['username']), room=reciever_sid)
            print(f'---------------Meesage from {sender_sid} to {reciever_sid} src{sender["lang"]} dest {reciever["lang"]}-----------')
            reciever_id = reciever['id']
            chat = Chat(body = translated,
                        timestamp = datetime.utcnow(),
                        sender_id = sender['id'],
                        reciever_id = reciever_id)
            db.session.add(chat)
            db.session.commit()

@socketio.on('client_disconnected')
def client_disconnected():
    print(f'disconnected {current_user.username}')
    # del(sid2lang[request.sid])
    # del(sid2username[request.sid])
    print(f'Removing {current_user.username} with sid {request.sid}')
    del(sid2user[request.sid])

@socketio.on('client_connected')
def connect():
    print(current_user)
    sid2user[request.sid] = vars(current_user)

@socketio.on('send')
def event(data):
    broadcast(request.sid, data['msg'],
              translator, socketio)

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
