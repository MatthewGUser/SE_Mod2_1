import unittest
from app import create_app, db
from app.models import User, Mechanic, ServiceTicket

class TestMechanicRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test admin user data
        self.admin_data = {
            'name': 'Admin User',
            'email': 'admin@example.com',
            'password': 'AdminPass123!',
            'phone': '123-456-7890',
            'is_admin': True
        }

        # Create test mechanic data - removed email field
        self.mechanic_data = {
            'name': 'Test Mechanic',
            'phone': '098-765-4321',
            'specialty': 'Engine Repair'
        }
        
        # Create admin user for tests
        admin_user = User(
            name=self.admin_data['name'],
            email=self.admin_data['email'],
            phone=self.admin_data['phone'],
            is_admin=True
        )
        admin_user.set_password(self.admin_data['password'])
        db.session.add(admin_user)
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_mechanic_success(self):
        """Test successful mechanic creation by admin"""
        # Login as admin first
        login_response = self.client.post('/users/login', 
            json={
                'email': self.admin_data['email'],
                'password': self.admin_data['password']
            })
        token = login_response.json['token']
        
        # Create mechanic
        response = self.client.post(
            '/mechanics',
            json={
                'name': 'Test Mechanic',
                'specialty': 'Engine Repair',
                'phone': '123-456-7890'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

    def test_create_mechanic_unauthorized(self):
        """Test mechanic creation by non-admin user"""
        # Register regular user
        user_data = {
            'name': 'Regular User',
            'email': 'user@example.com',
            'password': 'UserPass123!',
            'phone': '111-222-3333'
        }
        
        # Register and login
        self.client.post('/users/register', json=user_data)
        login_response = self.client.post('/users/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        token = login_response.json['token']
        
        # Attempt to create mechanic
        response = self.client.post(
            '/mechanics',
            json=self.mechanic_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 403)

    def test_get_mechanics(self):
        """Test retrieving list of mechanics"""
        # Login as admin
        login_response = self.client.post('/users/login', 
            json={
                'email': self.admin_data['email'],
                'password': self.admin_data['password']
            })
        token = login_response.json['token']
        
        # Create a mechanic first
        create_response = self.client.post(
            '/mechanics',
            json={
                'name': self.mechanic_data['name'],
                'phone': self.mechanic_data['phone'],
                'specialty': self.mechanic_data['specialty']
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(create_response.status_code, 201)
        
        # Get mechanics list
        response = self.client.get('/mechanics')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mechanics', response.json)
        
        # Verify mechanic data - removed email check
        mechanic = response.json['mechanics'][0]
        self.assertEqual(mechanic['name'], self.mechanic_data['name'])
        self.assertEqual(mechanic['phone'], self.mechanic_data['phone'])
        self.assertEqual(mechanic['specialty'], self.mechanic_data['specialty'])

    def test_assign_mechanic_to_ticket(self):
        """Test assigning mechanic to service ticket"""
        # Login as admin
        login_response = self.client.post('/users/login', 
            json={
                'email': self.admin_data['email'],
                'password': self.admin_data['password']
            })
        token = login_response.json['token']
        
        # Create mechanic
        mechanic_response = self.client.post(
            '/mechanics',
            json=self.mechanic_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(mechanic_response.status_code, 201)
        mechanic_id = mechanic_response.json['id']
        
        # Create ticket
        ticket_data = {
            'title': 'Test Ticket',
            'description': 'Test Description',
            'priority': 'high',
            'status': 'open'
        }
        ticket_response = self.client.post(
            '/service-tickets',
            json=ticket_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(ticket_response.status_code, 201)
        ticket_id = ticket_response.json['id']
        
        # Assign mechanic to ticket
        assign_response = self.client.post(
            f'/mechanics/{mechanic_id}/tickets/{ticket_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(assign_response.status_code, 200)
        
        # Verify assignment - use mechanic endpoint instead
        get_response = self.client.get(
            f'/mechanics/{mechanic_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertIn(ticket_id, [t for t in get_response.json.get('tickets', [])])