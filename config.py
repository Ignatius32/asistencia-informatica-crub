import os
from dotenv import load_dotenv

# Determine base directory for the application
base_dir = '/var/www/asistencia-informatica'
if not os.path.exists(base_dir):
    # If not in production, use current directory
    base_dir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
env_file = os.path.join(base_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    # Set a default SQLite database path if environment variable is not found
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, 'instance', 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GAS_DEPLOYMENT_URL = os.environ.get('GAS_DEPLOYMENT_URL')
    ADMIN_NAME = os.environ.get('ADMIN_NAME')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    GOOGLE_DRIVE_SECURE_TOKEN = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN')