from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app import db
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    lang = db.Column(db.String(5))
    sent = db.relationship('Chat', backref='sender', lazy='dynamic', foreign_keys = '[chat.c.sender_id]')
    recieved = db.relationship('Chat', backref='reciever', lazy='dynamic', foreign_keys = '[chat.c.reciever_id]')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_lang(self, lang):
        self.lang = lang
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reciever_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return str({
        'timestamp':self.timestamp.strftime('%d %b %Y %I:%M %p'),
        'sender_id':self.sender_id,
        'reciever_id':self.reciever_id,
        'body':self.body
        })

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
