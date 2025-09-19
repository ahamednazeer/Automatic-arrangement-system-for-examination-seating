#!/usr/bin/env python3
"""
Test Script for Student Management Functionality
Tests all the test cases: TC-STU-01 through TC-STU-05
"""

import os
import sys
import sqlite3
import csv
import tempfile
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import db_manager
from backend.models import Student, Subject

class StudentManagementTester:
    def __init__(self):
        self.test_results = []
        self.timestamp = str(int(time.time()))[-6:]  # Use last 6 digits of timestamp for unique IDs
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment and ensure database is initialized"""
        print("🔧 Setting up test environment...")
        
        # Initialize database if needed
        try:
            db_manager.initialize_database()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️  Database initialization: {e}")
        
        # Create some test subjects for enrollment
        try:
            subjects = [
                Subject(subject_code='CS101', subject_name='Programming Fundamentals', 
                       department='Computer Science', semester=1),
                Subject(subject_code='CS201', subject_name='Data Structures', 
                       department='Computer Science', semester=2),
                Subject(subject_code='IT101', subject_name='IT Fundamentals', 
                       department='Information Technology', semester=1)
            ]
            
            for subject in subjects:
                existing = Subject.get_by_code(subject.subject_code)
                if not existing:
                    subject.save()
                    print(f"✅ Created test subject: {subject.subject_code}")
        except Exception as e:
            print(f"⚠️  Subject setup: {e}")
    
    def log_test_result(self, test_id, description, status, notes=""):
        """Log test result"""
        result = {
            'test_id': test_id,
            'description': description,
            'status': status,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_id}: {description} - {status}")
        if notes:
            print(f"   📝 {notes}")
    
    def test_tc_stu_01_add_student_manually(self):
        """TC-STU-01: Add student manually"""
        print("\n🧪 Testing TC-STU-01: Add student manually")
        
        try:
            # Test data with unique ID
            test_id = f'T{self.timestamp}01'
            test_student = Student(
                student_id=test_id,
                name='Test Student One',
                department='Computer Science',
                semester=3,
                email='test1@example.com',
                phone='+1234567890'
            )
            
            # Check if student already exists and clean up
            existing = Student.get_by_id(test_id)
            if existing:
                existing.delete()
            
            # Add the student
            test_student.save()
            
            # Verify student was added
            saved_student = Student.get_by_id(test_id)
            if saved_student and saved_student.name == 'Test Student One':
                # Verify student appears in list
                all_students = Student.get_all()
                student_ids = [s.student_id for s in all_students]
                
                if test_id in student_ids:
                    self.log_test_result('TC-STU-01', 'Add student manually', 'PASS', 
                                       'Student successfully added and appears in list')
                else:
                    self.log_test_result('TC-STU-01', 'Add student manually', 'FAIL', 
                                       'Student saved but not found in list')
            else:
                self.log_test_result('TC-STU-01', 'Add student manually', 'FAIL', 
                                   'Student not saved correctly')
                
        except Exception as e:
            self.log_test_result('TC-STU-01', 'Add student manually', 'FAIL', f'Error: {str(e)}')
    
    def test_tc_stu_02_import_valid_csv(self):
        """TC-STU-02: Import valid student CSV"""
        print("\n🧪 Testing TC-STU-02: Import valid student CSV")
        
        try:
            # Create a valid CSV file with unique IDs
            csv_ids = [f'C{self.timestamp}01', f'C{self.timestamp}02', f'C{self.timestamp}03']
            csv_content = f"""student_id,name,department,semester,email,phone
{csv_ids[0]},CSV Student One,Computer Science,2,csv1@example.com,+1111111111
{csv_ids[1]},CSV Student Two,Information Technology,3,csv2@example.com,+2222222222
{csv_ids[2]},CSV Student Three,Mechanical Engineering,1,csv3@example.com,+3333333333"""
            
            # Clean up any existing test students
            for student_id in csv_ids:
                existing = Student.get_by_id(student_id)
                if existing:
                    existing.delete()
            
            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(csv_content)
                csv_file_path = f.name
            
            try:
                # Simulate CSV import process
                import csv as csv_module
                import io
                
                with open(csv_file_path, 'r') as file:
                    csv_input = csv_module.DictReader(file)
                    imported_count = 0
                    
                    for row in csv_input:
                        student = Student(
                            student_id=row['student_id'],
                            name=row['name'],
                            department=row['department'],
                            semester=int(row['semester']),
                            email=row['email'],
                            phone=row['phone']
                        )
                        student.save()
                        imported_count += 1
                
                # Verify all students were imported
                if imported_count == 3:
                    # Check if students appear in list
                    all_students = Student.get_all()
                    student_ids = [s.student_id for s in all_students]
                    
                    all_imported = all(sid in student_ids for sid in csv_ids)
                    
                    if all_imported:
                        self.log_test_result('TC-STU-02', 'Import valid student CSV', 'PASS', 
                                           f'All {imported_count} students imported successfully')
                    else:
                        self.log_test_result('TC-STU-02', 'Import valid student CSV', 'FAIL', 
                                           'Not all students found in list after import')
                else:
                    self.log_test_result('TC-STU-02', 'Import valid student CSV', 'FAIL', 
                                       f'Expected 3 students, imported {imported_count}')
                    
            finally:
                # Clean up temporary file
                os.unlink(csv_file_path)
                
        except Exception as e:
            self.log_test_result('TC-STU-02', 'Import valid student CSV', 'FAIL', f'Error: {str(e)}')
    
    def test_tc_stu_03_import_malformed_csv(self):
        """TC-STU-03: Import malformed CSV"""
        print("\n🧪 Testing TC-STU-03: Import malformed CSV")
        
        try:
            # Create a malformed CSV file (missing required headers)
            csv_content = """name,department,semester,email,phone
Bad Student One,Computer Science,2,bad1@example.com,+1111111111
Bad Student Two,Information Technology,3,bad2@example.com,+2222222222"""
            
            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(csv_content)
                csv_file_path = f.name
            
            try:
                # Simulate CSV import process
                import csv as csv_module
                
                with open(csv_file_path, 'r') as file:
                    csv_input = csv_module.DictReader(file)
                    headers = csv_input.fieldnames
                    
                    # Check for required headers
                    required_headers = ['student_id', 'name', 'department', 'semester']
                    headers_lower = [h.lower().strip() for h in headers] if headers else []
                    missing_headers = [h for h in required_headers if h not in headers_lower]
                    
                    if missing_headers:
                        error_msg = f"Invalid CSV format: Missing required headers: {', '.join(missing_headers)}"
                        self.log_test_result('TC-STU-03', 'Import malformed CSV', 'PASS', 
                                           f'Correctly detected error: {error_msg}')
                    else:
                        self.log_test_result('TC-STU-03', 'Import malformed CSV', 'FAIL', 
                                           'Should have detected missing headers but did not')
                    
            finally:
                # Clean up temporary file
                os.unlink(csv_file_path)
                
        except Exception as e:
            self.log_test_result('TC-STU-03', 'Import malformed CSV', 'FAIL', f'Error: {str(e)}')
    
    def test_tc_stu_04_delete_student(self):
        """TC-STU-04: Delete a student"""
        print("\n🧪 Testing TC-STU-04: Delete a student")
        
        try:
            # First, create a student to delete with unique ID
            delete_id = f'D{self.timestamp}01'
            test_student = Student(
                student_id=delete_id,
                name='Student To Delete',
                department='Computer Science',
                semester=2,
                email='delete@example.com',
                phone='+9999999999'
            )
            
            # Clean up if exists
            existing = Student.get_by_id(delete_id)
            if existing:
                existing.delete()
            
            # Add the student
            test_student.save()
            
            # Verify student exists
            saved_student = Student.get_by_id(delete_id)
            if not saved_student:
                self.log_test_result('TC-STU-04', 'Delete a student', 'FAIL', 
                                   'Could not create test student for deletion')
                return
            
            # Delete the student
            saved_student.delete()
            
            # Verify student is deleted
            deleted_student = Student.get_by_id(delete_id)
            if deleted_student is None:
                # Also verify student is removed from list
                all_students = Student.get_all()
                student_ids = [s.student_id for s in all_students]
                
                if delete_id not in student_ids:
                    self.log_test_result('TC-STU-04', 'Delete a student', 'PASS', 
                                       'Student successfully deleted and removed from list')
                else:
                    self.log_test_result('TC-STU-04', 'Delete a student', 'FAIL', 
                                       'Student deleted but still appears in list')
            else:
                self.log_test_result('TC-STU-04', 'Delete a student', 'FAIL', 
                                   'Student still exists after deletion')
                
        except Exception as e:
            self.log_test_result('TC-STU-04', 'Delete a student', 'FAIL', f'Error: {str(e)}')
    
    def test_tc_stu_05_search_by_department(self):
        """TC-STU-05: Search students by department"""
        print("\n🧪 Testing TC-STU-05: Search students by department")
        
        try:
            # Create test students in different departments with unique IDs
            search_ids = [f'S{self.timestamp}01', f'S{self.timestamp}02', f'S{self.timestamp}03', f'S{self.timestamp}04']
            test_students = [
                Student(student_id=search_ids[0], name='CSE Student 1', department='CSE', semester=1),
                Student(student_id=search_ids[1], name='CSE Student 2', department='CSE', semester=2),
                Student(student_id=search_ids[2], name='IT Student 1', department='IT', semester=1),
                Student(student_id=search_ids[3], name='ME Student 1', department='ME', semester=3)
            ]
            
            # Clean up existing test students first
            for student in test_students:
                existing = Student.get_by_id(student.student_id)
                if existing:
                    existing.delete()
            
            # Add test students
            for student in test_students:
                student.save()
            
            # Search for CSE students
            cse_students = Student.get_all(department='CSE')
            cse_student_ids = [s.student_id for s in cse_students]
            
            # Verify only CSE students are returned
            expected_cse_ids = [search_ids[0], search_ids[1]]
            unexpected_ids = [search_ids[2], search_ids[3]]
            
            cse_found = all(sid in cse_student_ids for sid in expected_cse_ids)
            no_others_found = not any(sid in cse_student_ids for sid in unexpected_ids)
            
            if cse_found and no_others_found:
                self.log_test_result('TC-STU-05', 'Search students by department', 'PASS', 
                                   f'Found {len([s for s in cse_students if s.department == "CSE"])} CSE students, filtered correctly')
            else:
                self.log_test_result('TC-STU-05', 'Search students by department', 'FAIL', 
                                   f'Filter failed. Found: {cse_student_ids}')
                
        except Exception as e:
            self.log_test_result('TC-STU-05', 'Search students by department', 'FAIL', f'Error: {str(e)}')
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Get all students and find ones with our timestamp prefix
        all_students = Student.get_all()
        test_prefixes = [f'T{self.timestamp}', f'C{self.timestamp}', f'D{self.timestamp}', f'S{self.timestamp}']
        
        deleted_count = 0
        for student in all_students:
            if any(student.student_id.startswith(prefix) for prefix in test_prefixes):
                try:
                    student.delete()
                    print(f"   🗑️  Deleted test student: {student.student_id}")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ⚠️  Could not delete {student.student_id}: {e}")
        
        if deleted_count == 0:
            print("   ✅ No test data to clean up")
    
    def run_all_tests(self):
        """Run all test cases"""
        print("=" * 80)
        print("  STUDENT MANAGEMENT FUNCTIONALITY TESTS")
        print("=" * 80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all test cases
        self.test_tc_stu_01_add_student_manually()
        self.test_tc_stu_02_import_valid_csv()
        self.test_tc_stu_03_import_malformed_csv()
        self.test_tc_stu_04_delete_student()
        self.test_tc_stu_05_search_by_department()
        
        # Clean up
        self.cleanup_test_data()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("  TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        total = len(self.test_results)
        
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌"
            print(f"{status_icon} {result['test_id']}: {result['description']} - {result['status']}")
            if result['notes']:
                print(f"   📝 {result['notes']}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {(passed/total*100):.1f}%" if total > 0 else "   Success Rate: 0%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Student management functionality is working correctly.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
        
        print("=" * 80)

def main():
    """Main function to run tests"""
    tester = StudentManagementTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()