from random import choice
from app.models.technician import Technician

class TicketDistributor:
    def __init__(self, technicians):
        self.technicians = technicians

    def distribute_ticket(self, ticket):
        profile = ticket.get('profile', 'soporte-tecnico')  # Default to 'soporte-tecnico'
        available_technicians = [tech for tech in self.technicians if tech['profile'] == profile]

        if available_technicians:
            assigned_technician = choice(available_technicians)
            return assigned_technician
        else:
            return None

# Helper function to get a list of technicians in the format the distributor expects
def get_technician_list():
    technicians = Technician.query.all()
    return [{'id': t.id, 'name': t.name, 'profile': t.technical_profile} for t in technicians]