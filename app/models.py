from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transactions = db.relationship('Transaction', backref='category_ref', lazy=True)
    is_default = db.Column(db.Boolean, default=False)

    def __init__(self, name, user_id, is_default=False):
        self.name = name
        self.user_id = user_id
        self.is_default = is_default

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False) 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    transaction_type = db.Column(db.String(64), nullable=False) 
    description = db.Column(db.String(256))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source = db.Column(db.String(64), default='manual') 
    
    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)
        if self.date is None:
            self.date = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'category_id': self.category_id,
            'transaction_type': self.transaction_type,
            'description': self.description or '',
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'source': self.source
        } 