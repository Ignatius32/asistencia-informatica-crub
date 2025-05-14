from app import db

class TicketCategory(db.Model):
    __tablename__ = 'ticket_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    technical_profile = db.Column(db.String(50), nullable=True)  # Made nullable since it's legacy
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='category', lazy=True)
    area = db.relationship('Area', backref=db.backref('categories', lazy='dynamic'))
    technician_assignments = db.relationship('TechnicianCategoryAssignment', back_populates='category', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TicketCategory {self.name} -> {self.technical_profile}>'