from random import choice
from app.models.technician import Technician
from app.models.category import TicketCategory
from app.models.technician_category_assignment import TechnicianCategoryAssignment

class TicketDistributor:
    def __init__(self, technicians):
        self.technicians = technicians    
    def distribute_ticket(self, ticket_model_instance):
        """
        Distribute a ticket to the most appropriate technician.
        
        Args:
            ticket_model_instance: The actual Ticket ORM object
        
        Returns:
            Dict with technician details or None if no suitable technician found
        """
        # Get the ticket category
        ticket_category = ticket_model_instance.category
        
        # If no category, cannot distribute
        if not ticket_category:
            return None
        
        # Initialize lists
        area_techs_with_explicit_assignment = []
        area_techs_with_matching_profile = []
        other_techs_with_matching_profile = []
        area_techs_without_profile = []  # New: just any technician in the area
          # If the category has an associated area
        if ticket_category.area_id:
            # Get technicians explicitly assigned to this category via TechnicianCategoryAssignment
            explicit_assignments = TechnicianCategoryAssignment.query.filter_by(
                category_id=ticket_category.id
            ).all()
            
            for assignment in explicit_assignments:
                tech = Technician.query.get(assignment.technician_id)
                if tech and tech.area_id == ticket_category.area_id:
                    area_techs_with_explicit_assignment.append({
                        'id': tech.id,
                        'name': tech.name,
                        'profile': tech.technical_profile  # Keep for backward compatibility
                    })
        
        # If no explicit assignments within the area, find technicians in the same area
        # Note: We're now prioritizing area over technical profile
        if not area_techs_with_explicit_assignment and ticket_category.area_id:
            # Get all technicians in this area
            area_techs = Technician.query.filter_by(
                area_id=ticket_category.area_id
            ).all()
            
            for tech in area_techs:
                # Technical profile match is now optional, not required
                if not tech.technical_profile or tech.technical_profile == ticket_category.technical_profile:
                    area_techs_with_matching_profile.append({
                        'id': tech.id,
                        'name': tech.name,
                        'profile': tech.technical_profile
                    })
        
        # If still no matches within the area, fall back to any technician with matching profile
        if not area_techs_with_explicit_assignment and not area_techs_with_matching_profile:
            matching_techs = Technician.query.filter_by(
                technical_profile=ticket_category.technical_profile
            ).all()
            
            for tech in matching_techs:
                other_techs_with_matching_profile.append({
                    'id': tech.id,
                    'name': tech.name,
                    'profile': tech.technical_profile
                })
        
        # Determine which list to use, with priority order
        if area_techs_with_explicit_assignment:
            selected_techs = area_techs_with_explicit_assignment
        elif area_techs_with_matching_profile:
            selected_techs = area_techs_with_matching_profile
        elif other_techs_with_matching_profile:
            selected_techs = other_techs_with_matching_profile
        else:
            # No matching technicians found
            return None
        
        # Randomly select a technician from the appropriate list
        return choice(selected_techs) if selected_techs else None

# Helper function to get a list of technicians in the format the distributor expects
def get_technician_list():
    technicians = Technician.query.all()
    return [{'id': t.id, 'name': t.name, 'profile': t.technical_profile} for t in technicians]