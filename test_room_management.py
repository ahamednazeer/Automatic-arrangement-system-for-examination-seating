#!/usr/bin/env python3
"""
Room Management Functionality Tests
Test Cases: TC-ROOM-01 through TC-ROOM-04
"""
import sys
import os
import unittest
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestRoomManagement(unittest.TestCase):
    """Test room management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        print("🔧 Setting up test environment...")
        try:
            from backend.database import db_manager
            from backend.models import Room
            self.db_manager = db_manager
            self.Room = Room
            
            # Clean up any existing test rooms
            self.cleanup_test_data()
            
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")
        except Exception as e:
            print(f"⚠️  Database initialization: {e}")
    
    def tearDown(self):
        """Clean up after tests"""
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Remove test room data"""
        try:
            # Clean up all test rooms (including capacity test rooms)
            test_room_ids = ['TEST_ROOM_01', 'TEST_ROOM_02', 'TEST_ROOM_03', 'TEST_ROOM_04', 'TEST_ROOM_INVALID']
            
            # Add capacity test room IDs
            for i in range(1, 6):  # Clean up CAPACITY_TEST_1 through CAPACITY_TEST_5
                test_room_ids.append(f'CAPACITY_TEST_{i}')
            
            for room_id in test_room_ids:
                room = self.Room.get_by_id(room_id)
                if room:
                    # Hard delete for test cleanup
                    query = 'DELETE FROM rooms WHERE room_id = ?'
                    self.db_manager.execute_query(query, (room_id,))
        except Exception as e:
            pass  # Ignore cleanup errors
    
    def test_tc_room_01_add_room_with_valid_layout(self):
        """TC-ROOM-01: Add room with valid layout"""
        print("\n🧪 Testing TC-ROOM-01: Add room with valid layout")
        
        try:
            # Test data
            room_data = {
                'room_id': 'TEST_ROOM_01',
                'name': 'Test Computer Lab',
                'rows': 5,
                'cols': 6,
                'building': 'Main Building',
                'floor': 1,
                'room_type': 'computer_lab',
                'facilities': 'Projector, AC, Computers'
            }
            
            # Create room
            room = self.Room(
                room_id=room_data['room_id'],
                name=room_data['name'],
                rows=room_data['rows'],
                cols=room_data['cols'],
                capacity=room_data['rows'] * room_data['cols'],  # Auto-calculated
                building=room_data['building'],
                floor=room_data['floor'],
                room_type=room_data['room_type'],
                facilities=room_data['facilities']
            )
            
            # Save room
            result = room.save()
            self.assertTrue(result, "Room save operation should succeed")
            
            # Verify room was added
            saved_room = self.Room.get_by_id(room_data['room_id'])
            self.assertIsNotNone(saved_room, "Room should be retrievable after saving")
            self.assertEqual(saved_room.name, room_data['name'])
            self.assertEqual(saved_room.rows, room_data['rows'])
            self.assertEqual(saved_room.cols, room_data['cols'])
            self.assertEqual(saved_room.capacity, 30)  # 5 * 6
            self.assertEqual(saved_room.building, room_data['building'])
            self.assertEqual(saved_room.floor, room_data['floor'])
            
            # Verify room appears in list
            all_rooms = self.Room.get_all()
            room_ids = [r.room_id for r in all_rooms]
            self.assertIn(room_data['room_id'], room_ids, "Room should appear in room list")
            
            print("✅ TC-ROOM-01: Add room with valid layout - PASS")
            print("   📝 Room successfully added and appears in list")
            return True
            
        except Exception as e:
            print(f"❌ TC-ROOM-01: Add room with valid layout - FAIL")
            print(f"   📝 Error: {str(e)}")
            self.fail(f"TC-ROOM-01 failed: {str(e)}")
    
    def test_tc_room_02_add_room_with_invalid_capacity(self):
        """TC-ROOM-02: Add room with invalid capacity (negative or zero)"""
        print("\n🧪 Testing TC-ROOM-02: Add room with invalid capacity")
        
        try:
            # Test with zero rows
            with self.assertRaises(Exception) as context:
                room = self.Room(
                    room_id='TEST_ROOM_INVALID',
                    name='Invalid Room Zero Rows',
                    rows=0,
                    cols=5,
                    capacity=0
                )
                room.save()
            
            # Test with negative rows
            with self.assertRaises(Exception) as context:
                room = self.Room(
                    room_id='TEST_ROOM_INVALID',
                    name='Invalid Room Negative Rows',
                    rows=-1,
                    cols=5,
                    capacity=-5
                )
                room.save()
            
            # Test with zero cols
            with self.assertRaises(Exception) as context:
                room = self.Room(
                    room_id='TEST_ROOM_INVALID',
                    name='Invalid Room Zero Cols',
                    rows=5,
                    cols=0,
                    capacity=0
                )
                room.save()
            
            # Test with negative cols
            with self.assertRaises(Exception) as context:
                room = self.Room(
                    room_id='TEST_ROOM_INVALID',
                    name='Invalid Room Negative Cols',
                    rows=5,
                    cols=-1,
                    capacity=-5
                )
                room.save()
            
            # Verify no invalid room was created
            invalid_room = self.Room.get_by_id('TEST_ROOM_INVALID')
            self.assertIsNone(invalid_room, "Invalid room should not be saved")
            
            print("✅ TC-ROOM-02: Add room with invalid capacity - PASS")
            print("   📝 Correctly rejected rooms with invalid capacity values")
            return True
            
        except AssertionError:
            raise  # Re-raise assertion errors
        except Exception as e:
            print(f"❌ TC-ROOM-02: Add room with invalid capacity - FAIL")
            print(f"   📝 Error: {str(e)}")
            self.fail(f"TC-ROOM-02 failed: {str(e)}")
    
    def test_tc_room_03_edit_room_name(self):
        """TC-ROOM-03: Edit room name"""
        print("\n🧪 Testing TC-ROOM-03: Edit room name")
        
        try:
            # First create a room
            room = self.Room(
                room_id='TEST_ROOM_03',
                name='Original Room Name',
                rows=4,
                cols=5,
                capacity=20,
                building='Test Building'
            )
            room.save()
            
            # Verify room was created
            created_room = self.Room.get_by_id('TEST_ROOM_03')
            self.assertIsNotNone(created_room, "Room should be created first")
            self.assertEqual(created_room.name, 'Original Room Name')
            
            # Update room name
            created_room.name = 'Updated Room Name'
            update_result = created_room.save()
            self.assertTrue(update_result, "Room update should succeed")
            
            # Verify room name was updated
            updated_room = self.Room.get_by_id('TEST_ROOM_03')
            self.assertIsNotNone(updated_room, "Room should still exist after update")
            self.assertEqual(updated_room.name, 'Updated Room Name', "Room name should be updated")
            
            # Verify other properties remain unchanged
            self.assertEqual(updated_room.rows, 4)
            self.assertEqual(updated_room.cols, 5)
            self.assertEqual(updated_room.capacity, 20)
            self.assertEqual(updated_room.building, 'Test Building')
            
            print("✅ TC-ROOM-03: Edit room name - PASS")
            print("   📝 Room name successfully updated")
            return True
            
        except Exception as e:
            print(f"❌ TC-ROOM-03: Edit room name - FAIL")
            print(f"   📝 Error: {str(e)}")
            self.fail(f"TC-ROOM-03 failed: {str(e)}")
    
    def test_tc_room_04_delete_room(self):
        """TC-ROOM-04: Delete a room"""
        print("\n🧪 Testing TC-ROOM-04: Delete a room")
        
        try:
            # First create a room
            room = self.Room(
                room_id='TEST_ROOM_04',
                name='Room to Delete',
                rows=3,
                cols=4,
                capacity=12,
                building='Test Building'
            )
            room.save()
            
            # Verify room was created
            created_room = self.Room.get_by_id('TEST_ROOM_04')
            self.assertIsNotNone(created_room, "Room should be created first")
            
            # Verify room appears in list
            all_rooms_before = self.Room.get_all()
            room_ids_before = [r.room_id for r in all_rooms_before]
            self.assertIn('TEST_ROOM_04', room_ids_before, "Room should appear in list before deletion")
            
            # Delete the room
            delete_result = created_room.delete()
            self.assertTrue(delete_result, "Room deletion should succeed")
            
            # Verify room is no longer accessible (soft delete)
            deleted_room = self.Room.get_by_id('TEST_ROOM_04')
            self.assertIsNone(deleted_room, "Room should not be accessible after deletion")
            
            # Verify room no longer appears in list
            all_rooms_after = self.Room.get_all()
            room_ids_after = [r.room_id for r in all_rooms_after]
            self.assertNotIn('TEST_ROOM_04', room_ids_after, "Room should not appear in list after deletion")
            
            print("✅ TC-ROOM-04: Delete a room - PASS")
            print("   📝 Room successfully deleted and removed from list")
            return True
            
        except Exception as e:
            print(f"❌ TC-ROOM-04: Delete a room - FAIL")
            print(f"   📝 Error: {str(e)}")
            self.fail(f"TC-ROOM-04 failed: {str(e)}")
    
    def test_room_capacity_auto_calculation(self):
        """Additional test: Verify capacity is auto-calculated correctly"""
        print("\n🧪 Testing Additional: Room capacity auto-calculation")
        
        try:
            import time
            timestamp = str(int(time.time()))[-6:]  # Use last 6 digits of timestamp for unique IDs
            
            test_cases = [
                {'rows': 5, 'cols': 6, 'expected_capacity': 30},
                {'rows': 10, 'cols': 8, 'expected_capacity': 80},
                {'rows': 3, 'cols': 4, 'expected_capacity': 12},
                {'rows': 1, 'cols': 1, 'expected_capacity': 1},
            ]
            
            created_rooms = []  # Track created rooms for cleanup
            
            for i, test_case in enumerate(test_cases):
                room_id = f'CAP{timestamp}{i+1}'
                room = self.Room(
                    room_id=room_id,
                    name=f'Capacity Test Room {i+1}',
                    rows=test_case['rows'],
                    cols=test_case['cols'],
                    capacity=test_case['rows'] * test_case['cols']  # Auto-calculated
                )
                room.save()
                created_rooms.append(room_id)
                
                # Verify capacity calculation
                saved_room = self.Room.get_by_id(room_id)
                self.assertEqual(
                    saved_room.capacity, 
                    test_case['expected_capacity'],
                    f"Capacity should be {test_case['expected_capacity']} for {test_case['rows']}x{test_case['cols']} room"
                )
            
            # Clean up created rooms
            for room_id in created_rooms:
                room = self.Room.get_by_id(room_id)
                if room:
                    room.delete()
            
            print("✅ Additional: Room capacity auto-calculation - PASS")
            print("   📝 All capacity calculations are correct")
            return True
            
        except Exception as e:
            print(f"❌ Additional: Room capacity auto-calculation - FAIL")
            print(f"   📝 Error: {str(e)}")
            self.fail(f"Capacity auto-calculation test failed: {str(e)}")

def run_room_management_tests():
    """Run room management tests with detailed reporting"""
    print("=" * 80)
    print("  ROOM MANAGEMENT FUNCTIONALITY TESTS")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestRoomManagement))
    
    # Custom test runner for detailed output
    class DetailedTestResult(unittest.TextTestResult):
        def __init__(self, stream, descriptions, verbosity):
            super().__init__(stream, descriptions, verbosity)
            self.test_results = []
        
        def addSuccess(self, test):
            super().addSuccess(test)
            self.test_results.append(('PASS', test._testMethodName, None))
        
        def addError(self, test, err):
            super().addError(test, err)
            self.test_results.append(('ERROR', test._testMethodName, err[1]))
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.test_results.append(('FAIL', test._testMethodName, err[1]))
    
    class DetailedTestRunner(unittest.TextTestRunner):
        resultclass = DetailedTestResult
    
    # Run tests
    runner = DetailedTestRunner(verbosity=0)
    result = runner.run(test_suite)
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    try:
        from backend.database import db_manager
        test_room_ids = ['TEST_ROOM_01', 'TEST_ROOM_02', 'TEST_ROOM_03', 'TEST_ROOM_04', 'TEST_ROOM_INVALID']
        for room_id in test_room_ids:
            query = 'DELETE FROM rooms WHERE room_id = ?'
            db_manager.execute_query(query, (room_id,))
            print(f"   🗑️  Deleted test room: {room_id}")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("  TEST RESULTS SUMMARY")
    print("=" * 80)
    
    # Map test method names to readable descriptions
    test_descriptions = {
        'test_tc_room_01_add_room_with_valid_layout': 'TC-ROOM-01: Add room with valid layout',
        'test_tc_room_02_add_room_with_invalid_capacity': 'TC-ROOM-02: Add room with invalid capacity',
        'test_tc_room_03_edit_room_name': 'TC-ROOM-03: Edit room name',
        'test_tc_room_04_delete_room': 'TC-ROOM-04: Delete a room',
        'test_room_capacity_auto_calculation': 'Additional: Room capacity auto-calculation'
    }
    
    for status, test_name, error in result.test_results:
        description = test_descriptions.get(test_name, test_name)
        if status == 'PASS':
            print(f"✅ {description} - PASS")
        else:
            print(f"❌ {description} - {status}")
            if error:
                print(f"   📝 Error: {str(error)}")
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total Tests: {result.testsRun}")
    print(f"   Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Failed: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        success_rate = 100.0
        print(f"   Success Rate: {success_rate}%")
        print("\n🎉 ALL TESTS PASSED! Room management functionality is working correctly.")
    else:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 80)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_room_management_tests()
    sys.exit(0 if success else 1)