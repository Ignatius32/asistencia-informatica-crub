"""
This migration script updates the Technician model to make technical_profile nullable.
Since SQLite doesn't support direct ALTER COLUMN, we'll recreate the table.
This version is more robust to handle partial previous executions and includes enhanced verification.
"""
from sqlalchemy import text, inspect
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our app
from app import create_app, db

def run_migration():
    print("Starting migration to make technician technical_profile nullable...")
    
    app = create_app()
    
    with app.app_context():
        try:
            engine = db.engine
            with engine.connect() as connection:
                trans = connection.begin()
                try:
                    dialect = engine.dialect.name
                    print(f"Database dialect: {dialect}")
                    
                    # Initial inspector
                    inspector = inspect(engine)
                    
                    if dialect == 'sqlite':
                        print("Using SQLite-specific migration approach...")

                        # 0. Drop the temporary table if it exists from a previous failed run
                        if 'technicians_new' in inspector.get_table_names():
                            print("Step 0: Dropping existing 'technicians_new' table...")
                            connection.execute(text("DROP TABLE IF EXISTS technicians_new"))
                        
                        # 1. Create a new table with the desired schema (technical_profile nullable)
                        print("Step 1: Creating new technicians table ('technicians_new') with nullable technical_profile...")
                        connection.execute(text("""
                        CREATE TABLE technicians_new (
                            id INTEGER PRIMARY KEY,
                            dni VARCHAR(20) NOT NULL UNIQUE,
                            name VARCHAR(100) NOT NULL,
                            email VARCHAR(100) NOT NULL UNIQUE,
                            technical_profile VARCHAR(50) NULL, -- Explicitly NULL
                            password_hash VARCHAR(128),
                            password_reset_token VARCHAR(100) UNIQUE,
                            token_expiration DATETIME,
                            area_id INTEGER,
                            FOREIGN KEY (area_id) REFERENCES areas (id)
                        )
                        """))
                        
                        # 2. Copy data from old table to new table
                        if 'technicians' in inspector.get_table_names(): # Use initial inspector for old table check
                            print("Step 2: Copying data from 'technicians' to 'technicians_new'...")
                            connection.execute(text(f"""
                            INSERT INTO technicians_new (id, dni, name, email, technical_profile, password_hash, 
                                   password_reset_token, token_expiration, area_id)
                            SELECT id, dni, name, email, technical_profile, password_hash, 
                                   password_reset_token, token_expiration, area_id
                            FROM technicians
                            """))
                        else:
                            print("Old 'technicians' table not found. Skipping data copy.")

                        # 3. Drop the old table if it exists
                        if 'technicians' in inspector.get_table_names(): # Use initial inspector for old table check
                            print("Step 3: Dropping old 'technicians' table...")
                            connection.execute(text("DROP TABLE IF EXISTS technicians"))
                        
                        # 4. Rename the new table to the original name
                        print("Step 4: Renaming 'technicians_new' to 'technicians'...")
                        connection.execute(text("ALTER TABLE technicians_new RENAME TO technicians"))
                        
                        # 5. Recreate indexes (UNIQUE constraints are part of CREATE TABLE)
                        print("Step 5: Recreating unique constraints/indexes (handled by CREATE TABLE)...")
                        
                        # Verify the schema of the new technicians table
                        print("Verifying schema of the new 'technicians' table...")
                        
                        # Re-initialize inspector to get the freshest schema after DDL changes
                        current_inspector = inspect(engine) # Or inspect(connection)
                        
                        new_columns = current_inspector.get_columns('technicians')
                        technical_profile_column_inspector_info = next((col for col in new_columns if col['name'] == 'technical_profile'), None)
                        
                        # Cross-check with PRAGMA table_info
                        pragma_info_cursor = connection.execute(text("PRAGMA table_info(technicians)"))
                        pragma_columns = pragma_info_cursor.fetchall()
                        print(f"Debug: PRAGMA table_info(technicians) result: {pragma_columns}")
                        
                        pragma_technical_profile_notnull = -1 # Default to an invalid state
                        for col_pragma in pragma_columns:
                            if col_pragma[1] == 'technical_profile': # name is at index 1
                                # 'notnull' is at index 3 (0 for false/nullable, 1 for true/NOT NULL)
                                pragma_technical_profile_notnull = col_pragma[3]
                                print(f"Debug: PRAGMA info for technical_profile: name={col_pragma[1]}, type={col_pragma[2]}, notnull={col_pragma[3]} (0=nullable, 1=NOT NULL)")
                                break
                        
                        is_nullable_by_inspector = technical_profile_column_inspector_info and technical_profile_column_inspector_info['nullable']
                        is_nullable_by_pragma = (pragma_technical_profile_notnull == 0)

                        if technical_profile_column_inspector_info and is_nullable_by_inspector:
                            print("✅ 'technical_profile' is now nullable (verified by SQLAlchemy Inspector).")
                            if not is_nullable_by_pragma :
                                print("⚠️ Warning: PRAGMA table_info disagrees with Inspector or did not find column properly.")
                        elif is_nullable_by_pragma:
                             print("✅ 'technical_profile' is now nullable (verified by PRAGMA table_info).")
                             if not technical_profile_column_inspector_info:
                                 print("⚠️ Warning: SQLAlchemy Inspector did not find the column, but PRAGMA did.")
                             elif not is_nullable_by_inspector:
                                 print("⚠️ Warning: SQLAlchemy Inspector reports NOT nullable, but PRAGMA reports nullable.")
                        else:
                            print("❌ Error: 'technical_profile' is NOT nullable after migration or column not found (checked by Inspector and PRAGMA).")
                            if technical_profile_column_inspector_info:
                                print(f"Debug (Inspector): Found column 'technical_profile'. Nullable attribute: {technical_profile_column_inspector_info['nullable']}.")
                                print(f"Debug (Inspector): Full column info: {technical_profile_column_inspector_info}")
                            else:
                                print("Debug (Inspector): Column 'technical_profile' was NOT found by SQLAlchemy Inspector.")
                            
                            if pragma_technical_profile_notnull != -1:
                                 print(f"Debug (PRAGMA): 'technical_profile' notnull flag: {pragma_technical_profile_notnull} (0 means nullable, 1 means NOT NULL).")
                            else:
                                print("Debug (PRAGMA): Column 'technical_profile' was NOT found by PRAGMA table_info.")
                            raise Exception("Migration failed to make technical_profile nullable. Check debug output.")

                        print("SQLite migration steps completed successfully.")
                    else:
                        # For PostgreSQL, MySQL, etc. that support ALTER COLUMN
                        print(f"Standard migration for {dialect}...")
                        # Check if column is already nullable
                        inspector = inspect(engine) # Ensure inspector is fresh here too
                        columns = inspector.get_columns('technicians')
                        technical_profile_col = next((col for col in columns if col['name'] == 'technical_profile'), None)
                        
                        if technical_profile_col and not technical_profile_col['nullable']:
                            print("Altering 'technical_profile' to be nullable...")
                            if dialect == 'postgresql':
                                connection.execute(text("ALTER TABLE technicians ALTER COLUMN technical_profile DROP NOT NULL"))
                            elif dialect == 'mysql':
                                connection.execute(text("ALTER TABLE technicians MODIFY COLUMN technical_profile VARCHAR(50) NULL"))
                            else:
                                connection.execute(text("ALTER TABLE technicians ALTER COLUMN technical_profile SET NULL"))
                            print("'technical_profile' column altered successfully.")
                        elif technical_profile_col and technical_profile_col['nullable']:
                            print("'technical_profile' column is already nullable.")
                        else:
                            print("Warning: 'technical_profile' column not found. Cannot alter.")
                        print("Standard migration completed successfully.")
                    
                    trans.commit()
                    print("Migration transaction committed successfully.")
                    return True
                
                except Exception as e:
                    print(f"Error during migration transaction: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        trans.rollback()
                        print("Migration transaction rolled back.")
                    except Exception as rb_e:
                        print(f"Error during rollback: {rb_e}")
                    return False
            
        except Exception as e:
            print(f"Error establishing database connection or app context: {e}")
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
