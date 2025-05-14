from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from functools import wraps
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.models.category import TicketCategory
from app.models.user import User
from app.models.area import Area
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
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Number of tickets per page in admin dashboard
    
    # Calculate statistics for the dashboard
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='Abierto').count()
    closed_tickets = Ticket.query.filter_by(status='Cerrado').count()
    
    # Get all tickets for the table, paginated and ordered by created_at desc
    pagination = Ticket.query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    tickets = pagination.items
    
    # Get unique departments and technicians for filters
    departments = db.session.query(User.departamento).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    technicians = Technician.query.all()
    
    return render_template('admin/dashboard.html', 
                          total_tickets=total_tickets, 
                          open_tickets=open_tickets,
                          closed_tickets=closed_tickets,
                          tickets=tickets,
                          pagination=pagination,
                          departments=departments,
                          technicians=technicians)

@admin_bp.route('/admin/manage_technicians', methods=['GET', 'POST'])
@admin_required
def manage_technicians():
    areas = Area.query.all()
    
    if request.method == 'POST':
        dni = request.form.get('dni')
        name = request.form.get('name')
        email = request.form.get('email')
        profile = request.form.get('profile')
        area_id = request.form.get('area_id')
        
        if not all([dni, name, email, profile]):
            flash('DNI, nombre, correo electrónico y perfil son requeridos.', 'danger')
            return render_template('admin/manage_technicians.html', areas=areas)
            
        existing_tech = Technician.query.filter(
            (Technician.email == email) | (Technician.dni == dni)
        ).first()
        
        if existing_tech:
            if existing_tech.email == email:
                flash('¡El correo electrónico ya está registrado!', 'danger')
            else:
                flash('¡El DNI ya está registrado!', 'danger')
            return render_template('admin/manage_technicians.html', areas=areas)
            
        try:
            new_technician = Technician(
                dni=dni,
                name=name, 
                email=email, 
                technical_profile=profile,
                area_id=area_id if area_id and area_id != 'none' else None
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
    areas = Area.query.all()
    if request.method == 'POST':
        dni = request.form.get('dni')
        name = request.form.get('name')
        email = request.form.get('email')
        profile = request.form.get('profile')
        area_id = request.form.get('area_id')
        is_jefe_area = bool(request.form.get('is_jefe_area'))
        
        if not all([dni, name, email, profile]):
            flash('DNI, nombre, correo electrónico y perfil son requeridos.', 'danger')
            return render_template('admin/edit_technician.html', technician=technician, areas=areas)
            
        existing_tech = Technician.query.filter(
            (Technician.email == email) | (Technician.dni == dni)
        ).first()
        
        if existing_tech and existing_tech.id != technician_id:
            if existing_tech.email == email:
                flash('¡El correo electrónico ya está registrado!', 'danger')
            else:
                flash('¡El DNI ya está registrado!', 'danger')
            return render_template('admin/edit_technician.html', technician=technician, areas=areas)
        
        try:
            technician.dni = dni
            technician.name = name
            technician.email = email
            technician.technical_profile = profile
            
            # Handle area assignment
            old_area_id = technician.area_id
            
            # Process area assignment
            if area_id:
                technician.area_id = int(area_id)
            else:
                technician.area_id = None
                
            # Handle jefe_area status
            if is_jefe_area and area_id:
                # Check if this area already has a chief
                current_chief = Area.query.get(int(area_id)).jefe_area
                if current_chief and current_chief.id != technician.id:
                    flash(f'El área ya tiene un jefe asignado: {current_chief.name}. Primero debe remover al jefe actual.', 'warning')
                else:
                    # Make this technician the chief of the area
                    area = Area.query.get(int(area_id))
                    area.jefe_area_id = technician.id
            elif not is_jefe_area and technician.led_area:                # Remove this technician as chief of any area
                technician.led_area.jefe_area_id = None
                
            db.session.commit()
            flash('¡Técnico actualizado exitosamente!', 'success')
            return redirect(url_for('admin.manage_technicians'))
        except Exception as e:
            current_app.logger.error(f"Error updating technician: {str(e)}")
            flash('Error al actualizar técnico.', 'danger')
    
    return render_template('admin/edit_technician.html', technician=technician, areas=areas)

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
        area_id = request.form.get('area_id')
        
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
                category.area_id = area_id if area_id and area_id != 'none' else None
                flash('¡Categoría actualizada exitosamente!', 'success')
            else:
                # Create new category
                category = TicketCategory(
                    name=name,
                    description=description,
                    technical_profile=technical_profile,
                    active=active,
                    area_id=area_id if area_id and area_id != 'none' else None
                )
                db.session.add(category)
                flash('¡Categoría agregada exitosamente!', 'success')
                
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error managing category: {str(e)}")
            flash('Error al guardar la categoría.', 'danger')
            
        return redirect(url_for('admin.manage_categories'))
        
    categories = TicketCategory.query.all()
    areas = Area.query.all()
    return render_template('admin/manage_categories.html', categories=categories, areas=areas)

@admin_bp.route('/admin/categories/<int:category_id>/edit')
@admin_required
def edit_category(category_id):
    category = TicketCategory.query.get_or_404(category_id)
    categories = TicketCategory.query.all()
    areas = Area.query.all()
    return render_template('admin/manage_categories.html', category=category, categories=categories, areas=areas)

@admin_bp.route('/admin/categories/<int:category_id>/toggle', methods=['POST'])
@admin_required
def toggle_category(category_id):
    category = TicketCategory.query.get_or_404(category_id)
    category.active = not category.active
    db.session.commit()
    status = "activada" if category.active else "desactivada"
    flash(f'¡Categoría {status} exitosamente!', 'success')
    return redirect(url_for('admin.manage_categories'))

# Area Management Routes
@admin_bp.route('/admin/manage_areas')
@admin_required
def manage_areas():
    areas = Area.query.all()
    return render_template('admin/manage_areas.html', areas=areas)

@admin_bp.route('/admin/add_area', methods=['GET', 'POST'])
@admin_required
def add_area():
    if request.method == 'POST':
        name = request.form.get('name')
        jefe_area_id = request.form.get('jefe_area_id')
        
        if not name:
            flash('Por favor ingrese un nombre para el área.', 'danger')
            return redirect(url_for('admin.add_area'))
        
        # Check if area name already exists
        if Area.query.filter_by(name=name).first():
            flash('Ya existe un área con ese nombre.', 'danger')
            return redirect(url_for('admin.add_area'))
        
        # Create new area
        new_area = Area(name=name)
        
        # Assign jefe_area if provided and not "none"
        if jefe_area_id and jefe_area_id != "none":
            new_area.jefe_area_id = int(jefe_area_id)
        
        db.session.add(new_area)
        db.session.commit()
        
        flash('Área creada exitosamente.', 'success')
        return redirect(url_for('admin.manage_areas'))
    
    # Get all technicians for jefe_area selection
    technicians = Technician.query.all()
    return render_template('admin/edit_area.html', technicians=technicians)

@admin_bp.route('/admin/edit_area/<int:area_id>', methods=['GET', 'POST'])
@admin_required
def edit_area(area_id):
    area = Area.query.get_or_404(area_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        jefe_area_id = request.form.get('jefe_area_id')
        
        if not name:
            flash('Por favor ingrese un nombre para el área.', 'danger')
            return redirect(url_for('admin.edit_area', area_id=area_id))
        
        # Check if area name already exists and is not this area
        existing_area = Area.query.filter_by(name=name).first()
        if existing_area and existing_area.id != area_id:
            flash('Ya existe un área con ese nombre.', 'danger')
            return redirect(url_for('admin.edit_area', area_id=area_id))
        
        # Update area
        area.name = name
        
        # Update jefe_area
        if jefe_area_id == "none":
            area.jefe_area_id = None
        elif jefe_area_id:
            area.jefe_area_id = int(jefe_area_id)
        
        db.session.commit()
        
        flash('Área actualizada exitosamente.', 'success')
        return redirect(url_for('admin.manage_areas'))
    
    # Get all technicians for jefe_area selection
    technicians = Technician.query.all()
    return render_template('admin/edit_area.html', area=area, technicians=technicians)

@admin_bp.route('/admin/delete_area/<int:area_id>', methods=['POST'])
@admin_required
def delete_area(area_id):
    area = Area.query.get_or_404(area_id)
    
    # Check if area has technicians or categories
    if area.technicians.count() > 0:
        flash('No se puede eliminar un área con técnicos asignados.', 'danger')
        return redirect(url_for('admin.manage_areas'))
    
    if area.categories.count() > 0:
        flash('No se puede eliminar un área con categorías asignadas.', 'danger')
        return redirect(url_for('admin.manage_areas'))
    
    db.session.delete(area)
    db.session.commit()
    
    flash('Área eliminada exitosamente.', 'success')
    return redirect(url_for('admin.manage_areas'))

@admin_bp.route('/admin/manage_area_technicians/<int:area_id>', methods=['GET', 'POST'])
@admin_required
def manage_area_technicians(area_id):
    area = Area.query.get_or_404(area_id)
    
    if request.method == 'POST':
        # Get the technicians to assign to this area
        technician_ids = request.form.getlist('technicians')
        technician_ids = [int(id) for id in technician_ids if id]
        
        # Get all technicians currently in this area
        assigned_technician_ids = [tech.id for tech in area.technicians]
        
        # For technicians no longer assigned to this area
        for tech_id in assigned_technician_ids:
            if tech_id not in technician_ids:
                tech = Technician.query.get(tech_id)
                if tech:
                    tech.area_id = None
        
        # For newly assigned technicians
        for tech_id in technician_ids:
            tech = Technician.query.get(tech_id)
            if tech:
                # Remove from any current area
                tech.area_id = area.id
        
        db.session.commit()
        flash('Asignación de técnicos actualizada exitosamente.', 'success')
        return redirect(url_for('admin.manage_areas'))
    
    # Get all technicians
    all_technicians = Technician.query.all()
    assigned_technician_ids = [tech.id for tech in area.technicians]
    
    return render_template('admin/manage_area_technicians.html',
                          area=area,
                          all_technicians=all_technicians,
                          assigned_technician_ids=assigned_technician_ids)

@admin_bp.route('/admin/manage_area_categories/<int:area_id>', methods=['GET', 'POST'])
@admin_required
def manage_area_categories(area_id):
    area = Area.query.get_or_404(area_id)
    
    if request.method == 'POST':
        # Get the categories to assign to this area
        category_ids = request.form.getlist('categories')
        category_ids = [int(id) for id in category_ids if id]
        
        # Get all categories currently in this area
        assigned_category_ids = [cat.id for cat in area.categories]
        
        # For categories no longer assigned to this area
        for cat_id in assigned_category_ids:
            if cat_id not in category_ids:
                cat = TicketCategory.query.get(cat_id)
                if cat:
                    cat.area_id = None
        
        # For newly assigned categories
        for cat_id in category_ids:
            cat = TicketCategory.query.get(cat_id)
            if cat:
                # Update area ID
                cat.area_id = area.id
        
        db.session.commit()
        flash('Asignación de categorías actualizada exitosamente.', 'success')
        return redirect(url_for('admin.manage_areas'))
    
    # Get all categories
    all_categories = TicketCategory.query.all()
    assigned_category_ids = [cat.id for cat in area.categories]
    
    return render_template('admin/manage_area_categories.html',
                          area=area,
                          all_categories=all_categories,
                          assigned_category_ids=assigned_category_ids)