from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from functools import wraps
from app.models.ticket import Ticket
from app.models.user import User
from app.models.technician import Technician
from app.models.category import TicketCategory
from app.models.area import Area
from app.utils.ticket_distributor import TicketDistributor
from app.utils.email_service import EmailService
from app import db
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Por favor regístrese o inicie sesión primero.', 'warning')
            return redirect(url_for('auth.register'))
        return f(*args, **kwargs)
    return decorated_function

@tickets_bp.route('/')
def area_select():
    """Display all available areas for ticket creation"""
    # Get all areas
    areas = Area.query.all()
    
    # Check if there are areas with at least one category
    valid_areas = []
    for area in areas:
        if area.categories.count() > 0:
            valid_areas.append(area)
    
    # If no valid areas, show a message
    if not valid_areas:
        flash('No hay áreas disponibles con categorías. Por favor contacte al administrador.', 'warning')
    
    # If the user is not logged in, redirect to login
    if not session.get('user_id'):
        flash('Por favor inicie sesión primero para crear un ticket.', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('tickets/area_select.html', areas=valid_areas)

@tickets_bp.route('/tickets')
@login_required
def tickets_index():
    """Redirect to ticket list"""
    return redirect(url_for('tickets.list'))

@tickets_bp.route('/area/<int:area_id>/tickets/create', methods=['GET', 'POST'])
@login_required
def create_by_area(area_id):
    """Create a ticket for a specific area"""
    # Get area by ID
    area = Area.query.get_or_404(area_id)
    
    # Get categories for this area
    categories = TicketCategory.query.filter_by(area_id=area_id, active=True).all()
    
    if not categories:
        flash('Esta área no tiene categorías disponibles para tickets.', 'warning')
        return redirect(url_for('tickets.area_select'))
    
    if request.method == 'POST':
        description = request.form['description']
        category_id = request.form.get('category_id')
        user_id = session['user_id']
        user = User.query.get(user_id)
        email_service = EmailService()
        
        # Validate that category belongs to the selected area
        category = TicketCategory.query.get(category_id)
        if not category or not category.active or category.area_id != area_id:
            flash('Categoría seleccionada inválida o inactiva para esta área.', 'danger')
            return render_template('tickets/create_by_area.html', area=area, categories=categories)
        
        new_ticket = Ticket(
            description=description, 
            status='Abierto', 
            priority=request.form.get('priority', 'baja'),
            user_id=user_id,
            category_id=category_id,
            profile=category.technical_profile
        )
        db.session.add(new_ticket)
        db.session.commit()
        
        # Distribute the ticket to an appropriate technician
        from app.utils.ticket_distributor import get_technician_list
        technicians = get_technician_list()
        distributor = TicketDistributor(technicians)
        assigned_tech = distributor.distribute_ticket(new_ticket)
        if assigned_tech:
            new_ticket.technician_id = assigned_tech['id']
            db.session.commit()        # Send email to user about ticket creation
        if user and user.email:
            # Get technician name if assigned, or "No asignado" if not
            technician_name = new_ticket.technician.name if new_ticket.technician else "No asignado"
            email_service.send_ticket_creation_notification(
                user.email, 
                user.nombre,
                new_ticket.id,
                new_ticket.description,
                technician_name
            )
          # Send email to assigned technician if one was assigned
        if new_ticket.technician and new_ticket.technician.email:
            email_service.send_ticket_assignment_notification(
                new_ticket.technician.email,
                new_ticket.technician.name,
                new_ticket.id,
                new_ticket.description,
                user.nombre
            )
          # Also notify the area chief if one exists
        if area.jefe_area and area.jefe_area.email and area.jefe_area.id != new_ticket.technician_id:
            email_service.send_area_ticket_notification(
                area.jefe_area.email,
                area.jefe_area.name,
                new_ticket.id,
                new_ticket.description,
                area.name
            )
        
        flash('Tu ticket ha sido creado y será atendido a la brevedad.', 'success')
        return redirect(url_for('tickets.view', ticket_id=new_ticket.id))
    
    return render_template('tickets/create_by_area.html', area=area, categories=categories)

@tickets_bp.route('/tickets/list')
@login_required
def list_tickets():
    return redirect(url_for('tickets.list'))

@tickets_bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create():
    """Redirect to area selection for ticket creation instead of directly creating tickets"""
    # Redirect to area selection page
    return redirect(url_for('tickets.area_select'))

@tickets_bp.route('/tickets')
@login_required
def list():
    # Get page from query parameters, default to 1 if not provided
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Number of tickets per page
    
    # Only show tickets for the current user unless they're an admin
    if session.get('user_role') == 'admin':
        pagination = Ticket.query.order_by(Ticket.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
    else:
        pagination = Ticket.query.filter_by(user_id=session['user_id']).order_by(
            Ticket.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    tickets = pagination.items
    return render_template('tickets/list.html', tickets=tickets, pagination=pagination)

@tickets_bp.route('/tickets/<int:ticket_id>')
@login_required
def view(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if session.get('user_role') == 'admin':
        # Admin can view all tickets
        can_update = True
        return render_template('tickets/view.html', ticket=ticket, can_update=can_update)
    elif session.get('user_role') == 'technician':
        # Check if user is a Jefe de Área
        is_jefe_area = session.get('is_jefe_area', False)
        managed_area_id = session.get('managed_area_id')
        
        # Jefe de Área can view if the ticket is in their area
        if is_jefe_area and (
            (ticket.category and ticket.category.area_id == managed_area_id) or
            (ticket.technician and ticket.technician.area_id == managed_area_id)
        ):
            can_update = True
            return render_template('tickets/view.html', ticket=ticket, can_update=can_update)
        
        # Regular technicians can only view tickets if:
        # 1. They are assigned to the ticket OR
        # 2. The ticket is unassigned AND in their technical area
        if (ticket.technician_id == session['user_id'] or 
            (ticket.technician_id is None and ticket.profile == session.get('technical_profile'))):
            # Technician can update only if assigned to them
            can_update = ticket.technician_id == session['user_id']
            return render_template('tickets/view.html', ticket=ticket, can_update=can_update)
    else:
        # Regular users can only view their own tickets
        if ticket.user_id == session['user_id']:
            return render_template('tickets/view.html', ticket=ticket, can_update=False)
    
    flash('No tienes permiso para ver este ticket', 'danger')
    return redirect(url_for('tickets.list'))

@tickets_bp.route('/tickets/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    email_service = EmailService()  # Initialize EmailService here
      # Prevent changes to closed tickets by technicians
    if ticket.status == 'Cerrado' and session.get('user_role') == 'technician':
        flash('No se puede modificar un ticket cerrado', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    # Check permissions: admin, assigned technician, or jefe_area of the corresponding area
    has_permissions = (
        session.get('user_role') == 'admin' or 
        (ticket.technician and session.get('user_id') == ticket.technician.id) or
        (session.get('is_jefe_area') and (
            # Jefe can modify if ticket's category belongs to their area
            (ticket.category and ticket.category.area_id == session.get('managed_area_id')) or
            # Or if ticket is assigned to a technician in their area
            (ticket.technician and ticket.technician.area_id == session.get('managed_area_id'))
        ))
    )
    
    if not has_permissions:
        flash('No tienes permiso para actualizar este ticket', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
    new_status = request.form.get('status')
    solution = request.form.get('solution')
    
    if new_status and new_status in ['Abierto', 'En Proceso', 'Cerrado']:
        old_status = ticket.status
        ticket.status = new_status
        
        # If closing ticket, solution is required
        if new_status == 'Cerrado':
            if not solution:
                flash('Se requiere una descripción de la solución al cerrar el ticket', 'danger')
                return redirect(url_for('tickets.view', ticket_id=ticket_id))
            ticket.solution = solution
            
            # Send solution email only when closing the ticket
            user = User.query.get(ticket.user_id) if ticket.user_id else None
            technician = Technician.query.get(ticket.technician_id) if ticket.technician_id else None
            technician_name = technician.name if technician else "Not assigned"
            
            if user and user.email:
                email_result = email_service.send_ticket_status_update(
                    user.email,
                    f"{user.nombre} {user.apellido}",
                    ticket.id,
                    ticket.description,
                    ticket.status,
                    technician_name,
                    solution
                )
                
                if not email_result["success"]:
                    current_app.logger.warning(f"Failed to send solution email: {email_result['message']}")
            
        db.session.commit()
        flash(f'Estado del ticket actualizado de {old_status} a {new_status}', 'success')
    else:
        flash('Estado inválido', 'danger')
    
    # Redirect to technician dashboard if user is a technician
    if session.get('user_role') == 'technician':
        return redirect(url_for('tickets.technician_dashboard'))
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/tickets/<int:ticket_id>/update_priority', methods=['POST'])
@login_required
def update_priority(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions: admin or jefe_area of the corresponding area
    has_permissions = (
        session.get('user_role') == 'admin' or 
        (session.get('is_jefe_area') and (
            # Jefe can modify if ticket's category belongs to their area
            (ticket.category and ticket.category.area_id == session.get('managed_area_id')) or
            # Or if ticket is assigned to a technician in their area
            (ticket.technician and ticket.technician.area_id == session.get('managed_area_id'))
        ))
    )
    
    if not has_permissions:
        flash('No tienes permiso para actualizar la prioridad de tickets', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
    new_priority = request.form.get('priority')
    
    if new_priority and new_priority in ['baja', 'media', 'alta', 'maxima']:
        old_priority = ticket.priority
        ticket.priority = new_priority
        db.session.commit()
        flash(f'Prioridad del ticket actualizada de {old_priority.title()} a {new_priority.title()}', 'success')
    else:
        flash('Prioridad inválida', 'danger')
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/tickets/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    if session.get('user_role') != 'admin':
        flash('No tienes permiso para eliminar tickets', 'danger')
        return redirect(url_for('tickets.list'))
        
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket eliminado exitosamente', 'success')
    return redirect(url_for('tickets.list'))

@tickets_bp.route('/technician/dashboard')
@login_required
def technician_dashboard():
    if session.get('user_role') != 'technician':
        flash('Acceso denegado. Se requiere acceso de técnico.', 'danger')
        return redirect(url_for('tickets.list'))
        
    technician_id = session.get('user_id')
    today = datetime.utcnow().date()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Number of tickets per page
    section = request.args.get('section', 'open')  # Default to open section
    
    # Get unique departments for filter dropdowns
    departments = db.session.query(User.departamento).filter(
        User.departamento.isnot(None)).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    # Get tickets assigned to this technician by status
    open_pagination = Ticket.query.filter_by(
        technician_id=technician_id,
        status='Abierto'
    ).order_by(Ticket.created_at.desc()).paginate(
        page=(page if section == 'open' else 1), 
        per_page=per_page, 
        error_out=False
    )
    
    in_progress_pagination = Ticket.query.filter_by(
        technician_id=technician_id,
        status='En Proceso'
    ).order_by(Ticket.created_at.desc()).paginate(
        page=(page if section == 'in_progress' else 1), 
        per_page=per_page, 
        error_out=False
    )
    
    closed_pagination = Ticket.query.filter_by(
        technician_id=technician_id,
        status='Cerrado'
    ).order_by(Ticket.updated_at.desc()).paginate(
        page=(page if section == 'closed' else 1), 
        per_page=per_page, 
        error_out=False
    )
    
    # Calculate statistics
    stats = {
        'open_tickets': Ticket.query.filter_by(
            technician_id=technician_id,
            status='Abierto'
        ).count(),
        'in_progress_tickets': Ticket.query.filter_by(
            technician_id=technician_id,
            status='En Proceso'
        ).count(),
        'closed_today': Ticket.query.filter(
            Ticket.technician_id == technician_id,
            Ticket.status == 'Cerrado',
            Ticket.updated_at >= today
        ).count()
    }
    
    return render_template('tickets/technician_dashboard.html',
                         open_tickets=open_pagination.items,
                         in_progress_tickets=in_progress_pagination.items,
                         closed_tickets=closed_pagination.items,
                         open_pagination=open_pagination,
                         in_progress_pagination=in_progress_pagination,
                         closed_pagination=closed_pagination,
                         departments=departments,
                         stats=stats,
                         current_section=section)