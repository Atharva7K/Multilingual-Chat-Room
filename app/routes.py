from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user
from app.models import User
from app import db
from app import app
from app.forms import LoginForm
from app import socketio
from googletrans import Translator

print(f' From routes {id(db)}')

sid2lang = {}
translator = Translator()

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

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print('legit user')
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
