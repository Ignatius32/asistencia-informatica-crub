# filepath: c:\Users\basti\OneDrive\Documentos\asistencia-informatica-crub\app\__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
import platform
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Set application root for subpath deployment if configured
    if 'APPLICATION_ROOT' in os.environ:
        app.config['APPLICATION_ROOT'] = os.environ['APPLICATION_ROOT']
        app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Determine if we're on Windows or Linux for path handling
    IS_WINDOWS = platform.system() == 'Windows'
    
    # Determine the correct base directory
    if IS_WINDOWS:
        # On Windows, use current directory's parent
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    else:
        # On Linux, check for production path first
        base_dir = '/var/www/asistencia-informatica'
        if not os.path.exists(base_dir):
            # Fallback to current directory's parent
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Configure logging with absolute paths
    logs_dir = os.path.join(base_dir, 'logs')
    if not os.path.exists(logs_dir):
        try:
            if IS_WINDOWS:
                os.makedirs(logs_dir)
            else:
                os.makedirs(logs_dir, mode=0o775)
        except:
            app.logger.warning("Could not create logs directory, logging to console only")
    
    try:
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'helpdesk.log'), 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    except:
        app.logger.warning("Could not configure file logging, logging to console only")
        
    app.logger.setLevel(logging.INFO)
    app.logger.info('Helpdesk system startup')
    
    # Ensure instance path exists
    instance_path = os.path.join(base_dir, 'instance')
    if not os.path.exists(instance_path):
        try:
            if IS_WINDOWS:
                os.makedirs(instance_path)
            else:
                os.makedirs(instance_path, mode=0o775)
            app.logger.info(f"Created instance directory at {instance_path}")
        except:
            app.logger.warning(f"Could not create instance directory at {instance_path}")
    
    db.init_app(app)
    
    with app.app_context():
        # Register blueprints
        from app.routes.auth import auth_bp
        from app.routes.tickets import tickets_bp
        from app.routes.admin import admin_bp
        from app.routes.jefe_area import jefe_area_bp  # Make sure this is imported
        
        app.register_blueprint(auth_bp)
        # Only register this once
        if 'tickets' not in app.blueprints:
            app.register_blueprint(tickets_bp)
        app.register_blueprint(admin_bp)
        # Register the new blueprint
        app.register_blueprint(jefe_area_bp)

        from .models import User, Technician, Ticket, Area, TicketCategory, TechnicianCategoryAssignment
        db.create_all()
        
        # Create default user and technicians if they don't exist
        create_defaults(app)

    return app

def create_defaults(app):
    """Create default users and technicians if they don't exist."""
    from .models.user import User
    from .models.technician import Technician
    from .models.category import TicketCategory
    from .utils.email_service import EmailService
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin:
        admin = User(
            dni='admin123',  # Default admin DNI
            apellido='Administrator',
            nombre='System',
            email=app.config['ADMIN_EMAIL'],
            role='admin'
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        app.logger.info(f"Created admin user: {app.config['ADMIN_EMAIL']}")
        
    # Create a default user if there are no users
    if User.query.filter_by(role='user').count() == 0:
        user = User(
            dni='user123',  # Default user DNI
            apellido='User',
            nombre='Default',
            email='user@example.com',
            role='user'
        )
        db.session.add(user)
        app.logger.info("Created default user")

    # Create default categories if there are none
    if TicketCategory.query.count() == 0:
        default_categories = [
            {
                'name': 'Hardware (problemas con equipos físicos)',
                'technical_profile': 'soporte-tecnico',
                'description': 'Problemas con computadoras, monitores y otros equipos físicos'
            },
            {
                'name': 'Software (problemas con aplicaciones o programas)',
                'technical_profile': 'soporte-tecnico',
                'description': 'Problemas con instalación, configuración o uso de software'
            },
            {
                'name': 'Falta de tinta o tóner en impresora',
                'technical_profile': 'soporte-tecnico',
                'description': 'Solicitud de reemplazo de consumibles'
            },
            {
                'name': 'Solicitud de nuevo equipo o software',
                'technical_profile': 'soporte-tecnico',
                'description': 'Petición de nuevo hardware o software'
            },
            {
                'name': 'Seguridad',
                'technical_profile': 'redes-e-infraestructura',
                'description': 'Problemas de seguridad informática'
            },
            {
                'name': 'Gestión de correos CRUB',
                'technical_profile': 'redes-e-infraestructura',
                'description': 'Soporte para correos institucionales'
            },
            {
                'name': 'Gestión de sitios web CRUB',
                'technical_profile': 'redes-e-infraestructura',
                'description': 'Soporte para sitios web institucionales'
            },
            {
                'name': 'Asistencia Multimedia',
                'technical_profile': 'soporte-tecnico',
                'description': 'Ayuda con equipos multimedia y presentaciones'
            }
        ]

        for cat_data in default_categories:
            category = TicketCategory(
                name=cat_data['name'],
                technical_profile=cat_data['technical_profile'],
                description=cat_data['description'],
                active=True
            )
            db.session.add(category)
        app.logger.info("Created default ticket categories")
    
    # Create default technicians if there are none
    if Technician.query.count() == 0:
        techs = [
        #    {
        #        'dni': 'tech001',
        #        'name': 'Alice',
        #        'email': 'alice@helpdesk.com',
        #        'technical_profile': 'redes-e-infraestructura'
        #    },
        #    {
        #        'dni': 'tech002',
        #        'name': 'Bob',
        #        'email': 'bob@helpdesk.com',
        #        'technical_profile': 'soporte-tecnico'
        #    },
            {
                'dni': '12345678',
                'name': 'Charlie',
                'email': 'ignaciobasti@gmail.com',
                'technical_profile': 'soporte-tecnico'
            }
        ]
        email_service = EmailService()
        for tech in techs:
            new_tech = Technician(**tech)
            db.session.add(new_tech)
            token = new_tech.generate_password_token()
            email_result = email_service.send_password_setup_email(
                new_tech.email,
                new_tech.name,
                token
            )
            if email_result["success"]:
                app.logger.info(f"Created technician and sent setup email: {tech['name']}")
            else:
                app.logger.warning(f"Created technician but failed to send setup email: {tech['name']}")
    
    db.session.commit()
    
    # Patches no longer needed as fixes have been applied directly to jefe_area.py
    # try:
    #     from .routes.jefe_area_patches import update_add_category_validation, update_add_technician
    #     update_add_category_validation()
    #     update_add_technician()
    #     app.logger.info("Applied patches for the jefe_area routes")
    # except Exception as e:
    #     app.logger.error(f"Error applying patches: {str(e)}")
