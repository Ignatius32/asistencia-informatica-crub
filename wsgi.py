import os
import sys
from dotenv import load_dotenv

# Add debug logging
import logging
logging.basicConfig(filename='/var/log/apache2/flask_debug.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Log current directory and python path
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Python path: {sys.path}")

# Try multiple possible .env file locations
possible_env_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),  # Current directory
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),  # Parent directory
    '/var/www/asistencia-informatica/.env'  # Absolute path in deployment
]

env_loaded = False
for env_path in possible_env_paths:
    if os.path.exists(env_path):
        logger.debug(f"Found .env file at: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    logger.error("No .env file found in any of the expected locations")
    for path in possible_env_paths:
        logger.error(f"Tried: {path}")

# Ensure SQLALCHEMY_DATABASE_URI is set explicitly for the application
if 'SQLALCHEMY_DATABASE_URI' not in os.environ:
    if 'DATABASE_URL' in os.environ:
        logger.debug("Setting SQLALCHEMY_DATABASE_URI from DATABASE_URL")
        os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    else:
        # Set a default SQLite path as fallback
        default_db_path = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'site.db')
        logger.debug(f"No database URI found in environment, using default: {default_db_path}")
        os.environ['SQLALCHEMY_DATABASE_URI'] = default_db_path

# Log critical environment variables (without revealing secrets)
logger.debug("Critical environment variables check:")
for key in ['SQLALCHEMY_DATABASE_URI', 'FLASK_APP', 'FLASK_ENV', 'SECRET_KEY']:
    value = os.environ.get(key)
    if key == 'SQLALCHEMY_DATABASE_URI' and value:
        # Only show DB type, not credentials
        db_type = value.split('://')[0] if '://' in value else 'unknown'
        logger.debug(f"{key}: {db_type}://**credentials-hidden**")
    elif key == 'SECRET_KEY' and value:
        logger.debug(f"{key}: **hidden**")
    else:
        logger.debug(f"{key}: {'SET' if value else 'NOT SET'}")

try:
    from app import create_app
    application = create_app()
    logger.debug("Application created successfully")
except Exception as e:
    logger.exception("Failed to create application")
    raise

if __name__ == '__main__':
    application.run()