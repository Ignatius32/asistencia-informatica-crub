import os
import platform
from dotenv import load_dotenv

# Determine if we're on Windows or Linux for path handling
IS_WINDOWS = platform.system() == 'Windows'

# Determine base directory for the application
if IS_WINDOWS:
    # On Windows, use current directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
else:
    # On Linux, check for production path first
    base_dir = '/var/www/asistencia-informatica'
    if not os.path.exists(base_dir):
        # Fallback to current directory
        base_dir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
env_file = os.path.join(base_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    
    # Make sure the instance directory exists with proper permissions
    instance_dir = os.path.join(base_dir, 'instance')
    if not os.path.exists(instance_dir):
        try:
            if IS_WINDOWS:
                os.makedirs(instance_dir)
            else:
                os.makedirs(instance_dir, mode=0o775)
        except:
            pass  # Will be handled later if this fails
    
    # Use absolute path for SQLite database
    db_path = os.path.join(base_dir, 'instance', 'site.db')
    
    # Database URI handling
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if db_uri and db_uri.startswith('sqlite:///'):
        if db_uri.startswith('sqlite:////'):
            # Already an absolute path
            pass
        else:
            # Convert relative path to absolute path
            rel_path = db_uri.replace('sqlite:///', '')
            if IS_WINDOWS:
                db_uri = f'sqlite:///{os.path.join(base_dir, rel_path)}'
            else:
                db_uri = f'sqlite:////{os.path.join(base_dir, rel_path)}'
    else:
        # Use default absolute path
        if IS_WINDOWS:
            db_uri = db_uri or os.environ.get('DATABASE_URL') or f'sqlite:///{db_path}'
        else:
            db_uri = db_uri or os.environ.get('DATABASE_URL') or f'sqlite:////{db_path}'
    
    SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GAS_DEPLOYMENT_URL = os.environ.get('GAS_DEPLOYMENT_URL')
    ADMIN_NAME = os.environ.get('ADMIN_NAME')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    GOOGLE_DRIVE_SECURE_TOKEN = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN')