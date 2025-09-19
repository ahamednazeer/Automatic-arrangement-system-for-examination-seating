#!/usr/bin/env python3
"""
Cleanup script to remove test data from database
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models import Student

def cleanup_all_test_data():
    """Clean up all test data"""
    print("🧹 Cleaning up all test data...")
    
    # Get all students and find test ones
    all_students = Student.get_all()
    test_prefixes = ['TEST', 'CSV', 'DELETE', 'SEARCH', 'CSE', 'IT', 'ME']
    
    deleted_count = 0
    for student in all_students:
        if any(student.student_id.startswith(prefix) for prefix in test_prefixes):
            try:
                student.delete()
                print(f"   🗑️  Deleted: {student.student_id} - {student.name}")
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️  Could not delete {student.student_id}: {e}")
    
    print(f"\n✅ Cleanup complete. Deleted {deleted_count} test records.")

if __name__ == "__main__":
    cleanup_all_test_data()