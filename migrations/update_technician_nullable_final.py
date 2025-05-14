"""
This migration script updates the Technician model to make technical_profile nullable.
Since SQLite doesn't support direct ALTER COLUMN, we'll recreate the table.
"""
from sqlalchemy import text
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our app
from app import create_app, db

def run_migration():
    print("Starting migration to make technician technical_profile nullable...")
    
    # Create the app with its context
    app = create_app()
    
    with app.app_context():
        try:
            # Get database connection
            connection = db.engine.connect()
            
            # Get the dialect
            dialect = db.engine.dialect.name
            print(f"Database dialect: {dialect}")
            
            if dialect == 'sqlite':
                print("Using SQLite-specific migration approach...")
                
                # 1. Create a new table with the desired schema
                print("Step 1: Creating new technicians table with nullable technical_profile...")
                connection.execute(text("""
                CREATE TABLE technicians_new (
                    id INTEGER PRIMARY KEY,
                    dni VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    technical_profile VARCHAR(50),
                    password_hash VARCHAR(128),
                    password_reset_token VARCHAR(100),
                    token_expiration DATETIME,
                    area_id INTEGER,
                    FOREIGN KEY (area_id) REFERENCES areas (id)
                )
                """))
                
                # 2. Copy data from old table to new table
                print("Step 2: Copying data to new table...")
                connection.execute(text("""
                INSERT INTO technicians_new 
                SELECT id, dni, name, email, technical_profile, password_hash, 
                       password_reset_token, token_expiration, area_id
                FROM technicians
                """))
                
                # 3. Drop the old table
                print("Step 3: Dropping old table...")
                connection.execute(text("DROP TABLE technicians"))
                
                # 4. Rename the new table to the original name
                print("Step 4: Renaming new table to 'technicians'...")
                connection.execute(text("ALTER TABLE technicians_new RENAME TO technicians"))
                
                # 5. Recreate indexes and constraints
                print("Step 5: Recreating unique indexes...")
                connection.execute(text("CREATE UNIQUE INDEX ix_technicians_dni ON technicians (dni)"))
                connection.execute(text("CREATE UNIQUE INDEX ix_technicians_email ON technicians (email)"))
                
                print("SQLite migration completed successfully.")
            else:
                # For PostgreSQL, MySQL, etc. that support ALTER COLUMN
                print(f"Standard migration for {dialect}...")
                connection.execute(text("ALTER TABLE technicians ALTER COLUMN technical_profile DROP NOT NULL"))
                print("Standard migration completed successfully.")
            
            connection.close()
            print("Migration completed successfully.")
            return True
            
        except Exception as e:
            print(f"Error during migration: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ Migration successfully completed.")
        sys.exit(0)
    else:
        print("❌ Migration failed.")
        sys.exit(1)
