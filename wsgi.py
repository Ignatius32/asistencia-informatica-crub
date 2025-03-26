import os
import sys
import platform
from dotenv import load_dotenv

# Determine if we're on Windows or Linux for path handling
IS_WINDOWS = platform.system() == 'Windows'

# Determine base directory and set working directory
if IS_WINDOWS:
    # On Windows, use current directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
else:
    # On Linux, check for production path first
    base_dir = '/var/www/asistencia-informatica'
    if not os.path.exists(base_dir):
        # Fallback to current directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
    else:
        # Change working directory in production
        os.chdir(base_dir)

# Add debug logging
import logging
# Configure logging based on environment
logs_dir = os.path.join(base_dir, 'logs')
if not os.path.exists(logs_dir):
    try:
        if IS_WINDOWS:
            os.makedirs(logs_dir)
        else:
            os.makedirs(logs_dir, mode=0o775)
    except:
        pass  # Handle error gracefully

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

# Set application root path for subpath deployment only in production
if not IS_WINDOWS and os.path.exists('/var/www/asistencia-informatica'):
    os.environ['APPLICATION_ROOT'] = '/asistencia-informatica'
    logger.debug("Setting APPLICATION_ROOT to /asistencia-informatica (production)")
else:
    # In development, we run at root path
    logger.debug("Running in development mode without APPLICATION_ROOT")

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