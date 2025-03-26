from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Set application root for subpath deployment if configured
    if 'APPLICATION_ROOT' in os.environ:
        app.config['APPLICATION_ROOT'] = os.environ['APPLICATION_ROOT']
        app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Determine the correct base directory
    base_dir = '/var/www/asistencia-informatica'
    if not os.path.exists(base_dir):
        # If not in production, use current directory's parent
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Configure logging with absolute paths
    logs_dir = os.path.join(base_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    
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
    app.logger.setLevel(logging.INFO)
    app.logger.info('Helpdesk system startup')
    
    # Ensure instance path exists
    instance_path = os.path.join(base_dir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        app.logger.info(f"Created instance directory at {instance_path}")
    
    db.init_app(app)

    with app.app_context():
        from .routes.admin import admin_bp
        from .routes.auth import auth_bp
        from .routes.tickets import tickets_bp
        
        # Register blueprints
        app.register_blueprint(admin_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(tickets_bp)

        from .models import User, Technician, Ticket
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
                'name': 'Acceso a Internet',
                'technical_profile': 'redes-e-infraestructura',
                'description': 'Problemas de conectividad a internet o red local'
            },
            {
                'name': 'Impresora / Escáner',
                'technical_profile': 'soporte-tecnico',
                'description': 'Problemas con impresoras o escáneres'
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