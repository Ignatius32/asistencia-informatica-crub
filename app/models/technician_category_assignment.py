from app import db
from datetime import datetime

class TechnicianCategoryAssignment(db.Model):
    __tablename__ = 'technician_category_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('ticket_categories.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define unique constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('technician_id', 'category_id', name='uix_tech_cat_assignment'),
    )
    
    # Relationships
    technician = db.relationship('Technician', back_populates='category_assignments')
    category = db.relationship('TicketCategory', back_populates='technician_assignments')
    
    def __repr__(self):
        return f'<TechnicianCategoryAssignment technician_id={self.technician_id} category_id={self.category_id}>'
