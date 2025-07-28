#!/usr/bin/env python3
"""
Setup script for Examination Seating Arrangement System
"""
import os
import sys
import subprocess
import sqlite3
from datetime import datetime

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("  EXAMINATION SEATING ARRANGEMENT SYSTEM SETUP")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    directories = [
        'uploads',
        'reports',
        'backups',
        'exports',
        'logs'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Error creating directory {directory}: {e}")
            return False
    
    return True

def initialize_database():
    """Initialize the database with tables and default data"""
    print("\nInitializing database...")
    try:
        from backend.database import db_manager
        db_manager.init_database()
        print("✅ Database initialized successfully")
        
        # Add sample data
        add_sample_data()
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def add_sample_data():
    """Add sample data for testing"""
    print("\nAdding sample data...")
    try:
        from backend.models import Student, Subject, Room, Invigilator
        
        # Add sample rooms
        rooms_data = [
            {'room_id': 'R001', 'name': 'Room 001', 'rows': 10, 'cols': 10, 'capacity': 100, 'building': 'Main Block', 'floor': 1},
            {'room_id': 'R002', 'name': 'Room 002', 'rows': 8, 'cols': 12, 'capacity': 96, 'building': 'Main Block', 'floor': 1},
            {'room_id': 'R003', 'name': 'Room 003', 'rows': 12, 'cols': 8, 'capacity': 96, 'building': 'Main Block', 'floor': 2},
        ]
        
        for room_data in rooms_data:
            room = Room(**room_data)
            try:
                room.save()
                print(f"✅ Added room: {room.name}")
            except:
                pass  # Room might already exist
        
        # Add sample subjects
        subjects_data = [
            {'subject_code': 'CS101', 'subject_name': 'Introduction to Programming', 'department': 'Computer Science', 'semester': 1},
            {'subject_code': 'CS201', 'subject_name': 'Data Structures', 'department': 'Computer Science', 'semester': 3},
            {'subject_code': 'IT101', 'subject_name': 'Computer Fundamentals', 'department': 'Information Technology', 'semester': 1},
            {'subject_code': 'EC101', 'subject_name': 'Basic Electronics', 'department': 'Electronics', 'semester': 1},
            {'subject_code': 'ME101', 'subject_name': 'Engineering Mechanics', 'department': 'Mechanical', 'semester': 1},
        ]
        
        for subject_data in subjects_data:
            subject = Subject(**subject_data)
            try:
                subject.save()
                print(f"✅ Added subject: {subject.subject_name}")
            except:
                pass  # Subject might already exist
        
        # Add sample students
        students_data = [
            {'student_id': 'CS001', 'name': 'John Doe', 'department': 'Computer Science', 'semester': 1, 'email': 'john@example.com'},
            {'student_id': 'CS002', 'name': 'Jane Smith', 'department': 'Computer Science', 'semester': 1, 'email': 'jane@example.com'},
            {'student_id': 'IT001', 'name': 'Bob Johnson', 'department': 'Information Technology', 'semester': 1, 'email': 'bob@example.com'},
            {'student_id': 'EC001', 'name': 'Alice Brown', 'department': 'Electronics', 'semester': 1, 'email': 'alice@example.com'},
            {'student_id': 'ME001', 'name': 'Charlie Wilson', 'department': 'Mechanical', 'semester': 1, 'email': 'charlie@example.com'},
        ]
        
        for student_data in students_data:
            student = Student(**student_data)
            try:
                student.save()
                # Enroll in a subject
                if student.department == 'Computer Science':
                    student.enroll_subject('CS101')
                elif student.department == 'Information Technology':
                    student.enroll_subject('IT101')
                elif student.department == 'Electronics':
                    student.enroll_subject('EC101')
                elif student.department == 'Mechanical':
                    student.enroll_subject('ME101')
                print(f"✅ Added student: {student.name}")
            except:
                pass  # Student might already exist
        
        # Add sample invigilators
        invigilators_data = [
            {'staff_id': 'STAFF001', 'name': 'Dr. Professor Smith', 'department': 'Computer Science', 'email': 'prof.smith@example.com'},
            {'staff_id': 'STAFF002', 'name': 'Dr. Mary Johnson', 'department': 'Information Technology', 'email': 'mary.j@example.com'},
            {'staff_id': 'STAFF003', 'name': 'Dr. Robert Brown', 'department': 'Electronics', 'email': 'robert.b@example.com'},
        ]
        
        for invigilator_data in invigilators_data:
            invigilator = Invigilator(**invigilator_data)
            try:
                invigilator.save()
                print(f"✅ Added invigilator: {invigilator.name}")
            except:
                pass  # Invigilator might already exist
        
        print("✅ Sample data added successfully")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not add sample data: {e}")

def create_config_file():
    """Create configuration file"""
    print("\nCreating configuration file...")
    config_content = f"""# Examination Seating System Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Application Settings
DEBUG = True
SECRET_KEY = 'change-this-in-production-{datetime.now().strftime("%Y%m%d")}'

# Database Settings
DATABASE_URL = 'sqlite:///exam_system.db'

# Upload Settings
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Report Settings
REPORTS_FOLDER = 'reports'
EXPORTS_FOLDER = 'exports'

# Security Settings
SESSION_TIMEOUT = 3600  # 1 hour
PASSWORD_MIN_LENGTH = 6

# Email Settings (for notifications)
MAIL_SERVER = 'localhost'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''

# Pagination
ITEMS_PER_PAGE = 20

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/app.log'
"""
    
    try:
        with open('config.py', 'w') as f:
            f.write(config_content)
        print("✅ Configuration file created")
        return True
    except Exception as e:
        print(f"❌ Error creating configuration file: {e}")
        return False

def create_run_script():
    """Create run script for easy startup"""
    print("\nCreating run script...")
    
    # For Unix/Linux/Mac
    run_script_unix = """#!/bin/bash
# Run script for Examination Seating System

echo "Starting Examination Seating System..."
echo "Access the application at: http://localhost:5000"
echo "Default login: admin@exam.com / admin123"
echo ""

python app_modular.py
"""
    
    # For Windows
    run_script_windows = """@echo off
REM Run script for Examination Seating System

echo Starting Examination Seating System...
echo Access the application at: http://localhost:5000
echo Default login: admin@exam.com / admin123
echo.

python app_modular.py
pause
"""
    
    try:
        # Create Unix script
        with open('run.sh', 'w') as f:
            f.write(run_script_unix)
        os.chmod('run.sh', 0o755)  # Make executable
        
        # Create Windows script
        with open('run.bat', 'w') as f:
            f.write(run_script_windows)
        
        print("✅ Run scripts created (run.sh for Unix/Linux/Mac, run.bat for Windows)")
        return True
    except Exception as e:
        print(f"❌ Error creating run scripts: {e}")
        return False

def print_completion_message():
    """Print setup completion message"""
    print("\n" + "=" * 60)
    print("  SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("🎉 The Examination Seating System is ready to use!")
    print()
    print("📋 Next Steps:")
    print("   1. Run the application:")
    print("      • Unix/Linux/Mac: ./run.sh")
    print("      • Windows: run.bat")
    print("      • Manual: python app_modular.py")
    print()
    print("   2. Open your browser and go to: http://localhost:5000")
    print()
    print("   3. Login with default credentials:")
    print("      • Email: admin@exam.com")
    print("      • Password: admin123")
    print()
    print("   4. Change the default password after first login!")
    print()
    print("📚 Documentation:")
    print("   • README.md - Complete documentation")
    print("   • config.py - Configuration settings")
    print()
    print("🆘 Support:")
    print("   • Check README.md for troubleshooting")
    print("   • Review logs in logs/ directory")
    print()
    print("⚠️  Security Note:")
    print("   • Change the SECRET_KEY in config.py for production")
    print("   • Update default admin password")
    print("   • Configure proper database for production use")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Setup failed during directory creation")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("\n❌ Setup failed during database initialization")
        sys.exit(1)
    
    # Create configuration file
    if not create_config_file():
        print("\n❌ Setup failed during configuration file creation")
        sys.exit(1)
    
    # Create run scripts
    if not create_run_script():
        print("\n❌ Setup failed during run script creation")
        sys.exit(1)
    
    # Print completion message
    print_completion_message()

if __name__ == "__main__":
    main()