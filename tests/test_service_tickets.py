import unittest
from app import create_app, db
from app.models import User, ServiceTicket
from datetime import datetime

class TestServiceTicketRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Register and login to get token
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'phone': '123-456-7890'
        }
        
        # Register user
        self.client.post('/users/register', json=user_data)
        
        # Login to get token
        login_response = self.client.post('/users/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        self.token = login_response.json['token']

        # Test ticket data
        self.test_ticket_data = {
            'title': 'Test Ticket',
            'description': 'Test Description',
            'priority': 'high',
            'status': 'open'
        }
        
        self.user_id = login_response.json['user']['id']
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_ticket_success(self):
        """Test successful ticket creation"""
        response = self.client.post(
            '/service-tickets',
            json=self.test_ticket_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['title'], self.test_ticket_data['title'])
        self.assertEqual(response.json['user_id'], self.user_id)

    def test_create_ticket_unauthorized(self):
        """Test ticket creation without authentication"""
        response = self.client.post('/service-tickets', json=self.test_ticket_data)
        self.assertEqual(response.status_code, 401)

    def test_get_user_tickets(self):
        """Test retrieving user's tickets"""
        # First create a ticket
        self.client.post(
            '/service-tickets',
            json=self.test_ticket_data,
            headers=self.headers
        )
        
        # Then get all user's tickets
        response = self.client.get('/users/my-tickets', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['title'], self.test_ticket_data['title'])

    def test_update_ticket_success(self):
        """Test successful ticket update"""
        # Create a ticket
        create_response = self.client.post(
            '/service-tickets',
            json=self.test_ticket_data,
            headers=self.headers
        )
        ticket_id = create_response.json['id']
        
        # Update the ticket
        update_data = {'status': 'closed', 'priority': 'low'}
        response = self.client.put(
            f'/service-tickets/{ticket_id}',
            json=update_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], update_data['status'])
        self.assertEqual(response.json['priority'], update_data['priority'])

    def test_delete_ticket_success(self):
        """Test successful ticket deletion"""
        # Create a ticket
        create_response = self.client.post(
            '/service-tickets',
            json=self.test_ticket_data,
            headers=self.headers
        )
        ticket_id = create_response.json['id']
        
        # Delete the ticket
        response = self.client.delete(
            f'/service-tickets/{ticket_id}',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 204)