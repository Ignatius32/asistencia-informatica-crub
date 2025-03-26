import os
import sys
from dotenv import load_dotenv

# Add debug logging
import logging
# Change log location to application logs directory which should be writable by www-data
logs_dir = '/var/www/asistencia-informatica/logs'
if not os.path.exists(logs_dir):
    try:
        os.makedirs(logs_dir)
    except:
        pass  # We'll handle the error gracefully if we can't create the directory

log_file = os.path.join(logs_dir, 'flask_debug.log')
try:
    logging.basicConfig(filename=log_file, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
except:
    # Fallback to stderr if file logging fails
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.warning("Unable to write to log file, falling back to stderr")

# Log current directory and python path
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Python path: {sys.path}")

# Set absolute path for .env file - adjusted for direct deployment
base_dir = '/var/www/asistencia-informatica'
if not os.path.exists(base_dir):
    # If not in production, use current directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, '.env')
logger.debug(f"Looking for .env file at: {env_path}")

# Load environment variables from .env file
logger.debug("Loading .env file...")
load_dotenv(env_path)

# Set application root path for subpath deployment
os.environ['APPLICATION_ROOT'] = '/asistencia'

# Log all environment variables
logger.debug("Environment variables:")
for key, value in os.environ.items():
    logger.debug(f"{key}: {value if 'SECRET' not in key.upper() else '*****'}")

# Ensure database URI is set before importing app
if 'SQLALCHEMY_DATABASE_URI' not in os.environ and 'DATABASE_URL' in os.environ:
    logger.debug("Setting SQLALCHEMY_DATABASE_URI from DATABASE_URL")
    os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()