from flask import Flask
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
from datetime import datetime
import sys
import sqlite3
from sqlalchemy import text

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Get the database URI from .env
DB_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/site.db')

# For SQLite, extract the database path
if DB_URI.startswith('sqlite:///'):
    sqlite_path = DB_URI.replace('sqlite:///', '')
    # Make path absolute if it's relative
    if not os.path.isabs(sqlite_path):
        sqlite_path = os.path.join(project_root, sqlite_path)
else:
    print(f"Unsupported database URI: {DB_URI}")
    sys.exit(1)

print(f"Using SQLite database at: {sqlite_path}")

# Check if the database file exists
if not os.path.exists(sqlite_path):
    print(f"Database file does not exist: {sqlite_path}")
    print("Make sure the Flask application has been run at least once to create it.")
    sys.exit(1)

# Connect to the SQLite database directly
try:
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    print("Connected to SQLite database")
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

# Function to check if a table exists
def table_exists(table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

# Function to check if a column exists in a table
def column_exists(table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column[1] == column_name for column in columns)

# Create the areas table if it doesn't exist
if not table_exists('areas'):
    print("Creating areas table...")
    cursor.execute('''
    CREATE TABLE areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        jefe_area_id INTEGER,
        FOREIGN KEY (jefe_area_id) REFERENCES technicians(id)
    )
    ''')
    print("Created areas table")
else:
    print("Areas table already exists")

# Add area_id column to technicians table if it doesn't exist
if table_exists('technicians') and not column_exists('technicians', 'area_id'):
    print("Adding area_id column to technicians table...")
    cursor.execute('ALTER TABLE technicians ADD COLUMN area_id INTEGER')
    print("Added area_id column to technicians table")
else:
    print("Technicians table doesn't exist or area_id column already exists")

# Add area_id column to ticket_categories table if it doesn't exist
if table_exists('ticket_categories') and not column_exists('ticket_categories', 'area_id'):
    print("Adding area_id column to ticket_categories table...")
    cursor.execute('ALTER TABLE ticket_categories ADD COLUMN area_id INTEGER')
    print("Added area_id column to ticket_categories table")
else:
    print("ticket_categories table doesn't exist or area_id column already exists")

# Create technician_category_assignments table if it doesn't exist
if not table_exists('technician_category_assignments'):
    print("Creating technician_category_assignments table...")
    cursor.execute('''
    CREATE TABLE technician_category_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (technician_id) REFERENCES technicians(id),
        FOREIGN KEY (category_id) REFERENCES ticket_categories(id),
        UNIQUE(technician_id, category_id)
    )
    ''')
    print("Created technician_category_assignments table")
else:
    print("technician_category_assignments table already exists")

# Create index on areas.name
print("Creating index on areas.name...")
cursor.execute('CREATE INDEX IF NOT EXISTS ix_areas_name ON areas (name)')

# Commit the changes
conn.commit()
conn.close()

print("Migration completed successfully")
