from app import db

class TicketCategory(db.Model):
    __tablename__ = 'ticket_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    technical_profile = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    tickets = db.relationship('Ticket', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<TicketCategory {self.name} -> {self.technical_profile}>'