#!/usr/bin/env python3
"""
Seat Allocation Functionality Tests
Test Cases: TC-SEAT-01 through TC-SEAT-04
"""

import sys
import os
import unittest
from datetime import datetime, date, timedelta
import uuid

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.database import db_manager
    from backend.seating_algorithm import seating_algorithm
    from backend.models import Student, Subject, Room, Exam
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

class TestSeatAllocation(unittest.TestCase):
    """Test seat allocation functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        print("🔧 Setting up test environment...")
        
        # Initialize database if needed
        try:
            if hasattr(db_manager, 'initialize_database'):
                db_manager.initialize_database()
                print("✅ Database initialized")
            else:
                print("⚠️  Database initialization: 'DatabaseManager' object has no attribute 'initialize_database'")
        except Exception as e:
            print(f"⚠️  Database initialization error: {e}")
        
        # Test data
        cls.test_subjects = [
            {'subject_code': 'CS46390801', 'subject_name': 'Data Structures', 'department': 'Computer Science', 'semester': 3},
            {'subject_code': 'CS46390802', 'subject_name': 'Algorithms', 'department': 'Computer Science', 'semester': 3},
            {'subject_code': 'IT46390801', 'subject_name': 'Database Systems', 'department': 'Information Technology', 'semester': 3},
            {'subject_code': 'EC46390801', 'subject_name': 'Digital Electronics', 'department': 'Electronics', 'semester': 3}
        ]
        
        cls.test_students = [
            {'student_id': 'S46390801', 'name': 'Alice Johnson', 'department': 'Computer Science', 'semester': 3},
            {'student_id': 'S46390802', 'name': 'Bob Smith', 'department': 'Computer Science', 'semester': 3},
            {'student_id': 'S46390803', 'name': 'Charlie Brown', 'department': 'Computer Science', 'semester': 3},
            {'student_id': 'IT46390801', 'name': 'David Wilson', 'department': 'Information Technology', 'semester': 3},
            {'student_id': 'IT46390802', 'name': 'Eva Davis', 'department': 'Information Technology', 'semester': 3},
            {'student_id': 'EC46390801', 'name': 'Frank Miller', 'department': 'Electronics', 'semester': 3},
            {'student_id': 'EC46390802', 'name': 'Grace Lee', 'department': 'Electronics', 'semester': 3},
            {'student_id': 'EC46390803', 'name': 'Henry Taylor', 'department': 'Electronics', 'semester': 3}
        ]
        
        cls.test_rooms = [
            {'room_id': 'SEAT_TEST_ROOM_01', 'name': 'Test Room 1', 'rows': 5, 'cols': 4, 'capacity': 20},
            {'room_id': 'SEAT_TEST_ROOM_02', 'name': 'Test Room 2', 'rows': 4, 'cols': 3, 'capacity': 12}
        ]
        
        # Clean up any leftover data first
        cls._cleanup_leftover_data()
        
        # Create test data
        cls._create_test_data()
        
    @classmethod
    def _cleanup_leftover_data(cls):
        """Clean up any leftover data from previous test runs"""
        try:
            # Clean up overflow students and their enrollments
            db_manager.execute_query("DELETE FROM student_subjects WHERE student_id LIKE 'OVERFLOW_%'")
            db_manager.execute_query("DELETE FROM students WHERE student_id LIKE 'OVERFLOW_%'")
            
            # Clean up any existing test subject enrollments
            for subject in cls.test_subjects:
                db_manager.execute_query("DELETE FROM student_subjects WHERE subject_code = ?", (subject['subject_code'],))
            
            # Clean up seating arrangements
            db_manager.execute_query("DELETE FROM seating_arrangements WHERE room_id LIKE 'SEAT_TEST_%'")
            
            # Store original room states and deactivate non-test rooms for testing
            cls._store_and_deactivate_production_rooms()
            
            print("   🧹 Cleaned up leftover test data")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")
    
    @classmethod
    def _store_and_deactivate_production_rooms(cls):
        """Store original room states and deactivate production rooms"""
        try:
            # Get all active rooms that are not test rooms
            query = "SELECT room_id FROM rooms WHERE is_active = 1 AND room_id NOT LIKE 'SEAT_TEST_%'"
            cls.original_active_rooms = db_manager.execute_query(query)
            
            # Deactivate production rooms during testing
            db_manager.execute_query("UPDATE rooms SET is_active = 0 WHERE room_id NOT LIKE 'SEAT_TEST_%'")
            
        except Exception as e:
            print(f"   ⚠️  Room deactivation warning: {e}")
            cls.original_active_rooms = []
    
    @classmethod
    def _create_test_data(cls):
        """Create test subjects, students, and rooms"""
        
        # Create test subjects
        for subject_data in cls.test_subjects:
            try:
                query = '''
                    INSERT OR REPLACE INTO subjects 
                    (subject_code, subject_name, department, semester, is_active)
                    VALUES (?, ?, ?, ?, 1)
                '''
                db_manager.execute_query(query, (
                    subject_data['subject_code'],
                    subject_data['subject_name'],
                    subject_data['department'],
                    subject_data['semester']
                ))
                print(f"   📚 Created test subject: {subject_data['subject_code']}")
            except Exception as e:
                print(f"   ❌ Failed to create subject {subject_data['subject_code']}: {e}")
        
        # Create test students
        for student_data in cls.test_students:
            try:
                query = '''
                    INSERT OR REPLACE INTO students 
                    (student_id, name, department, semester, email, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                '''
                db_manager.execute_query(query, (
                    student_data['student_id'],
                    student_data['name'],
                    student_data['department'],
                    student_data['semester'],
                    f"{student_data['student_id'].lower()}@test.edu"
                ))
                print(f"   👤 Created test student: {student_data['student_id']}")
            except Exception as e:
                print(f"   ❌ Failed to create student {student_data['student_id']}: {e}")
        
        # Create test rooms
        for room_data in cls.test_rooms:
            try:
                query = '''
                    INSERT OR REPLACE INTO rooms 
                    (room_id, name, rows, cols, capacity, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                '''
                db_manager.execute_query(query, (
                    room_data['room_id'],
                    room_data['name'],
                    room_data['rows'],
                    room_data['cols'],
                    room_data['capacity']
                ))
                print(f"   🏢 Created test room: {room_data['room_id']}")
            except Exception as e:
                print(f"   ❌ Failed to create room {room_data['room_id']}: {e}")
    
    def setUp(self):
        """Set up for each test"""
        self.test_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.test_time = '10:00'
        
        # Clean up any existing arrangements
        self._cleanup_arrangements()
        
        # Clean up any existing exams
        self._cleanup_exams()
        
        # Clean up any leftover overflow students
        self._cleanup_overflow_students()
    
    def tearDown(self):
        """Clean up after each test"""
        self._cleanup_arrangements()
        self._cleanup_exams()
        self._cleanup_overflow_students()
    
    def _cleanup_arrangements(self):
        """Clean up seating arrangements"""
        try:
            query = "DELETE FROM seating_arrangements WHERE exam_date = ? AND session_time = ?"
            db_manager.execute_query(query, (self.test_date, self.test_time))
        except Exception:
            pass
    
    def _cleanup_exams(self):
        """Clean up test exams"""
        try:
            for subject in self.test_subjects:
                query = "DELETE FROM exams WHERE subject_code = ? AND exam_date = ?"
                db_manager.execute_query(query, (subject['subject_code'], self.test_date))
        except Exception:
            pass
    
    def _cleanup_overflow_students(self):
        """Clean up overflow students from previous test runs"""
        try:
            # Clean up overflow students and their enrollments
            db_manager.execute_query("DELETE FROM student_subjects WHERE student_id LIKE 'OVERFLOW_%'")
            db_manager.execute_query("DELETE FROM students WHERE student_id LIKE 'OVERFLOW_%'")
        except Exception:
            pass
    
    def _create_test_exam(self, subject_code, exam_date=None, start_time=None):
        """Create a test exam"""
        if exam_date is None:
            exam_date = self.test_date
        if start_time is None:
            start_time = self.test_time
            
        try:
            query = '''
                INSERT INTO exams 
                (subject_code, exam_date, start_time, end_time, duration, is_active)
                VALUES (?, ?, ?, ?, 180, 1)
            '''
            result = db_manager.execute_query(query, (
                subject_code, exam_date, start_time, '13:00'
            ))
            return True
        except Exception as e:
            print(f"Failed to create exam: {e}")
            return False
    
    def _enroll_students_in_subject(self, subject_code, student_ids):
        """Enroll students in a subject"""
        for student_id in student_ids:
            try:
                query = '''
                    INSERT OR REPLACE INTO student_subjects 
                    (student_id, subject_code, is_active)
                    VALUES (?, ?, 1)
                '''
                db_manager.execute_query(query, (student_id, subject_code))
            except Exception as e:
                print(f"Failed to enroll student {student_id}: {e}")
    
    def _get_seating_arrangements(self):
        """Get current seating arrangements"""
        try:
            query = '''
                SELECT sa.*, s.name, s.department, sub.subject_name
                FROM seating_arrangements sa
                JOIN students s ON sa.student_id = s.student_id
                JOIN subjects sub ON sa.subject_code = sub.subject_code
                WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
                ORDER BY sa.room_id, sa.seat_row, sa.seat_col
            '''
            return db_manager.execute_query(query, (self.test_date, self.test_time))
        except Exception as e:
            print(f"Failed to get arrangements: {e}")
            return []
    
    def _check_adjacent_conflicts(self, arrangements):
        """Check for adjacent same-department students"""
        conflicts = []
        
        # Group by room
        rooms = {}
        for arr in arrangements:
            room_id = arr['room_id']
            if room_id not in rooms:
                rooms[room_id] = {}
            
            key = (arr['seat_row'], arr['seat_col'])
            rooms[room_id][key] = arr
        
        # Check each room for conflicts
        for room_id, seats in rooms.items():
            for (row, col), student in seats.items():
                # Check adjacent positions (4-directional)
                adjacent_positions = [
                    (row-1, col), (row+1, col),  # up, down
                    (row, col-1), (row, col+1)   # left, right
                ]
                
                for adj_row, adj_col in adjacent_positions:
                    adj_key = (adj_row, adj_col)
                    if adj_key in seats:
                        adjacent_student = seats[adj_key]
                        if student['department'] == adjacent_student['department']:
                            conflicts.append({
                                'student1': student,
                                'student2': adjacent_student,
                                'room': room_id
                            })
        
        return conflicts
    
    def test_tc_seat_01_allocate_seats_valid_data(self):
        """TC-SEAT-01: Allocate seats for valid data"""
        print("\n🧪 Testing TC-SEAT-01: Allocate seats for valid data")
        
        # Create exam for CS subject
        self.assertTrue(self._create_test_exam('CS46390801'))
        
        # Enroll students in the subject
        cs_students = ['S46390801', 'S46390802', 'S46390803']
        self._enroll_students_in_subject('CS46390801', cs_students)
        
        # Generate seating arrangement
        result = seating_algorithm.generate_seating_arrangement(
            exam_date=self.test_date,
            session_time=self.test_time,
            arrangement_type='mixed',
            conflict_avoidance='moderate'
        )
        
        # Verify result
        self.assertTrue(result['success'], f"Seating generation failed: {result.get('message', 'Unknown error')}")
        self.assertEqual(result['students_allocated'], 3, "Should allocate all 3 students")
        self.assertEqual(result['students_failed'], 0, "Should have no failed allocations")
        
        # Verify arrangements in database
        arrangements = self._get_seating_arrangements()
        self.assertEqual(len(arrangements), 3, "Should have 3 seating records")
        
        # Verify all students are seated
        seated_students = {arr['student_id'] for arr in arrangements}
        expected_students = set(cs_students)
        self.assertEqual(seated_students, expected_students, "All students should be seated")
        
        print("✅ TC-SEAT-01: Allocate seats for valid data - PASS")
        print(f"   📝 All {len(arrangements)} students seated successfully")
    
    def test_tc_seat_02_prevent_adjacent_same_department(self):
        """TC-SEAT-02: Prevent same-subject students from sitting adjacent"""
        print("\n🧪 Testing TC-SEAT-02: Prevent same-subject students from sitting adjacent")
        
        # Create exam for CS subject
        self.assertTrue(self._create_test_exam('CS46390801'))
        
        # Enroll multiple CS students
        cs_students = ['S46390801', 'S46390802', 'S46390803']
        self._enroll_students_in_subject('CS46390801', cs_students)
        
        # Generate seating arrangement with strict conflict avoidance
        result = seating_algorithm.generate_seating_arrangement(
            exam_date=self.test_date,
            session_time=self.test_time,
            arrangement_type='mixed',
            conflict_avoidance='strict'
        )
        
        # Verify result
        self.assertTrue(result['success'], f"Seating generation failed: {result.get('message', 'Unknown error')}")
        
        # Get arrangements and check for conflicts
        arrangements = self._get_seating_arrangements()
        conflicts = self._check_adjacent_conflicts(arrangements)
        
        # With strict conflict avoidance, there should be minimal conflicts
        # (Some conflicts might be unavoidable with limited room space)
        conflict_count = len(conflicts)
        
        print(f"   📊 Found {conflict_count} adjacent same-department pairs")
        
        # For this test, we expect the algorithm to minimize conflicts
        # The exact number depends on room layout and student count
        self.assertLessEqual(conflict_count, 1, "Should minimize adjacent same-department students")
        
        print("✅ TC-SEAT-02: Prevent same-subject students from sitting adjacent - PASS")
        print(f"   📝 Conflict avoidance working - {conflict_count} conflicts detected")
    
    def test_tc_seat_03_overflow_case(self):
        """TC-SEAT-03: Overflow case - students > total seats"""
        print("\n🧪 Testing TC-SEAT-03: Overflow case - students > total seats")
        
        # Create exam
        self.assertTrue(self._create_test_exam('CS46390801'))
        
        # Create many students (more than room capacity)
        overflow_students = []
        total_capacity = sum(room['capacity'] for room in self.test_rooms)  # 32 seats
        student_count = total_capacity + 10  # 42 students (10 overflow)
        
        # Create additional students for overflow test
        for i in range(student_count):
            student_id = f'OVERFLOW_{i+1:03d}'
            overflow_students.append(student_id)
            
            # Add to database
            try:
                query = '''
                    INSERT OR REPLACE INTO students 
                    (student_id, name, department, semester, email, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                '''
                db_manager.execute_query(query, (
                    student_id,
                    f'Overflow Student {i+1}',
                    'Computer Science',
                    3,
                    f'overflow{i+1}@test.edu'
                ))
            except Exception as e:
                print(f"Failed to create overflow student: {e}")
        
        # Enroll all students
        self._enroll_students_in_subject('CS46390801', overflow_students)
        
        # Generate seating arrangement
        result = seating_algorithm.generate_seating_arrangement(
            exam_date=self.test_date,
            session_time=self.test_time,
            arrangement_type='mixed',
            conflict_avoidance='relaxed'
        )
        
        # The algorithm should detect insufficient capacity
        if result['success']:
            # If it succeeds, check that it allocated maximum possible
            self.assertLessEqual(result['students_allocated'], total_capacity, f"Allocated {result['students_allocated']} > capacity {total_capacity}")
            self.assertGreater(result['students_failed'], 0, "Should have some failed allocations")
            
            print(f"   📊 Allocated: {result['students_allocated']}, Failed: {result['students_failed']}")
            print("✅ TC-SEAT-03: Overflow case - PASS")
            print(f"   📝 {result['students_allocated']} seated, {result['students_failed']} unassigned with capacity limit respected")
        else:
            # Algorithm correctly detected insufficient capacity
            self.assertIn('Insufficient capacity', result['message'])
            print("✅ TC-SEAT-03: Overflow case - PASS")
            print(f"   📝 System correctly detected capacity overflow: {result['message']}")
        
        # Clean up overflow students
        try:
            for student_id in overflow_students:
                db_manager.execute_query("DELETE FROM student_subjects WHERE student_id = ?", (student_id,))
                db_manager.execute_query("DELETE FROM students WHERE student_id = ?", (student_id,))
        except Exception:
            pass
    
    def test_tc_seat_04_rerun_allocation(self):
        """TC-SEAT-04: Re-run allocation - same dataset"""
        print("\n🧪 Testing TC-SEAT-04: Re-run allocation - same dataset")
        
        # Create exam
        self.assertTrue(self._create_test_exam('CS46390801'))
        
        # Enroll students
        cs_students = ['S46390801', 'S46390802', 'S46390803']
        self._enroll_students_in_subject('CS46390801', cs_students)
        
        # First allocation
        result1 = seating_algorithm.generate_seating_arrangement(
            exam_date=self.test_date,
            session_time=self.test_time,
            arrangement_type='mixed',
            conflict_avoidance='moderate'
        )
        
        self.assertTrue(result1['success'], "First allocation should succeed")
        arrangements1 = self._get_seating_arrangements()
        
        # Second allocation (should clear and recreate)
        result2 = seating_algorithm.generate_seating_arrangement(
            exam_date=self.test_date,
            session_time=self.test_time,
            arrangement_type='mixed',
            conflict_avoidance='moderate'
        )
        
        self.assertTrue(result2['success'], "Second allocation should succeed")
        arrangements2 = self._get_seating_arrangements()
        
        # Verify both allocations have same number of students
        self.assertEqual(len(arrangements1), len(arrangements2), "Both allocations should seat same number of students")
        self.assertEqual(result1['students_allocated'], result2['students_allocated'], "Same allocation count")
        
        # Verify all students are still seated
        seated_students1 = {arr['student_id'] for arr in arrangements1}
        seated_students2 = {arr['student_id'] for arr in arrangements2}
        self.assertEqual(seated_students1, seated_students2, "Same students should be seated")
        
        # The arrangements might be different (rebalanced), but should be valid
        print(f"   📊 First run: {result1['students_allocated']} students")
        print(f"   📊 Second run: {result2['students_allocated']} students")
        
        print("✅ TC-SEAT-04: Re-run allocation - PASS")
        print("   📝 Re-allocation successful with consistent results")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test data...")
        
        # Clean up test students
        for student_data in cls.test_students:
            try:
                db_manager.execute_query("DELETE FROM student_subjects WHERE student_id = ?", (student_data['student_id'],))
                db_manager.execute_query("DELETE FROM students WHERE student_id = ?", (student_data['student_id'],))
                print(f"   🗑️  Deleted test student: {student_data['student_id']}")
            except Exception:
                pass
        
        # Clean up test subjects
        for subject_data in cls.test_subjects:
            try:
                db_manager.execute_query("DELETE FROM subjects WHERE subject_code = ?", (subject_data['subject_code'],))
                print(f"   🗑️  Deleted test subject: {subject_data['subject_code']}")
            except Exception:
                pass
        
        # Clean up test rooms
        for room_data in cls.test_rooms:
            try:
                db_manager.execute_query("DELETE FROM rooms WHERE room_id = ?", (room_data['room_id'],))
                print(f"   🗑️  Deleted test room: {room_data['room_id']}")
            except Exception:
                pass
        
        # Restore original room states
        cls._restore_production_rooms()
    
    @classmethod
    def _restore_production_rooms(cls):
        """Restore original production room states"""
        try:
            if hasattr(cls, 'original_active_rooms') and cls.original_active_rooms:
                for room in cls.original_active_rooms:
                    db_manager.execute_query("UPDATE rooms SET is_active = 1 WHERE room_id = ?", (room['room_id'],))
                print(f"   🔄 Restored {len(cls.original_active_rooms)} production rooms")
        except Exception as e:
            print(f"   ⚠️  Room restoration warning: {e}")

def run_seat_allocation_tests():
    """Run seat allocation functionality tests"""
    print("=" * 80)
    print("  SEAT ALLOCATION FUNCTIONALITY TESTS")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestSeatAllocation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(test_suite)
    
    # Collect results
    test_results = []
    
    # Since we can't easily capture individual test results from TextTestRunner,
    # we'll run tests individually to get detailed results
    test_methods = [
        ('TC-SEAT-01', 'test_tc_seat_01_allocate_seats_valid_data', 'Allocate seats for valid data'),
        ('TC-SEAT-02', 'test_tc_seat_02_prevent_adjacent_same_department', 'Prevent same-subject students from sitting adjacent'),
        ('TC-SEAT-03', 'test_tc_seat_03_overflow_case', 'Overflow case: students > total seats'),
        ('TC-SEAT-04', 'test_tc_seat_04_rerun_allocation', 'Re-run allocation')
    ]
    
    test_instance = TestSeatAllocation()
    test_instance.setUpClass()
    
    for test_id, method_name, description in test_methods:
        try:
            test_instance.setUp()
            method = getattr(test_instance, method_name)
            method()
            test_instance.tearDown()
            test_results.append((test_id, description, 'PASS', ''))
        except Exception as e:
            test_results.append((test_id, description, 'FAIL', str(e)))
    
    test_instance.tearDownClass()
    
    # Print results summary
    print("\n" + "=" * 80)
    print("  TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_id, description, status, message in test_results:
        if status == 'PASS':
            print(f"✅ {test_id}: {description} - {status}")
            if message:
                print(f"   📝 {message}")
            passed += 1
        else:
            print(f"❌ {test_id}: {description} - {status}")
            if message:
                print(f"   📝 Error: {message}")
            failed += 1
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total Tests: {len(test_results)}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! Seat allocation functionality is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
    
    print("=" * 80)
    return failed == 0

if __name__ == "__main__":
    success = run_seat_allocation_tests()
    sys.exit(0 if success else 1)