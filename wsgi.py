import os
import sys
from dotenv import load_dotenv

# Explicitly set the base directory and change to it
base_dir = '/var/www/asistencia-informatica'
if os.path.exists(base_dir):
    os.chdir(base_dir)  # Change working directory to application directory

# Add debug logging
import logging
# Change log location to application logs directory which should be writable
logs_dir = os.path.join(base_dir, 'logs')
if not os.path.exists(logs_dir):
    try:
        os.makedirs(logs_dir, mode=0o775)
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

# Set absolute path for .env file
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