import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure database URI is set before importing app
if 'SQLALCHEMY_DATABASE_URI' not in os.environ and 'DATABASE_URL' in os.environ:
    os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()