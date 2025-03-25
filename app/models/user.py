from app import db
import bcrypt
from datetime import datetime, timedelta
import secrets

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    departamento = db.Column(db.String(100), nullable=True)  # New field
    role = db.Column(db.String(50), nullable=False)  # 'user' or 'admin'
    password_hash = db.Column(db.String(128))  # Only required for admin users
    password_reset_token = db.Column(db.String(100), unique=True)
    token_expiration = db.Column(db.DateTime)
    tickets = db.relationship('Ticket', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'
    
    def set_password(self, password):
        if password:
            self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        if self.password_hash and password:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        return False

    def generate_password_token(self):
        self.password_reset_token = secrets.token_urlsafe(32)
        self.token_expiration = datetime.utcnow() + timedelta(hours=24)
        return self.password_reset_token

    def check_password_token(self, token):
        if (self.password_reset_token and token and 
            self.password_reset_token == token and 
            self.token_expiration > datetime.utcnow()):
            return True
        return False

    def clear_password_token(self):
        self.password_reset_token = None
        self.token_expiration = None