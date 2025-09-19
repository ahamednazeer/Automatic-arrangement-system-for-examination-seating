#!/usr/bin/env python3
"""
Authentication Test Suite for Examination Seating Arrangement System
Tests the authentication functionality based on the provided test cases:
- TC-AUTH-01: Login with valid credentials
- TC-AUTH-02: Login with invalid credentials  
- TC-AUTH-03: Logout user
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestAuthentication(unittest.TestCase):
    """Test authentication functionality"""
    
    def setUp(self):
        """Set up test environment using the monolithic app.py"""
        try:
            import app
            self.app = app.app
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
    
    def test_tc_auth_01_login_valid_credentials(self):
        """
        TC-AUTH-01: Login with valid credentials
        Input: Email, correct password
        Expected Result: Redirect to dashboard
        """
        print("\n🧪 Running TC-AUTH-01: Login with valid credentials")
        
        # Test data
        test_email = 'admin@exam.com'
        test_password = 'admin123'
        # Perform login request
        response = self.client.post('/login', data={
            'email': test_email,
            'password': test_password
        }, follow_redirects=False)
        # Accept both 302 and 308 as valid redirects
        self.assertIn(response.status_code, (302, 308), "Should redirect after successful login")
        self.assertIn('/dashboard', response.location, "Should redirect to dashboard")
        print("✅ TC-AUTH-01 PASSED: Valid credentials redirect to dashboard")
    
    def test_tc_auth_02_login_invalid_credentials(self):
        """
        TC-AUTH-02: Login with invalid credentials
        Input: Email, wrong password
        Expected Result: Show error: "Invalid credentials"
        """
        print("\n🧪 Running TC-AUTH-02: Login with invalid credentials")
        
        # Test cases for invalid credentials
        test_cases = [
            {
                'name': 'Wrong password',
                'email': 'admin@exam.com',
                'password': 'wrongpassword',
                'mock_admin': {
                    'id': 1,
                    'name': 'Test Admin',
                    'email': 'admin@exam.com',
                    'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS',
                    'role': 'admin',
                    'is_active': 1
                }
            },
            {
                'name': 'Non-existent user',
                'email': 'nonexistent@exam.com',
                'password': 'admin123',
                'mock_admin': None
            },
            {
                'name': 'Inactive user',
                'email': 'admin@exam.com',
                'password': 'admin123',
                'mock_admin': {
                    'id': 1,
                    'name': 'Test Admin',
                    'email': 'admin@exam.com',
                    'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS',
                    'role': 'admin',
                    'is_active': 0
                }
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(case=test_case['name']):
                # Perform login request
                response = self.client.post('/login', data={
                    'email': test_case['email'],
                    'password': test_case['password']
                }, follow_redirects=True)
                # Assertions
                self.assertEqual(response.status_code, 200, f"Should return login page for {test_case['name']}")
                response_data = response.get_data(as_text=True)
                expected_error = (
                    'Your account is inactive. Please contact the administrator.'
                    if test_case.get('name', '').lower().startswith('inactive')
                    else 'Invalid email or password'
                )
                self.assertIn(expected_error, response_data,
                              f"Should show error message for {test_case['name']}")
                print(f"✅ TC-AUTH-02 PASSED: {test_case['name']} shows error message")
    
    def test_tc_auth_03_logout_user(self):
        """
        TC-AUTH-03: Logout user
        Input: Click logout
        Expected Result: Return to login page
        """
        print("\n🧪 Running TC-AUTH-03: Logout user")
        
        # First, simulate a logged-in session
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['admin_name'] = 'Test Admin'
            sess['admin_email'] = 'admin@exam.com'
            sess['admin_role'] = 'admin'

        # Perform logout request
        response = self.client.get('/logout', follow_redirects=False)
        # Accept both 302 and 308 as valid redirects
        self.assertIn(response.status_code, (302, 308), "Should redirect after logout")
        self.assertIn('/login', response.location, "Should redirect to login page")
        # Verify session is cleared by trying to access a protected route
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertIn(response.status_code, (302, 308), "Should redirect when not logged in")
        self.assertIn('/login', response.location, "Should redirect to login page")
        print("✅ TC-AUTH-03 PASSED: Logout redirects to login page and clears session")
    
    def test_login_page_accessibility(self):
        """Test that login page is accessible"""
        print("\n🧪 Running additional test: Login page accessibility")
        
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200, "Login page should be accessible")
        
        response_data = response.get_data(as_text=True)
        self.assertIn('ExamSeat', response_data, "Should contain application title")
        self.assertIn('email', response_data, "Should contain email input")
        self.assertIn('password', response_data, "Should contain password input")
        self.assertIn('admin@exam.com', response_data, "Should show demo credentials")
        
        print("✅ Login page accessibility test PASSED")
    
    def test_protected_route_redirect(self):
        """Test that protected routes redirect to login when not authenticated"""
        print("\n🧪 Running additional test: Protected route redirect")
        
        protected_routes = ['/dashboard', '/students', '/subjects', '/rooms', '/exams']
        for route in protected_routes:
            with self.subTest(route=route):
                response = self.client.get(route, follow_redirects=False)
                self.assertIn(response.status_code, (302, 308), f"Route {route} should redirect when not authenticated")
                self.assertIn('/login', response.location, f"Route {route} should redirect to login")
        print("✅ Protected route redirect test PASSED")

class TestAuthenticationEdgeCases(unittest.TestCase):
    """Test edge cases and security aspects of authentication"""
    
    def setUp(self):
        """Set up test environment using the monolithic app.py"""
        try:
            import app
            self.app = app.app
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
    
    def test_empty_credentials(self):
        """Test login with empty credentials"""
        print("\n🧪 Running edge case test: Empty credentials")
        
        test_cases = [
            {'email': '', 'password': ''},
            {'email': 'admin@exam.com', 'password': ''},
            {'email': '', 'password': 'admin123'}
        ]
        
        for test_case in test_cases:
            with self.subTest(email=test_case['email'], password=test_case['password']):
                response = self.client.post('/login', data=test_case, follow_redirects=True)
                self.assertEqual(response.status_code, 200, "Should return login page for empty credentials")
        
        print("✅ Empty credentials test PASSED")
    
    def test_sql_injection_attempt(self):
        """Test SQL injection protection"""
        print("\n🧪 Running security test: SQL injection protection")
        # Attempt SQL injection
        malicious_email = "admin@exam.com'; DROP TABLE admins; --"
        response = self.client.post('/login', data={
            'email': malicious_email,
            'password': 'admin123'
        }, follow_redirects=True)
        # Should handle gracefully and not crash
        self.assertEqual(response.status_code, 200, "Should handle SQL injection attempt gracefully")
        print("✅ SQL injection protection test PASSED")

def run_authentication_tests():
    """Run all authentication tests with detailed output"""
    print("=" * 80)
    print("  EXAMINATION SEATING SYSTEM - AUTHENTICATION TEST SUITE")
    print("=" * 80)
    print()
    print("Testing authentication functionality based on test cases:")
    print("• TC-AUTH-01: Login with valid credentials")
    print("• TC-AUTH-02: Login with invalid credentials")
    print("• TC-AUTH-03: Logout user")
    print("• Additional security and edge case tests")
    print()
    print("-" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestAuthentication))
    test_suite.addTest(loader.loadTestsFromTestCase(TestAuthenticationEdgeCases))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    print("-" * 80)
    print()
    
    # Test Summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print("📊 TEST SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failures}")
    print(f"   🚨 Errors: {errors}")
    print()
    
    if result.wasSuccessful():
        print("🎉 ALL AUTHENTICATION TESTS PASSED!")
        print()
        print("✅ TC-AUTH-01: Login with valid credentials - PASSED")
        print("✅ TC-AUTH-02: Login with invalid credentials - PASSED") 
        print("✅ TC-AUTH-03: Logout user - PASSED")
        print("✅ Additional security tests - PASSED")
    else:
        print("❌ SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
                print(f"  • {test}: {error_msg}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                error_msg = traceback.split('\n')[-2]
                print(f"  • {test}: {error_msg}")
    
    print()
    print("=" * 80)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_authentication_tests()
    sys.exit(0 if success else 1)