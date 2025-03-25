from app import create_app, db
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.utils.email_service import EmailService
from datetime import datetime, timedelta
import sys

def send_daily_summaries():
    """Send daily summary emails to all technicians."""
    app = create_app()
    with app.app_context():
        # Get all technicians
        technicians = Technician.query.all()
        today = datetime.now().date()
        
        for technician in technicians:
            # Count open tickets assigned to this technician
            open_tickets = Ticket.query.filter_by(
                technician_id=technician.id
            ).filter(
                Ticket.status != 'Closed'
            ).count()
            
            # Count tickets closed today by this technician
            closed_today = Ticket.query.filter_by(
                technician_id=technician.id,
                status='Closed'
            ).filter(
                Ticket.updated_at >= today
            ).count()
            
            # Send the summary email
            email_service = EmailService()
            result = email_service.send_technician_daily_summary(
                technician.email,
                technician.name,
                open_tickets,
                closed_today
            )
            
            if not result["success"]:
                print(f"Failed to send summary to {technician.name}: {result['message']}")
            else:
                print(f"Successfully sent summary to {technician.name}")

if __name__ == '__main__':
    send_daily_summaries()