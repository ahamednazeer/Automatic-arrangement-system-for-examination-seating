#!/usr/bin/env python3
"""
Check what's in the database
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models import Student

def check_database():
    """Check what's in the database"""
    print("🔍 Checking database contents...")
    
    try:
        all_students = Student.get_all()
        print(f"Total students in database: {len(all_students)}")
        
        for student in all_students:
            print(f"   - {student.student_id}: {student.name} ({student.department})")
            
        # Try to add a test student to see what happens
        print("\n🧪 Testing student creation...")
        test_student = Student(
            student_id='DEBUG001',
            name='Debug Student',
            department='Debug',
            semester=1
        )
        
        # Check if it exists first
        existing = Student.get_by_id('DEBUG001')
        if existing:
            print(f"   Student DEBUG001 already exists: {existing.name}")
            existing.delete()
            print("   Deleted existing student")
        
        test_student.save()
        print("   ✅ Successfully created test student")
        
        # Clean up
        test_student.delete()
        print("   ✅ Successfully deleted test student")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()