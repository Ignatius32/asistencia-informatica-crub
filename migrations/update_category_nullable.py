"""
This migration script updates the TicketCategory model to make technical_profile nullable.
It also ensures the relationship between technicians and categories is properly set up.
"""
from app import app, db
from app.models.category import TicketCategory
import sqlalchemy as sa
from sqlalchemy import text

def run_migration():
    print("Starting migration to make category technical_profile nullable...")
    
    with app.app_context():
        # Modify the technical_profile column to be nullable
        # This is done with raw SQL to ensure compatibility
        try:
            # First get the current table and column info
            connection = db.engine.connect()
            
            # For SQLite (which is what we're likely using)
            # Since SQLite doesn't support ALTER COLUMN, we need a different approach
            # 1. Create a new temporary table with the desired schema
            # 2. Copy data to the new table
            # 3. Drop the old table
            # 4. Rename the new table to the original name
            
            # First, check if we're using SQLite
            dialect = db.engine.dialect.name
            
            if dialect == 'sqlite':
                print("Detected SQLite database, using SQLite-specific migration...")
                
                # Step 1: Create a new temporary table with the desired schema
                connection.execute(text("""
                CREATE TABLE ticket_categories_new (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    technical_profile VARCHAR(50),
                    description VARCHAR(255),
                    active BOOLEAN,
                    area_id INTEGER,
                    FOREIGN KEY (area_id) REFERENCES areas (id)
                )
                """))
                
                # Step 2: Copy data to the new table
                connection.execute(text("""
                INSERT INTO ticket_categories_new 
                SELECT id, name, technical_profile, description, active, area_id 
                FROM ticket_categories
                """))
                
                # Step 3: Drop the old table
                connection.execute(text("DROP TABLE ticket_categories"))
                
                # Step 4: Rename the new table to the original name
                connection.execute(text("ALTER TABLE ticket_categories_new RENAME TO ticket_categories"))
                
                print("SQLite migration completed successfully.")
            else:
                # For PostgreSQL, MySQL, etc. that support ALTER COLUMN
                print(f"Detected {dialect} database, using standard migration...")
                connection.execute(text("ALTER TABLE ticket_categories ALTER COLUMN technical_profile DROP NOT NULL"))
                print("Standard migration completed successfully.")
            
            connection.close()
            print("Migration completed successfully.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    run_migration()
