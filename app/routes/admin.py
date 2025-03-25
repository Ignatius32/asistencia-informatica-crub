from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from functools import wraps
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.models.category import TicketCategory
from app.models.user import User
from app.utils.email_service import EmailService
from app import db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or session.get('user_role') != 'admin':
            flash('Se requiere acceso de administrador.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    # Calculate statistics for the dashboard
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='Abierto').count()
    closed_tickets = Ticket.query.filter_by(status='Cerrado').count()
    
    # Get all tickets for the table
    tickets = Ticket.query.all()
    
    # Get unique departments and technicians for filters
    departments = db.session.query(User.departamento).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    technicians = Technician.query.all()
    
    return render_template('admin/dashboard.html', 
                          total_tickets=total_tickets, 
                          open_tickets=open_tickets,
                          closed_tickets=closed_tickets,
                          tickets=tickets,
                          departments=departments,
                          technicians=technicians)

@admin_bp.route('/admin/manage_technicians', methods=['GET', 'POST'])
@admin_required
def manage_technicians():
    if request.method == 'POST':
        dni = request.form.get('dni')
        name = request.form.get('name')
        email = request.form.get('email')
        profile = request.form.get('profile')
        
        if not all([dni, name, email, profile]):
            flash('DNI, nombre, correo electrónico y perfil son requeridos.', 'danger')
            return render_template('admin/manage_technicians.html')
            
        existing_tech = Technician.query.filter(
            (Technician.email == email) | (Technician.dni == dni)
        ).first()
        
        if existing_tech:
            if existing_tech.email == email:
                flash('¡El correo electrónico ya está registrado!', 'danger')
            else:
                flash('¡El DNI ya está registrado!', 'danger')
            return render_template('admin/manage_technicians.html')
            
        try:
            new_technician = Technician(
                dni=dni,
                name=name, 
                email=email, 
                technical_profile=profile
            )
            token = new_technician.generate_password_token()
            db.session.add(new_technician)
            db.session.commit()
            
            # Send password setup email
            current_app.logger.info(f"Technician created successfully: {email}")
            email_service = EmailService()
            email_result = email_service.send_password_setup_email(
                new_technician.email,
                new_technician.name,
                token
            )
            
            if email_result["success"]:
                flash('¡Técnico agregado exitosamente! Recibirá un correo para configurar su contraseña.', 'success')
                current_app.logger.info(f"Password setup email sent to technician: {email}")
            else:
                current_app.logger.error(f"Failed to send password setup email to technician: {email_result['message']}")
                db.session.delete(new_technician)
                db.session.commit()
                flash('Error al agregar técnico: No se pudo enviar el correo de configuración.', 'danger')
                return render_template('admin/manage_technicians.html')
                
        except Exception as e:
            current_app.logger.error(f"Error creating technician: {str(e)}")
            flash('Error al agregar técnico debido a un error del sistema.', 'danger')
            return render_template('admin/manage_technicians.html')
            
        return redirect(url_for('admin.manage_technicians'))
    technicians = Technician.query.all()
    return render_template('admin/manage_technicians.html', technicians=technicians)

@admin_bp.route('/admin/edit_technician/<int:technician_id>', methods=['GET', 'POST'])
@admin_required
def edit_technician(technician_id):
    technician = Technician.query.get_or_404(technician_id)
    
    if request.method == 'POST':
        dni = request.form.get('dni')
        name = request.form.get('name')
        email = request.form.get('email')
        profile = request.form.get('profile')
        
        if not all([dni, name, email, profile]):
            flash('DNI, nombre, correo electrónico y perfil son requeridos.', 'danger')
            return render_template('admin/edit_technician.html', technician=technician)
            
        existing_tech = Technician.query.filter(
            (Technician.email == email) | (Technician.dni == dni)
        ).first()
        
        if existing_tech and existing_tech.id != technician_id:
            if existing_tech.email == email:
                flash('¡El correo electrónico ya está registrado!', 'danger')
            else:
                flash('¡El DNI ya está registrado!', 'danger')
            return render_template('admin/edit_technician.html', technician=technician)
        
        try:
            technician.dni = dni
            technician.name = name
            technician.email = email
            technician.technical_profile = profile
            db.session.commit()
            flash('¡Técnico actualizado exitosamente!', 'success')
            return redirect(url_for('admin.manage_technicians'))
        except Exception as e:
            current_app.logger.error(f"Error updating technician: {str(e)}")
            flash('Error al actualizar técnico.', 'danger')
    
    return render_template('admin/edit_technician.html', technician=technician)

@admin_bp.route('/admin/delete_technician/<int:technician_id>')
@admin_required
def delete_technician(technician_id):
    technician = Technician.query.get_or_404(technician_id)
    db.session.delete(technician)
    db.session.commit()
    flash('¡Técnico eliminado exitosamente!', 'success')
    return redirect(url_for('admin.manage_technicians'))

@admin_bp.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        technical_profile = request.form.get('technical_profile')
        active = 'active' in request.form
        category_id = request.form.get('category_id')
        
        if not all([name, technical_profile]):
            flash('El nombre y el perfil técnico son requeridos.', 'danger')
            return redirect(url_for('admin.manage_categories'))
            
        try:
            if category_id:
                # Update existing category
                category = TicketCategory.query.get_or_404(category_id)
                category.name = name
                category.description = description
                category.technical_profile = technical_profile
                category.active = active
                flash('¡Categoría actualizada exitosamente!', 'success')
            else:
                # Create new category
                category = TicketCategory(
                    name=name,
                    description=description,
                    technical_profile=technical_profile,
                    active=active
                )
                db.session.add(category)
                flash('¡Categoría agregada exitosamente!', 'success')
                
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error managing category: {str(e)}")
            flash('Error al guardar la categoría.', 'danger')
            
        return redirect(url_for('admin.manage_categories'))
        
    categories = TicketCategory.query.all()
    return render_template('admin/manage_categories.html', categories=categories)

@admin_bp.route('/admin/categories/<int:category_id>/edit')
@admin_required
def edit_category(category_id):
    category = TicketCategory.query.get_or_404(category_id)
    categories = TicketCategory.query.all()
    return render_template('admin/manage_categories.html', category=category, categories=categories)

@admin_bp.route('/admin/categories/<int:category_id>/toggle', methods=['POST'])
@admin_required
def toggle_category(category_id):
    category = TicketCategory.query.get_or_404(category_id)
    category.active = not category.active
    db.session.commit()
    status = "activada" if category.active else "desactivada"
    flash(f'¡Categoría {status} exitosamente!', 'success')
    return redirect(url_for('admin.manage_categories'))