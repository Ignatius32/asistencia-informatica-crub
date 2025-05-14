from app import db

class Area(db.Model):
    __tablename__ = 'areas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    jefe_area_id = db.Column(db.Integer, db.ForeignKey('technicians.id'), unique=True, nullable=True)
    
    # One-to-One relationship with Technician (the chief)
    jefe_area = db.relationship('Technician', 
                               foreign_keys=[jefe_area_id], 
                               backref=db.backref('led_area', uselist=False), 
                               uselist=False)
    
    def __repr__(self):
        return f'<Area {self.name}>'
