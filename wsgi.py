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

# Set absolute path for .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
logger.debug(f"Looking for .env file at: {env_path}")

# Load environment variables from .env file
logger.debug("Loading .env file...")
load_dotenv(env_path)

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