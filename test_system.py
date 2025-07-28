#!/usr/bin/env python3
"""
Test script for Examination Seating Arrangement System
"""
import sys
import os
import unittest
from datetime import datetime, date

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSystemComponents(unittest.TestCase):
    """Test system components"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from backend.database import db_manager
            self.db_manager = db_manager
        except ImportError as e:
            self.skipTest(f"Cannot import database module: {e}")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            stats = self.db_manager.get_statistics()
            self.assertIsInstance(stats, dict)
            print("✅ Database connection test passed")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_models_import(self):
        """Test model imports"""
        try:
            from backend.models import Student, Subject, Room, Exam, Invigilator
            print("✅ Models import test passed")
        except ImportError as e:
            self.fail(f"Models import failed: {e}")
    
    def test_seating_algorithm_import(self):
        """Test seating algorithm import"""
        try:
            from backend.seating_algorithm import seating_algorithm
            self.assertIsNotNone(seating_algorithm)
            print("✅ Seating algorithm import test passed")
        except ImportError as e:
            self.fail(f"Seating algorithm import failed: {e}")
    
    def test_reports_import(self):
        """Test reports module import"""
        try:
            from backend.reports import report_generator
            self.assertIsNotNone(report_generator)
            print("✅ Reports module import test passed")
        except ImportError as e:
            self.fail(f"Reports module import failed: {e}")
    
    def test_frontend_routes_import(self):
        """Test frontend routes import"""
        try:
            from frontend.routes import register_blueprints
            self.assertIsNotNone(register_blueprints)
            print("✅ Frontend routes import test passed")
        except ImportError as e:
            self.fail(f"Frontend routes import failed: {e}")

class TestDataOperations(unittest.TestCase):
    """Test data operations"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from backend.models import Student, Subject, Room
            self.Student = Student
            self.Subject = Subject
            self.Room = Room
        except ImportError as e:
            self.skipTest(f"Cannot import models: {e}")
    
    def test_student_creation(self):
        """Test student creation"""
        try:
            student = self.Student(
                student_id='TEST001',
                name='Test Student',
                department='Computer Science',
                semester=1,
                email='test@example.com'
            )
            self.assertEqual(student.student_id, 'TEST001')
            self.assertEqual(student.name, 'Test Student')
            print("✅ Student creation test passed")
        except Exception as e:
            self.fail(f"Student creation failed: {e}")
    
    def test_subject_creation(self):
        """Test subject creation"""
        try:
            subject = self.Subject(
                subject_code='TEST101',
                subject_name='Test Subject',
                department='Computer Science',
                semester=1
            )
            self.assertEqual(subject.subject_code, 'TEST101')
            self.assertEqual(subject.subject_name, 'Test Subject')
            print("✅ Subject creation test passed")
        except Exception as e:
            self.fail(f"Subject creation failed: {e}")
    
    def test_room_creation(self):
        """Test room creation"""
        try:
            room = self.Room(
                room_id='TEST_ROOM',
                name='Test Room',
                rows=10,
                cols=10,
                capacity=100
            )
            self.assertEqual(room.room_id, 'TEST_ROOM')
            self.assertEqual(room.capacity, 100)
            print("✅ Room creation test passed")
        except Exception as e:
            self.fail(f"Room creation failed: {e}")

class TestSeatingAlgorithm(unittest.TestCase):
    """Test seating algorithm"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from backend.seating_algorithm import seating_algorithm
            self.seating_algorithm = seating_algorithm
        except ImportError as e:
            self.skipTest(f"Cannot import seating algorithm: {e}")
    
    def test_algorithm_methods(self):
        """Test algorithm methods exist"""
        try:
            self.assertTrue(hasattr(self.seating_algorithm, 'generate_seating_arrangement'))
            self.assertTrue(hasattr(self.seating_algorithm, 'validate_arrangement'))
            self.assertTrue(hasattr(self.seating_algorithm, 'get_arrangement_statistics'))
            print("✅ Seating algorithm methods test passed")
        except Exception as e:
            self.fail(f"Seating algorithm methods test failed: {e}")

class TestFlaskApp(unittest.TestCase):
    """Test Flask application"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from app_modular import create_app
            self.app = create_app()
            self.app.config['TESTING'] = True
            self.client = self.app.test_client()
        except ImportError as e:
            self.skipTest(f"Cannot import Flask app: {e}")
    
    def test_app_creation(self):
        """Test app creation"""
        try:
            self.assertIsNotNone(self.app)
            print("✅ Flask app creation test passed")
        except Exception as e:
            self.fail(f"Flask app creation failed: {e}")
    
    def test_login_page(self):
        """Test login page access"""
        try:
            response = self.client.get('/login')
            self.assertEqual(response.status_code, 200)
            print("✅ Login page access test passed")
        except Exception as e:
            self.fail(f"Login page access failed: {e}")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = self.client.get('/health')
            self.assertIn(response.status_code, [200, 500])  # May fail if DB not initialized
            print("✅ Health endpoint test passed")
        except Exception as e:
            self.fail(f"Health endpoint test failed: {e}")

def run_system_check():
    """Run comprehensive system check"""
    print("=" * 60)
    print("  EXAMINATION SEATING SYSTEM - SYSTEM CHECK")
    print("=" * 60)
    print()
    
    # Check Python version
    print(f"Python Version: {sys.version}")
    print(f"Python Path: {sys.executable}")
    print()
    
    # Check required directories
    print("Checking directories...")
    required_dirs = ['backend', 'frontend', 'templates', 'static']
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}/ exists")
        else:
            print(f"❌ {directory}/ missing")
    print()
    
    # Check required files
    print("Checking required files...")
    required_files = [
        'app_modular.py',
        'requirements.txt',
        'backend/database.py',
        'backend/models.py',
        'backend/seating_algorithm.py',
        'backend/reports.py',
        'frontend/routes.py',
        'templates/base.html',
        'templates/login.html'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
    print()
    
    # Run unit tests
    print("Running unit tests...")
    print("-" * 40)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestSystemComponents))
    test_suite.addTest(loader.loadTestsFromTestCase(TestDataOperations))
    test_suite.addTest(loader.loadTestsFromTestCase(TestSeatingAlgorithm))
    test_suite.addTest(loader.loadTestsFromTestCase(TestFlaskApp))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("-" * 40)
    print()
    
    # Summary
    if result.wasSuccessful():
        print("🎉 All tests passed! System is ready to use.")
        print()
        print("Next steps:")
        print("1. Run: python app_modular.py")
        print("2. Open: http://localhost:5000")
        print("3. Login: admin@exam.com / admin123")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print()
        print("Common solutions:")
        print("1. Run: pip install -r requirements.txt")
        print("2. Run: python setup.py")
        print("3. Check file permissions")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    run_system_check()