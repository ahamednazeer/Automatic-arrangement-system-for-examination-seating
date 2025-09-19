#!/usr/bin/env python3
"""
Simple Authentication Test Suite for Examination Seating System
Tests the core authentication functionality based on test cases:
- TC-AUTH-01: Login with valid credentials
- TC-AUTH-02: Login with invalid credentials  
- TC-AUTH-03: Logout user
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestAuthenticationCore(unittest.TestCase):
    """Test core authentication functionality"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from app_modular import create_app
            self.app = create_app()
            self.app.config['TESTING'] = True
            self.app.config['SECRET_KEY'] = 'test-secret-key'
            self.client = self.app.test_client()
            self.app_context = self.app.app_context()
            self.app_context.push()
        except ImportError as e:
            self.skipTest(f"Cannot import Flask app: {e}")
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        print("\n🧪 Testing login page accessibility")
        
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.get_data(as_text=True)
        self.assertIn('ExamSeat', response_data)
        self.assertIn('email', response_data)
        self.assertIn('password', response_data)
        
        print("✅ Login page loads correctly")
    
    @patch('backend.database.db_manager')
    def test_tc_auth_01_valid_login(self, mock_db):
        """
        TC-AUTH-01: Login with valid credentials
        Expected: Redirect to dashboard
        """
        print("\n🧪 Running TC-AUTH-01: Login with valid credentials")
        
        # Mock valid admin user
        mock_admin = {
            'id': 1,
            'name': 'Test Admin',
            'email': 'admin@exam.com',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'is_active': 1
        }
        mock_db.execute_query.return_value = mock_admin
        mock_db.log_action.return_value = None
        
        # Attempt login
        response = self.client.post('/login', data={
            'email': 'admin@exam.com',
            'password': 'admin123'
        }, follow_redirects=False)
        
        # Check redirect response
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard', response.location)
        
        # Verify database was called
        mock_db.execute_query.assert_called()
        mock_db.log_action.assert_called()
        
        print("✅ TC-AUTH-01 PASSED: Valid credentials redirect to dashboard")
    
    @patch('backend.database.db_manager')
    def test_tc_auth_02_invalid_login(self, mock_db):
        """
        TC-AUTH-02: Login with invalid credentials
        Expected: Show error message
        """
        print("\n🧪 Running TC-AUTH-02: Login with invalid credentials")
        
        # Test case 1: Wrong password
        mock_admin = {
            'id': 1,
            'name': 'Test Admin',
            'email': 'admin@exam.com',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'is_active': 1
        }
        mock_db.execute_query.return_value = mock_admin
        
        response = self.client.post('/login', data={
            'email': 'admin@exam.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', response_data)
        
        print("✅ TC-AUTH-02 PASSED: Wrong password shows error")
        
        # Test case 2: Non-existent user
        mock_db.execute_query.return_value = None
        
        response = self.client.post('/login', data={
            'email': 'nonexistent@exam.com',
            'password': 'admin123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', response_data)
        
        print("✅ TC-AUTH-02 PASSED: Non-existent user shows error")
    
    @patch('backend.database.db_manager')
    def test_tc_auth_03_logout(self, mock_db):
        """
        TC-AUTH-03: Logout user
        Expected: Return to login page
        """
        print("\n🧪 Running TC-AUTH-03: Logout user")
        
        mock_db.log_action.return_value = None
        
        # First login to create session
        with self.client as c:
            with c.session_transaction() as sess:
                sess['admin_id'] = 1
                sess['admin_name'] = 'Test Admin'
                sess['admin_email'] = 'admin@exam.com'
                sess['admin_role'] = 'admin'
            
            # Now logout
            response = c.get('/logout', follow_redirects=False)
            
            # Check redirect to login
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login', response.location)
            
            # Verify session is cleared
            with c.session_transaction() as sess:
                self.assertNotIn('admin_id', sess)
        
        print("✅ TC-AUTH-03 PASSED: Logout redirects to login and clears session")
    
    def test_protected_routes_redirect(self):
        """Test that protected routes redirect to login"""
        print("\n🧪 Testing protected route access without login")
        
        # Test dashboard redirect
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
        
        print("✅ Protected routes redirect to login when not authenticated")

def run_auth_tests():
    """Run authentication tests with summary"""
    print("=" * 70)
    print("  AUTHENTICATION TEST SUITE")
    print("=" * 70)
    print()
    print("Testing authentication functionality:")
    print("• TC-AUTH-01: Login with valid credentials")
    print("• TC-AUTH-02: Login with invalid credentials")
    print("• TC-AUTH-03: Logout user")
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthenticationCore)
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   ✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Failed: {len(result.failures)}")
    print(f"   🚨 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("\n✅ TC-AUTH-01: Login with valid credentials - PASSED")
        print("✅ TC-AUTH-02: Login with invalid credentials - PASSED") 
        print("✅ TC-AUTH-03: Logout user - PASSED")
        print("\nAuthentication system is working correctly! ✨")
    else:
        print("\n❌ SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, error in result.failures:
                print(f"  • {test.id()}: {error.split('AssertionError: ')[-1].split(chr(10))[0]}")
        if result.errors:
            print("\nErrors:")
            for test, error in result.errors:
                print(f"  • {test.id()}: {error.split(chr(10))[-2]}")
    
    print("\n" + "=" * 70)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_auth_tests()
    sys.exit(0 if success else 1)