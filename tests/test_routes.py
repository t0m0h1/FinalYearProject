import unittest
from app import app, db, User

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Add a test user
        self.user = User(name='Test User', email='test2@example.com', password='password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        return self.client.post('/login', json={
            'email': 'test2@example.com',
            'password': 'password'
        })

    def test_access_protected_route_without_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login page

    def test_access_protected_route_with_login(self):
        self.login()
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'chatbot', response.data)  # Depends on your homepage contents

