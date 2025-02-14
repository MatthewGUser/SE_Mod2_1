import unittest
import warnings
from sqlalchemy import select
from app import create_app, db
from app.models import User, Part

# Filter out SQLAlchemy warnings
warnings.filterwarnings('ignore', category=Warning)

class TestInventoryRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Suppress warnings for tests
        warnings.simplefilter("ignore")
        
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

        # Create test part data
        self.part_data = {
            'name': 'Test Part',
            'part_number': 'TP001',
            'price': 99.99,
            'quantity': 10
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

    def test_create_part_success(self):
        """Test successful part creation by admin"""
        # Login as admin
        login_response = self.client.post('/users/login', 
            json={
                'email': self.admin_data['email'],
                'password': self.admin_data['password']
            })
        token = login_response.json['token']
        
        # Create part
        response = self.client.post(
            '/inventory',  # URL without trailing slash
            json=self.part_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

    def test_create_part_unauthorized(self):
        """Test part creation by non-admin user"""
        # Create and register regular user
        user_data = {
            'name': 'Regular User',
            'email': 'user@example.com',
            'password': 'UserPass123!',
            'phone': '111-222-3333'
        }
        
        # Register user using correct endpoint
        register_response = self.client.post(
            '/users',  # Changed from '/users/register' to '/users'
            json=user_data
        )
        self.assertEqual(register_response.status_code, 201)
        
        # Login as regular user
        login_response = self.client.post(
            '/users/login',
            json={
                'email': user_data['email'],
                'password': user_data['password']
            }
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json['token']
        
        # Attempt to create part
        response = self.client.post(
            '/inventory',
            json=self.part_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 403)

    def test_get_inventory(self):
        """Test retrieving inventory list"""
        # Login as admin
        login_data = {
            'email': self.admin_data['email'],
            'password': self.admin_data['password']
        }
        login_response = self.client.post('/users/login', json=login_data)
        token = login_response.json['token']

        # Create a part
        create_response = self.client.post(
            '/inventory',
            json=self.part_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(create_response.status_code, 201)

        # Get parts list
        response = self.client.get('/inventory')
        self.assertEqual(response.status_code, 200)

        # Test pagination
        response = self.client.get('/inventory?page=1&per_page=10')
        self.assertEqual(response.status_code, 200)

    def test_update_part(self):
        """Test updating part details"""
        # Get login token
        login_response = self.client.post('/users/login', 
            json={
                'email': self.admin_data['email'],
                'password': self.admin_data['password']
            })
        token = login_response.json['token']

        # Create a part first
        create_response = self.client.post(
            '/inventory',
            json=self.part_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        
        part_id = create_response.json['id']
        update_data = {
            'name': 'Updated Part',
            'price': 199.99
        }
        
        # Update the part
        response = self.client.put(
            f'/inventory/{part_id}',
            json=update_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], update_data['name'])
        self.assertEqual(float(response.json['price']), update_data['price'])

    def test_delete_part(self):
        """Test deleting a part"""
        # Login as admin
        login_response = self.client.post('/users/login', 
            json={
                'email': self.admin_data['email'],
                'password': self.admin_data['password']
            })
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json['token']
        
        # Create a part first
        create_response = self.client.post(
            '/inventory',  # Updated endpoint
            json=self.part_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertIn('id', create_response.json)
        part_id = create_response.json['id']
        
        # Delete the part
        delete_response = self.client.delete(
            f'/inventory/{part_id}',  # Updated endpoint
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify part is deleted
        get_response = self.client.get(f'/inventory/{part_id}')  # Updated endpoint
        self.assertEqual(get_response.status_code, 404)