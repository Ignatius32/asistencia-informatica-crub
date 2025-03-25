from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from app.models.user import User
from app.models.technician import Technician
from app.utils.email_service import EmailService
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        dni = request.form.get('dni')
        apellido = request.form.get('apellido')
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        departamento = request.form.get('departamento')
        
        if not all([dni, apellido, nombre, email, departamento]):
            flash('Todos los campos son requeridos', 'danger')
            return render_template('auth/register.html')
        
        existing_user = User.query.filter(
            (User.email == email) | (User.dni == dni)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                flash('El correo electrónico ya está registrado', 'danger')
            else:
                flash('El DNI ya está registrado', 'danger')
            return render_template('auth/register.html')
        
        try:    
            new_user = User(
                dni=dni,
                apellido=apellido,
                nombre=nombre,
                email=email,
                departamento=departamento,
                role='user'
            )
            token = new_user.generate_password_token()
            db.session.add(new_user)
            db.session.commit()
            
            # Send password setup email
            current_app.logger.info(f"User registered successfully: {email}")
            email_service = EmailService()
            email_result = email_service.send_password_setup_email(
                new_user.email,
                new_user.nombre,  # Using nombre instead of name
                token
            )
            
            if email_result["success"]:
                flash('¡Registro exitoso! Por favor, revise su correo electrónico para configurar su contraseña.', 'success')
                current_app.logger.info(f"Password setup email sent successfully to {email}")
            else:
                current_app.logger.error(f"Failed to send password setup email: {email_result['message']}")
                db.session.delete(new_user)
                db.session.commit()
                flash('Registro fallido: No se pudo enviar el correo de configuración. Por favor, intente nuevamente o contacte a soporte.', 'danger')
                return render_template('auth/register.html')
                
        except Exception as e:
            current_app.logger.error(f"Error during registration: {str(e)}")
            flash('El registro falló debido a un error del sistema. Por favor intente más tarde.', 'danger')
            return render_template('auth/register.html')
            
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/set-password/<token>', methods=['GET', 'POST'])
def set_password(token):
    if not token:
        flash('Enlace de configuración de contraseña inválido.', 'danger')
        return redirect(url_for('auth.login'))
        
    # Check both User and Technician models for the token
    user = User.query.filter_by(password_reset_token=token).first()
    technician = Technician.query.filter_by(password_reset_token=token).first()
    
    # Determine which type of account we're dealing with
    account = user if user else technician
    
    if not account or (user and not user.check_password_token(token)) or (technician and not technician.check_password_token(token)):
        flash('Enlace de configuración de contraseña inválido o expirado.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Por favor complete todos los campos.', 'danger')
            return render_template('auth/set_password.html', token=token)
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('auth/set_password.html', token=token)
            
        account.set_password(password)
        account.clear_password_token()
        db.session.commit()
        
        flash('¡Contraseña configurada exitosamente! Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/set_password.html', token=token)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni = request.form.get('dni')
        password = request.form.get('password')
        
        # Check for admin login
        if dni == 'admin':
            # Get admin user
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                flash('¡Cuenta de administrador no encontrada!', 'danger')
                return render_template('auth/login.html')
                
            if not password or not admin.check_password(password):
                flash('¡Credenciales de administrador inválidas!', 'danger')
                return render_template('auth/login.html')
            
            session['user_id'] = admin.id
            session['user_name'] = f"{admin.nombre} {admin.apellido}"
            session['user_role'] = 'admin'
            
            flash('¡Inicio de sesión de administrador exitoso!', 'success')
            return redirect(url_for('admin.dashboard'))
        
        # Check for technician login with DNI
        technician = Technician.query.filter_by(dni=dni).first()
        if technician:
            if not technician.password_hash:
                flash('Por favor configure su contraseña primero. Revise su correo electrónico para instrucciones.', 'warning')
                return render_template('auth/login.html')
                
            if not password or not technician.check_password(password):
                flash('¡Credenciales inválidas!', 'danger')
                return render_template('auth/login.html')
            
            session['user_id'] = technician.id
            session['user_name'] = technician.name
            session['user_role'] = 'technician'
            session['technical_profile'] = technician.technical_profile
            
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('tickets.technician_dashboard'))  # Changed this line
        
        # Check for regular user login with DNI
        user = User.query.filter_by(dni=dni).first()
        if user:
            if not user.password_hash:
                flash('Por favor configure su contraseña primero. Revise su correo electrónico para instrucciones.', 'warning')
                return render_template('auth/login.html')
                
            if not password or not user.check_password(password):
                flash('¡Credenciales inválidas!', 'danger')
                return render_template('auth/login.html')
            
            session['user_id'] = user.id
            session['user_name'] = f"{user.nombre} {user.apellido}"
            session['user_role'] = 'user'
            
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('tickets.list'))
        
        flash('¡Usuario no encontrado!', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Ha cerrado sesión exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        dni = request.form.get('dni')
        if not dni:
            flash('Por favor ingrese su DNI.', 'danger')
            return render_template('auth/forgot_password.html')
            
        # Check both User and Technician tables
        user = User.query.filter_by(dni=dni).first()
        technician = Technician.query.filter_by(dni=dni).first()
        
        account = user if user else technician
        
        if not account:
            flash('No se encontró una cuenta con ese DNI.', 'danger')
            return render_template('auth/forgot_password.html')
            
        # Generate password reset token
        token = account.generate_password_token()
        db.session.commit()
        
        # Send password reset email
        email_service = EmailService()
        name = f"{account.nombre} {account.apellido}" if isinstance(account, User) else account.name
        email_result = email_service.send_password_setup_email(
            account.email,
            name,
            token
        )
        
        if email_result["success"]:
            flash('Se ha enviado un enlace de recuperación a su correo electrónico.', 'success')
            return redirect(url_for('auth.login'))
        else:
            current_app.logger.error(f"Failed to send password reset email: {email_result['message']}")
            flash('Error al enviar el correo de recuperación. Por favor intente más tarde.', 'danger')
            
    return render_template('auth/forgot_password.html')