import unittest
from app import app, db, User
from flask import url_for

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # in-memory database
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user
        user = User(name='Test User', email='test@example.com', password='password')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_success(self):
        response = self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)

    def test_login_failure(self):
        response = self.client.post('/login', json={
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid credentials', response.data)

    def test_signup(self):
        response = self.client.post('/signup', data={
            'name': 'New User',
            'email': 'new@example.com',
            'password': 'newpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='new@example.com').first()
        self.assertIsNotNone(user)

