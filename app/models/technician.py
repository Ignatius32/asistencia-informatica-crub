from app import db
import bcrypt
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import relationship

class Technician(db.Model):
    __tablename__ = 'technicians'

    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    technical_profile = db.Column(db.String(50), nullable=True)  # Made nullable since it's legacy
    password_hash = db.Column(db.String(128))
    password_reset_token = db.Column(db.String(100), unique=True)
    token_expiration = db.Column(db.DateTime)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='technician', lazy=True)
    area = db.relationship('Area', foreign_keys=[area_id], backref=db.backref('technicians', lazy='dynamic'))
    category_assignments = db.relationship('TechnicianCategoryAssignment', back_populates='technician', cascade='all, delete-orphan')
    assigned_categories = db.relationship('TicketCategory', secondary='technician_category_assignments', 
                                         viewonly=True, lazy='dynamic',
                                         backref=db.backref('assigned_technicians', viewonly=True, lazy='dynamic'))

    def __repr__(self):
        return f'<Technician {self.name} - {self.technical_profile}>'
    
    @property
    def is_jefe_area(self):
        from app.models.area import Area
        return Area.query.filter_by(jefe_area_id=self.id).first() is not None
        
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