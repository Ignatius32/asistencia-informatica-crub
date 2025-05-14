"""
This script runs all migrations in the correct order to ensure database consistency.
"""
import os
import sys
import importlib.util

def import_module_from_file(module_name, file_path):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_migrations():
    """Run all migration scripts in the proper order."""
    # Path to migrations folder
    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define migrations to run in order
    migration_files = [
        "update_category_nullable.py",
        "update_technician_nullable_final.py"
    ]
    
    # Run each migration
    for migration_file in migration_files:
        migration_path = os.path.join(migrations_dir, migration_file)
        
        if not os.path.exists(migration_path):
            print(f"❌ Migration file not found: {migration_file}")
            continue
        
        print(f"Running migration: {migration_file}")
        
        try:
            # Import and run the migration
            migration_module = import_module_from_file(
                f"migration_{migration_file.replace('.py', '')}", 
                migration_path
            )
            
            if hasattr(migration_module, "run_migration"):
                result = migration_module.run_migration()
                if result:
                    print(f"✅ Successfully completed migration: {migration_file}")
                else:
                    print(f"❌ Failed to run migration: {migration_file}")
                    return False
            else:
                print(f"❌ No run_migration function found in {migration_file}")
                return False
                
        except Exception as e:
            print(f"❌ Error running migration {migration_file}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    print("Starting database migrations...")
    success = run_migrations()
    
    if success:
        print("✅ All migrations completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration process failed. Database may be in an inconsistent state.")
        sys.exit(1)
