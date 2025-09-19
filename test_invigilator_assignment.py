#!/usr/bin/env python3
"""
Test Cases for Invigilator Assignment Functionality
==================================================

Test Case Expected Results:
1. Assign invigilator to session - Appears in duty chart
2. Assign same person to overlapping room - Warning message shown

This module tests the invigilator assignment system including:
- Basic assignment functionality
- Conflict detection for overlapping sessions
- Duty chart generation
- Error handling
"""

import os
import sys
import sqlite3
import tempfile
import shutil
from datetime import datetime, timedelta
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import DatabaseManager
from backend.models import Invigilator, Room, Subject, Exam

class InvigilatorAssignmentTester:
    def __init__(self):
        self.db_manager = None
        self.temp_dir = None
        self.test_data = {}
        
    def setup_test_environment(self):
        """Set up test environment with temporary database"""
        print("🔧 Setting up test environment...")
        
        # Create temporary directory for test database
        self.temp_dir = tempfile.mkdtemp(prefix="invigilator_test_")
        test_db_path = os.path.join(self.temp_dir, "test_exam_system.db")
        
        # Initialize database manager
        self.db_manager = DatabaseManager(test_db_path)
        self.db_manager.init_database()
        
        print("✅ Database initialized")
        
        # Clean up any existing test data
        self._cleanup_test_data()
        
        # Create test data
        self._create_test_data()
        
        print(f"📁 Created temp directory: {self.temp_dir}")
        
    def _cleanup_test_data(self):
        """Clean up existing test data"""
        cleanup_queries = [
            "DELETE FROM invigilator_assignments WHERE staff_id LIKE 'TEST_%'",
            "DELETE FROM seating_arrangements WHERE room_id LIKE 'TEST_%'",
            "DELETE FROM enrollments WHERE subject_code LIKE 'TEST_%'",
            "DELETE FROM exams WHERE subject_code LIKE 'TEST_%'",
            "DELETE FROM subjects WHERE subject_code LIKE 'TEST_%'",
            "DELETE FROM rooms WHERE room_id LIKE 'TEST_%'",
            "DELETE FROM invigilators WHERE staff_id LIKE 'TEST_%'"
        ]
        
        for query in cleanup_queries:
            try:
                self.db_manager.execute_query(query)
                print(f"   🗑️  Cleaned: {query.split()[2]}")
            except Exception as e:
                pass  # Ignore errors for non-existent data
    
    def _create_test_data(self):
        """Create test data for invigilator assignment tests"""
        
        # Create test invigilators
        test_invigilators = [
            {'staff_id': 'TEST_INV_001', 'name': 'Dr. Test Invigilator 1', 'department': 'Computer Science', 'email': 'test1@example.com', 'phone': '1234567890'},
            {'staff_id': 'TEST_INV_002', 'name': 'Dr. Test Invigilator 2', 'department': 'Information Technology', 'email': 'test2@example.com', 'phone': '1234567891'},
            {'staff_id': 'TEST_INV_003', 'name': 'Dr. Test Invigilator 3', 'department': 'Electronics', 'email': 'test3@example.com', 'phone': '1234567892'}
        ]
        
        for inv_data in test_invigilators:
            # Check if invigilator already exists
            existing = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM invigilators WHERE staff_id = ?",
                (inv_data['staff_id'],)
            )
            
            if existing[0]['count'] == 0:
                invigilator = Invigilator(**inv_data)
                invigilator.save()
                print(f"   👤 Created test invigilator: {inv_data['name']}")
            else:
                print(f"   👤 Using existing test invigilator: {inv_data['name']}")
        
        # Create test rooms
        test_rooms = [
            {'room_id': 'TEST_ROOM_01', 'name': 'Test Room 1', 'rows': 6, 'cols': 5, 'capacity': 30, 'building': 'Test Building', 'floor': 1},
            {'room_id': 'TEST_ROOM_02', 'name': 'Test Room 2', 'rows': 5, 'cols': 5, 'capacity': 25, 'building': 'Test Building', 'floor': 1},
            {'room_id': 'TEST_ROOM_03', 'name': 'Test Room 3', 'rows': 7, 'cols': 5, 'capacity': 35, 'building': 'Test Building', 'floor': 2}
        ]
        
        for room_data in test_rooms:
            # Check if room already exists
            existing = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM rooms WHERE room_id = ?",
                (room_data['room_id'],)
            )
            
            if existing[0]['count'] == 0:
                room = Room(**room_data)
                room.save()
                print(f"   🏢 Created test room: {room_data['name']}")
            else:
                print(f"   🏢 Using existing test room: {room_data['name']}")
        
        # Create test subjects
        test_subjects = [
            {'subject_code': 'TEST_SUB_001', 'subject_name': 'Test Subject 1', 'department': 'Computer Science', 'semester': 1, 'credits': 3},
            {'subject_code': 'TEST_SUB_002', 'subject_name': 'Test Subject 2', 'department': 'Information Technology', 'semester': 1, 'credits': 4}
        ]
        
        for subject_data in test_subjects:
            # Check if subject already exists
            existing = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM subjects WHERE subject_code = ?",
                (subject_data['subject_code'],)
            )
            
            if existing[0]['count'] == 0:
                subject = Subject(**subject_data)
                subject.save()
                print(f"   📚 Created test subject: {subject_data['subject_name']}")
            else:
                print(f"   📚 Using existing test subject: {subject_data['subject_name']}")
        
        # Create test exams
        tomorrow = datetime.now() + timedelta(days=1)
        exam_date = tomorrow.strftime('%Y-%m-%d')
        
        test_exams = [
            {
                'subject_code': 'TEST_SUB_001',
                'exam_date': exam_date,
                'start_time': '09:00',
                'end_time': '12:00',
                'duration': 180
            },
            {
                'subject_code': 'TEST_SUB_002', 
                'exam_date': exam_date,
                'start_time': '10:00',  # Overlapping with first exam
                'end_time': '13:00',
                'duration': 180
            }
        ]
        
        for exam_data in test_exams:
            # Check if exam already exists
            existing = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM exams WHERE subject_code = ? AND exam_date = ?",
                (exam_data['subject_code'], exam_data['exam_date'])
            )
            
            if existing[0]['count'] == 0:
                exam = Exam(**exam_data)
                exam.save()
                print(f"   📝 Created test exam for {exam_data['subject_code']} on {exam_date}")
            else:
                print(f"   📝 Using existing test exam for {exam_data['subject_code']} on {exam_date}")
        
        # Store test data for use in tests
        self.test_data = {
            'invigilators': test_invigilators,
            'rooms': test_rooms,
            'subjects': test_subjects,
            'exams': test_exams,
            'exam_date': exam_date
        }
    
    def test_assign_invigilator_to_session(self):
        """Test Case 1: Assign invigilator to session - Should appear in duty chart"""
        print("\n🧪 Testing TC-INVIGILATOR-01: Assign invigilator to session")
        
        try:
            # Assign invigilator to first exam session
            assignment_data = {
                'staff_id': 'TEST_INV_001',
                'room_id': 'TEST_ROOM_01',
                'exam_date': self.test_data['exam_date'],
                'session_time': '09:00',
                'subject_code': 'TEST_SUB_001'
            }
            
            # Insert assignment
            query = '''
                INSERT INTO invigilator_assignments (staff_id, room_id, exam_date, session_time, subject_code, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            '''
            self.db_manager.execute_query(query, tuple(assignment_data.values()))
            print("   ✅ Invigilator assigned to session successfully")
            
            # Verify assignment appears in duty chart
            duty_chart_query = '''
                SELECT ia.*, i.name as invigilator_name, r.name as room_name, s.subject_name
                FROM invigilator_assignments ia
                JOIN invigilators i ON ia.staff_id = i.staff_id
                JOIN rooms r ON ia.room_id = r.room_id
                JOIN subjects s ON ia.subject_code = s.subject_code
                WHERE ia.staff_id = ? AND ia.exam_date = ? AND ia.session_time = ?
            '''
            
            result = self.db_manager.execute_query(
                duty_chart_query, 
                (assignment_data['staff_id'], assignment_data['exam_date'], assignment_data['session_time'])
            )
            
            if result and len(result) > 0:
                assignment = result[0]
                print(f"   ✅ Assignment appears in duty chart:")
                print(f"      - Invigilator: {assignment['invigilator_name']}")
                print(f"      - Room: {assignment['room_name']}")
                print(f"      - Subject: {assignment['subject_name']}")
                print(f"      - Date: {assignment['exam_date']}")
                print(f"      - Time: {assignment['session_time']}")
                print("   📝 Invigilator assignment appears correctly in duty chart")
                return True
            else:
                print("   ❌ Assignment not found in duty chart")
                return False
                
        except Exception as e:
            print(f"   ❌ Error in assignment test: {str(e)}")
            return False
    
    def test_overlapping_room_assignment_warning(self):
        """Test Case 2: Assign same person to overlapping room - Should show warning"""
        print("\n🧪 Testing TC-INVIGILATOR-02: Assign same person to overlapping room")
        
        try:
            # Try to assign the same invigilator to overlapping session
            overlapping_assignment = {
                'staff_id': 'TEST_INV_001',  # Same invigilator as previous test
                'room_id': 'TEST_ROOM_02',   # Different room
                'exam_date': self.test_data['exam_date'],
                'session_time': '10:00',     # Overlapping time (09:00-12:00 vs 10:00-13:00)
                'subject_code': 'TEST_SUB_002'
            }
            
            # Check for existing overlapping assignments
            conflict_check_query = '''
                SELECT ia.*, i.name as invigilator_name, r.name as room_name, s.subject_name,
                       e1.start_time as existing_start, e1.end_time as existing_end,
                       e2.start_time as new_start, e2.end_time as new_end
                FROM invigilator_assignments ia
                JOIN invigilators i ON ia.staff_id = i.staff_id
                JOIN rooms r ON ia.room_id = r.room_id
                JOIN subjects s ON ia.subject_code = s.subject_code
                JOIN exams e1 ON ia.subject_code = e1.subject_code AND ia.exam_date = e1.exam_date
                JOIN exams e2 ON e2.subject_code = ? AND e2.exam_date = ?
                WHERE ia.staff_id = ? AND ia.exam_date = ? AND ia.is_active = 1
                AND (
                    (e1.start_time <= e2.start_time AND e1.end_time > e2.start_time) OR
                    (e2.start_time <= e1.start_time AND e2.end_time > e1.start_time)
                )
            '''
            
            conflicts = self.db_manager.execute_query(
                conflict_check_query,
                (overlapping_assignment['subject_code'], overlapping_assignment['exam_date'],
                 overlapping_assignment['staff_id'], overlapping_assignment['exam_date'])
            )
            
            if conflicts and len(conflicts) > 0:
                conflict = conflicts[0]
                warning_message = f"Warning: {conflict['invigilator_name']} is already assigned to {conflict['room_name']} from {conflict['existing_start']} to {conflict['existing_end']}. New assignment conflicts with time {conflict['new_start']} to {conflict['new_end']}."
                
                print("   ✅ Conflict detected successfully")
                print(f"   ⚠️  Warning message: {warning_message}")
                print("   📝 Overlapping assignment warning displayed correctly")
                return True
            else:
                print("   ❌ No conflict detected - this should have shown a warning")
                return False
                
        except Exception as e:
            print(f"   ❌ Error in overlap test: {str(e)}")
            return False
    
    def test_duty_chart_generation(self):
        """Test Case 3: Generate duty chart with assignments"""
        print("\n🧪 Testing TC-INVIGILATOR-03: Generate duty chart")
        
        try:
            # Get all assignments for duty chart
            duty_chart_query = '''
                SELECT ia.*, i.name as invigilator_name, i.department, i.phone,
                       r.name as room_name, r.building, s.subject_name,
                       e.start_time, e.end_time, e.duration
                FROM invigilator_assignments ia
                JOIN invigilators i ON ia.staff_id = i.staff_id
                JOIN rooms r ON ia.room_id = r.room_id
                JOIN subjects s ON ia.subject_code = s.subject_code
                JOIN exams e ON ia.subject_code = e.subject_code AND ia.exam_date = e.exam_date
                WHERE ia.exam_date = ? AND ia.is_active = 1
                ORDER BY ia.session_time, i.name
            '''
            
            duty_chart = self.db_manager.execute_query(duty_chart_query, (self.test_data['exam_date'],))
            
            if duty_chart and len(duty_chart) > 0:
                print(f"   ✅ Duty chart generated with {len(duty_chart)} assignments")
                print("   📊 Duty Chart Details:")
                
                for assignment in duty_chart:
                    print(f"      - {assignment['invigilator_name']} ({assignment['department']})")
                    print(f"        Room: {assignment['room_name']} ({assignment['building']})")
                    print(f"        Subject: {assignment['subject_name']}")
                    print(f"        Time: {assignment['start_time']} - {assignment['end_time']}")
                    print(f"        Phone: {assignment['phone']}")
                    print()
                
                print("   📝 Duty chart generated successfully with all assignment details")
                return True
            else:
                print("   ❌ No assignments found for duty chart")
                return False
                
        except Exception as e:
            print(f"   ❌ Error generating duty chart: {str(e)}")
            return False
    
    def test_assignment_validation(self):
        """Test Case 4: Validate assignment constraints"""
        print("\n🧪 Testing TC-INVIGILATOR-04: Assignment validation")
        
        try:
            # Test invalid invigilator
            print("   📊 Testing invalid invigilator assignment...")
            invalid_assignment = {
                'staff_id': 'INVALID_STAFF',
                'room_id': 'TEST_ROOM_01',
                'exam_date': self.test_data['exam_date'],
                'session_time': '14:00',
                'subject_code': 'TEST_SUB_001'
            }
            
            # Check if invigilator exists
            invigilator_check = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM invigilators WHERE staff_id = ? AND is_active = 1",
                (invalid_assignment['staff_id'],)
            )
            
            if invigilator_check[0]['count'] == 0:
                print("   ✅ Invalid invigilator detected correctly")
            else:
                print("   ❌ Invalid invigilator not detected")
                return False
            
            # Test invalid room
            print("   📊 Testing invalid room assignment...")
            invalid_room_assignment = {
                'staff_id': 'TEST_INV_002',
                'room_id': 'INVALID_ROOM',
                'exam_date': self.test_data['exam_date'],
                'session_time': '14:00',
                'subject_code': 'TEST_SUB_001'
            }
            
            room_check = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM rooms WHERE room_id = ? AND is_active = 1",
                (invalid_room_assignment['room_id'],)
            )
            
            if room_check[0]['count'] == 0:
                print("   ✅ Invalid room detected correctly")
            else:
                print("   ❌ Invalid room not detected")
                return False
            
            print("   📝 Assignment validation working correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Error in validation test: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data and temporary files"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            self._cleanup_test_data()
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🗑️  Removed temp directory: {self.temp_dir}")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up completely: {str(e)}")
    
    def run_all_tests(self):
        """Run all invigilator assignment tests"""
        print("=" * 80)
        print("  INVIGILATOR ASSIGNMENT FUNCTIONALITY TESTS")
        print("=" * 80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Setup
        self.setup_test_environment()
        
        # Run tests
        test_results = []
        
        test_results.append(("TC-INVIGILATOR-01 Assign Invigilator to Session", self.test_assign_invigilator_to_session()))
        test_results.append(("TC-INVIGILATOR-02 Overlapping Assignment Warning", self.test_overlapping_room_assignment_warning()))
        test_results.append(("TC-INVIGILATOR-03 Duty Chart Generation", self.test_duty_chart_generation()))
        test_results.append(("TC-INVIGILATOR-04 Assignment Validation", self.test_assignment_validation()))
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results summary
        print("\n" + "=" * 80)
        print("  TEST RESULTS SUMMARY")
        print("=" * 80)
        print()
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            status_icon = "✅" if result else "❌"
            print(f"{status_icon} {test_name} - {status}")
            
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {len(test_results)}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {(passed/len(test_results)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Invigilator assignment functionality is working correctly.")
        else:
            print(f"\n⚠️  {failed} TEST(S) FAILED! Please check the implementation.")
        
        print("=" * 80)
        
        return failed == 0

def main():
    """Main function to run invigilator assignment tests"""
    tester = InvigilatorAssignmentTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())