import unittest
from app import create_app, db
from app.models import User

class TestUserRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Test user data
        self.test_user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '111-222-3333',
            'password': 'TestPass123!'
        }

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_and_login(self):
        """Helper method to register and login a user"""
        # Register
        self.client.post('/users/register', json=self.test_user_data)
        
        # Login
        login_response = self.client.post('/users/login', json={
            'email': self.test_user_data['email'],
            'password': self.test_user_data['password']
        })
        return login_response.json['token']

    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post('/users/register', json=self.test_user_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('user', response.json)
        self.assertEqual(response.json['user']['email'], self.test_user_data['email'])

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # First registration
        self.client.post('/users/register', json=self.test_user_data)
        
        # Second registration with same email
        response = self.client.post('/users/register', json=self.test_user_data)
        self.assertEqual(response.status_code, 409)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['message'], 'This email is already in use')

    def test_login_success(self):
        """Test successful login"""
        # First register a user
        self.client.post('/users/register', json=self.test_user_data)
        
        # Then try to login
        login_data = {
            'email': self.test_user_data['email'],
            'password': self.test_user_data['password']
        }
        response = self.client.post('/users/login', json=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)
        self.assertIn('user', response.json)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'wrong@example.com',
            'password': 'WrongPass123!'
        }
        response = self.client.post('/users/login', json=login_data)
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)

    def test_get_user_success(self):
        """Test successful user retrieval"""
        # Register and login
        token = self.register_and_login()
        user_id = 1  # First user in test database
        
        # Get user details
        response = self.client.get(
            f'/users/{user_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], self.test_user_data['email'])
        self.assertEqual(response.json['name'], self.test_user_data['name'])

    def test_get_user_unauthorized(self):
        """Test user retrieval without authentication"""
        response = self.client.get('/users/1')
        self.assertEqual(response.status_code, 401)