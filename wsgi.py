import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()