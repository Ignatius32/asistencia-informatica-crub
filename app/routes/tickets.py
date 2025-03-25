from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from functools import wraps
from app.models.ticket import Ticket
from app.models.user import User
from app.models.technician import Technician
from app.models.category import TicketCategory
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
@login_required
def home():
    return redirect(url_for('tickets.list'))

@tickets_bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        description = request.form['description']
        category_id = request.form.get('category_id')
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        # Get category and its technical profile
        category = TicketCategory.query.get(category_id)
        if not category or not category.active:
            flash('Categoría seleccionada inválida o inactiva.', 'danger')
            return redirect(url_for('tickets.create'))
        
        new_ticket = Ticket(
            description=description, 
            status='Abierto', 
            priority=request.form.get('priority', 'baja'),
            user_id=user_id,
            category_id=category_id,
            profile=category.technical_profile  # Set profile from category
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        
        technicians = Technician.query.all()
        tech_list = [{'id': t.id, 'name': t.name, 'profile': t.technical_profile} for t in technicians]
        
        distributor = TicketDistributor(tech_list)
        ticket_dict = {'id': new_ticket.id, 'description': new_ticket.description, 'profile': category.technical_profile}
        
        assigned_tech = distributor.distribute_ticket(ticket_dict)
        technician_name = "Sin asignar"
        
        if assigned_tech:
            new_ticket.technician_id = assigned_tech['id']
            db.session.commit()
            technician_name = assigned_tech["name"]
            flash(f'Ticket creado y asignado a {technician_name}', 'success')
        else:
            flash('Ticket creado pero no hay técnicos disponibles para esta área', 'warning')
        
        if user.email:
            email_service = EmailService()
            email_result = email_service.send_ticket_creation_notification(
                user.email,
                f"{user.nombre} {user.apellido}",
                new_ticket.id,
                new_ticket.description,
                technician_name
            )
            
            if not email_result["success"]:
                current_app.logger.warning(f"Failed to send ticket creation email: {email_result['message']}")
            
        return redirect(url_for('tickets.list'))
    
    # Get active categories for the form
    categories = TicketCategory.query.filter_by(active=True).all()
    return render_template('tickets/create.html', categories=categories)

@tickets_bp.route('/tickets')
@login_required
def list():
    # Only show tickets for the current user unless they're an admin
    if session.get('user_role') == 'admin':
        tickets = Ticket.query.all()
    else:
        tickets = Ticket.query.filter_by(user_id=session['user_id']).all()
    return render_template('tickets/list.html', tickets=tickets)

@tickets_bp.route('/tickets/<int:ticket_id>')
@login_required
def view(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if session.get('user_role') == 'admin':
        # Admin can view all tickets
        return render_template('tickets/view.html', ticket=ticket)
    elif session.get('user_role') == 'technician':
        # Technicians can only view tickets if:
        # 1. They are assigned to the ticket OR
        # 2. The ticket is unassigned AND in their technical area
        if (ticket.technician_id == session['user_id'] or 
            (ticket.technician_id is None and ticket.profile == session.get('technical_profile'))):
            return render_template('tickets/view.html', ticket=ticket)
    else:
        # Regular users can only view their own tickets
        if ticket.user_id == session['user_id']:
            return render_template('tickets/view.html', ticket=ticket)
    
    flash('No tienes permiso para ver este ticket', 'danger')
    return redirect(url_for('tickets.list'))

@tickets_bp.route('/tickets/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Prevent changes to closed tickets by technicians
    if ticket.status == 'Cerrado' and session.get('user_role') == 'technician':
        flash('No se puede modificar un ticket cerrado', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    # Only allow technicians assigned to the ticket or admins to update status
    if not (session.get('user_role') == 'admin' or 
            (ticket.technician and session.get('user_id') == ticket.technician.id)):
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
                email_service = EmailService()
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
    if session.get('user_role') != 'admin':
        flash('No tienes permiso para actualizar la prioridad de tickets', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
    ticket = Ticket.query.get_or_404(ticket_id)
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
    
    # Get tickets assigned to this technician by status
    open_tickets = Ticket.query.filter_by(
        technician_id=technician_id,
        status='Abierto'
    ).all()
    
    in_progress_tickets = Ticket.query.filter_by(
        technician_id=technician_id,
        status='En Proceso'
    ).all()
    
    closed_tickets = Ticket.query.filter_by(
        technician_id=technician_id,
        status='Cerrado'
    ).order_by(Ticket.updated_at.desc()).limit(10).all()  # Show last 10 closed tickets
    
    # Calculate statistics
    stats = {
        'open_tickets': len(open_tickets),
        'in_progress_tickets': len(in_progress_tickets),
        'closed_today': Ticket.query.filter(
            Ticket.technician_id == technician_id,
            Ticket.status == 'Cerrado',
            Ticket.updated_at >= today
        ).count()
    }
    
    return render_template('tickets/technician_dashboard.html',
                         open_tickets=open_tickets,
                         in_progress_tickets=in_progress_tickets,
                         closed_tickets=closed_tickets,
                         stats=stats)