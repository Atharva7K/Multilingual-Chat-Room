from flask import render_template, flash, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from app import app
from app.models import User, Chat
from app import db
db.create_all()
from app.forms import LoginForm, RegistrationForm
from app import socketio
from googletrans import Translator


sid2username = {}
sid2lang = {}
translator = Translator()

def broadcast(sender_sid, msg, sid2lang, translator, sid2username, socket):
    print(sid2username)
    src = sid2lang[sender_sid]
    for reciever_sid, lang in sid2lang.items():
        dest = lang
        if reciever_sid != sender_sid:
            #print(f'reciever_sid is {sid2username[reciever_sid]}')
            translated = translator.translate(msg, src=src, dest=dest).text
            socket.emit('recieve', data=(translated, sid2username[sender_sid]), room=reciever_sid)
            print(f'Msg from {sid2username[sender_sid]} to {sid2username[reciever_sid]}')

            # chat = Chat(body = translated,
            #             timestamp = datetime.utcnow(),
            #             sender_username = sender_username,
            #             reciever_username = reciever_username)
            # db.session.add(chat)
            # db.session.commit()

@socketio.on('client_disconnected')
def client_disconnected():
    print(f'disconnected {request.sid}')
    del(sid2lang[request.sid])
    del(sid2username[request.sid])
    #print(f'session is {session}')
    #session.clear()
    print(sid2lang)
    print(sid2username)

@socketio.on('client_connected')
def client_connected(data):
    #print(f'Username: {session}')
    #print(f'connected {request.sid} {data["lang"]}')
    sid2lang[request.sid] = data['lang']
    sid2username[request.sid] = current_user.username
    print(f' sid2username {sid2username}')
    print(f'sid2lang {sid2lang}')

@socketio.on('send')
def event(data):
    print(f'Senders username {current_user.username}; senders sid {request.sid}')
    broadcast(request.sid,data['msg'],
             sid2lang, translator,
             sid2username, socketio)
    #broadcast(current_user.username, data['msg'], sid2lang, translator, socketio)

    #socketio.emit('recieve', data['msg'], broadcast=True)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('lang'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lang'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print(user)
        if user is None or not user.check_password(form.password.data):
            print(' ran')
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('lang'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))

@app.route('/lang', methods=['GET', 'POST'])
@login_required
def lang():
    return render_template('lang.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    return render_template('chat.html')
