from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_socketio import SocketIO
from googletrans import Translator
translator = Translator()

app = Flask(__name__)
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

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    return render_template('chat.html')
