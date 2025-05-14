import sys
import os
from datetime import datetime

def print_header():
    print("=" * 80)
    print("HELPDESK SYSTEM MIGRATION TOOL".center(80))
    print("=" * 80)
    print("This script will execute the database migration for the area management structure.")
    print("Make sure to back up your database before proceeding.\n")

def get_confirmation():
    while True:
        response = input("Are you sure you want to run this migration? [y/N]: ").lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no', ''):
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def run_migration():
    try:
        print("\nExecuting migration...")
        print("-" * 80)
        
        # Import and run the migration script
        import migrations.create_area_structure as migration
        
        # Log the migration
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\n[{now}] Area management structure migration executed."
        
        try:
            with open('logs/migration_history.log', 'a') as f:
                f.write(log_entry)
        except:
            print("Could not write to migration log file.")
        
        print("-" * 80)
        print("Migration completed successfully!")
        print("\nNext steps:")
        print("1. Assign existing technicians to areas through the admin interface")
        print("2. Assign existing categories to areas through the admin interface")
        print("3. Designate Jefes de Área for each area")
        print("\nOpen the admin panel and navigate to 'Gestionar Áreas' to start configuring.")
        
        return True
    except Exception as e:
        print(f"\nERROR: Migration failed - {str(e)}")
        return False

if __name__ == "__main__":
    print_header()
    
    if get_confirmation():
        success = run_migration()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("\nMigration cancelled by user.")
        sys.exit(0)
