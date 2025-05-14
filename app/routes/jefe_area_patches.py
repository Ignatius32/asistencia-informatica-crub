# This file contains fixes and updates for the jefe_area routes

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from functools import wraps
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.models.category import TicketCategory
from app.models.area import Area
from app.models.technician_category_assignment import TechnicianCategoryAssignment
from app.utils.email_service import EmailService
from app import db
from datetime import datetime

# Helper function to update add_category route validation
def update_add_category_validation():
    """
    This function should be called from the main app to patch the add_category route
    validation so it doesn't require technical_profile.
    """
    from app.routes.jefe_area import jefe_area_bp
    
    # Get original add_category function
    original_add_category = jefe_area_bp.view_functions['jefe_area.add_category']
    
    # Define new add_category function
    @jefe_area_bp.route('/add_category_updated', methods=['GET', 'POST'])
    @wraps(original_add_category)  # Preserve attributes of original function
    def add_category_updated():
        # Get managed area ID from session
        managed_area_id = session.get('managed_area_id')
        
        if not managed_area_id:
            flash('Error: No se ha encontrado el área gestionada.', 'danger')
            return redirect(url_for('tickets.technician_dashboard'))
        
        area = Area.query.get_or_404(managed_area_id)
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            technical_profile = request.form.get('technical_profile')  # Now optional
            
            # Validate form data - only name is required now
            if not name:
                flash('Por favor complete el nombre de la categoría.', 'danger')
                return render_template('jefe_area/add_category.html', area=area)
            
            # Check if category name already exists
            if TicketCategory.query.filter_by(name=name).first():
                flash('Ya existe una categoría con ese nombre.', 'danger')
                return render_template('jefe_area/add_category.html', area=area)
            
            # Create new category
            new_category = TicketCategory(
                name=name,
                description=description,
                technical_profile=technical_profile,  # Can be None now
                area_id=area.id,
                active=True
            )
            
            db.session.add(new_category)
            db.session.commit()
            
            flash('Categoría creada exitosamente.', 'success')
            return redirect(url_for('jefe_area.area_categories'))
        
        return render_template('jefe_area/add_category.html', area=area)
    
    # Replace the original route function with the updated one
    jefe_area_bp.view_functions['jefe_area.add_category'] = add_category_updated
    
    return True

# Helper function to update technician creation without technical_profile
def update_add_technician():
    """
    This function should be called from the main app to patch the add_technician route
    so it doesn't require technical_profile.
    """
    from app.routes.jefe_area import jefe_area_bp
    
    # Get original add_technician function
    original_add_technician = jefe_area_bp.view_functions['jefe_area.add_technician']
    
    # Define new add_technician function
    @jefe_area_bp.route('/add_technician_updated', methods=['GET', 'POST'])
    @wraps(original_add_technician)  # Preserve attributes of original function
    def add_technician_updated():
        # Get managed area ID from session
        managed_area_id = session.get('managed_area_id')
        
        if not managed_area_id:
            flash('Error: No se ha encontrado el área gestionada.', 'danger')
            return redirect(url_for('tickets.technician_dashboard'))
        
        area = Area.query.get_or_404(managed_area_id)
        
        if request.method == 'POST':
            dni = request.form.get('dni')
            name = request.form.get('name')
            email = request.form.get('email')
            
            # Validate form data - technical_profile is no longer required
            if not all([dni, name, email]):
                flash('Por favor complete todos los campos requeridos.', 'danger')
                return render_template('jefe_area/add_technician.html', area=area)
            
            # Check if technician already exists
            existing_tech = Technician.query.filter(
                (Technician.email == email) | (Technician.dni == dni)
            ).first()
            
            if existing_tech:
                if existing_tech.email == email:
                    flash('Ya existe un técnico con ese correo electrónico.', 'danger')
                else:
                    flash('Ya existe un técnico con ese DNI.', 'danger')
                return render_template('jefe_area/add_technician.html', area=area)
            
            # Create new technician - no technical_profile field
            new_technician = Technician(
                dni=dni,
                name=name,
                email=email,
                area_id=area.id  # Assign directly to the chief's area
            )
            
            db.session.add(new_technician)
            db.session.commit()
            
            # Send email invite to set up password
            email_service = EmailService()
            token = new_technician.generate_password_token()
            email_result = email_service.send_password_setup_email(
                new_technician.email,
                new_technician.name,
                token
            )
            
            if email_result.get("success"):
                flash(f'Técnico {name} creado exitosamente. Se ha enviado un correo para configurar la contraseña.', 'success')
            else:
                flash(f'Técnico {name} creado exitosamente, pero hubo un problema al enviar el correo de configuración.', 'warning')
            
            return redirect(url_for('jefe_area.area_technicians'))
        
        return render_template('jefe_area/add_technician.html', area=area)
    
    # Replace the original route function with the updated one
    jefe_area_bp.view_functions['jefe_area.add_technician'] = add_technician_updated
    
    return True
