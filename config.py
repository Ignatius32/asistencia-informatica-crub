import os
import sys
from dotenv import load_dotenv

# Try to load environment variables from .env file at different possible locations
possible_env_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),  # Current directory
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),  # Parent directory
    '/var/www/asistencia-informatica/.env'  # Absolute path in deployment
]

for env_path in possible_env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    
    # Use an absolute path for SQLite database to avoid path issues in production
    default_db_path = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'site.db')
    
    # Prioritize environment variables
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        os.environ.get('DATABASE_URL') or \
        default_db_path
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GAS_DEPLOYMENT_URL = os.environ.get('GAS_DEPLOYMENT_URL')
    ADMIN_NAME = os.environ.get('ADMIN_NAME')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    GOOGLE_DRIVE_SECURE_TOKEN = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN')