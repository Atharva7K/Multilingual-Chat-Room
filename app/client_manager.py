from app.models import Chat
from datetime import datetime
from app import db
class ClientManager:

    def __init__(self):
        self.sid2client = {}

    def add_client(self, req_sid, client):
        self.sid2client[req_sid] = vars(client)

    def remove_client(self, req_sid):
        del self.sid2client[req_sid]

    def broadcast(self, sender_sid, msg, translator, socket):
        self_chat = Chat(body = msg, timestamp = datetime.utcnow(),
                         sender_id = self.sid2client[sender_sid]["id"],
                         reciever_id = self.sid2client[sender_sid]["id"])
        db.session.add(self_chat)
        db.session.commit()
        #print(self.sid2clientname)
        src = self.sid2client[sender_sid]['lang']
        sender = self.sid2client[sender_sid]

        for reciever_sid in self.sid2client:
            if reciever_sid != sender_sid:
                reciever = self.sid2client[reciever_sid]
                dest = reciever['lang']
                #print(f'reciever_sid is {self.sid2clientname[reciever_sid]}')
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

    def notify_client_join(self, new_client_sid, socket):
        username = self.sid2client[new_client_sid]['username']
        socket.emit('client_joined', {'username':username}, broadcast=True, include_self=False)

    def notify_client_leave(self, left_client_sid, socket):
        username = self.sid2client[left_client_sid]['username']
        for client_sid in self.sid2client:
            if client_sid != left_client_sid:
                socket.emit('client_left', {'username':username}, broadcast=True, include_self=False)
