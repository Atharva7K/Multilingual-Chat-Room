import json
from datetime import datetime

from app import db
from app.models import Chat


class ClientManager:

    sid2client = {}
    def __init__(self):
        pass


    def add_client(self, req_sid, client):
        self.sid2client[req_sid] = vars(client)


    def delete_client(self, req_sid):
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
        socket.emit('client_left', {'username':username}, broadcast=True, include_self=False)


    def notify_inroom_clients(self, new_client_sid, socket):
        print('---------notifying clients--------')
        usernames = ''
        for i, client_sid in enumerate(self.sid2client):
            if client_sid != new_client_sid:
                if i == 0:
                    usernames = usernames + self.sid2client[client_sid]['username']
                else:
                    usernames = usernames + ' ' + self.sid2client[client_sid]['username']
        print(usernames)
        socket.emit('inroom_clients', usernames, room=new_client_sid)


    def add_new_client(self, new_client_sid, client, socket):
        self.add_client(new_client_sid, client)
        self.notify_client_join(new_client_sid, socket)
        self.notify_inroom_clients(new_client_sid, socket)


    def remove_client(self, client_sid, socket):
        self.notify_client_leave(client_sid, socket)
        self.delete_client(client_sid)
