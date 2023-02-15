import os
from unittest import TestCase

from datetime import date
 
from books_app.extensions import app, db, bcrypt
from books_app.models import Book, Author, User, Audience

"""
Run these tests with the command:
python -m unittest books_app.main.tests
"""

#################################################
# Setup
#################################################

def create_books():
    a1 = Author(name='Harper Lee')
    b1 = Book(
        title='To Kill a Mockingbird',
        publish_date=date(1960, 7, 11),
        author=a1
    )
    db.session.add(b1)

    a2 = Author(name='Sylvia Plath')
    b2 = Book(title='The Bell Jar', author=a2)
    db.session.add(b2)
    db.session.commit()

def create_user():
    password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
    user = User(username='me1', password=password_hash)
    db.session.add(user)
    db.session.commit()

#################################################
# Tests
#################################################

class AuthTests(TestCase):
    """Tests for authentication (login & signup)."""
 
    def setUp(self):
        """Executed prior to each test."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def test_signup(self):
        post_data = {
            'username': 'josh',
            'password': 'password'
        }
        self.app.post('/signup', data=post_data)
        added_user = User.query.filter_by(username='josh').one()
        self.assertEqual('josh', added_user.username)

    def test_signup_existing_user(self):
        create_user()

        post_data = {
            'username': 'me1',
            'password': 'password'
        }

        response = self.app.post('/signup', data=post_data)
        response_text = response.get_data(as_text=True)

        self.assertIn('That username is taken. Please choose a different one.', response_text)
        user_list = User.query.filter_by(username='me1').all()
        # confirm that only one user with username me1 is in the database
        self.assertEqual(1, len(user_list))


    def test_login_correct_password(self):
        create_user()

        post_data = {
            'username': 'me1',
            'password': 'password'
        }

        response = self.app.post('/login', data=post_data, follow_redirects=True)
        # check that login was succesful
        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)
        #check that the login button is not displayed
        self.assertNotIn('<a href="/login">Log In</a>', response_text)

    def test_login_nonexistent_user(self):
        post_data = {
            'username': 'fake_user',
            'password': 'very secure password'
        }

        response = self.app.post('/login', data=post_data)
        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)
        #check that error message is displayed
        self.assertIn('No user with that username. Please try again.', response_text)
        #check that the login form itself is displayed
        self.assertIn('<form action="/login" method="POST">', response_text)

    def test_login_incorrect_password(self):
        create_user()

        post_data = {
            'username': 'me1',
            'password': 'incorrect_password'
        }

        response = self.app.post('/login', data=post_data)
        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)
        #check that error message is displayed
        #seems that at some point along the way the apostrophe is converted
        #to its decimel character reference (&#39;)
        self.assertIn("Password doesn&#39;t match. Please try again.", response_text)
        #check that the login form itself is displayed
        self.assertIn('<form action="/login" method="POST">', response_text)

    def test_logout(self):
        create_user()

        post_data = {
            'username': 'me1',
            'password': 'password'
        }

        response = self.app.post('/login', data=post_data, follow_redirects=True)
        # check that login was succesful
        self.assertEqual(response.status_code, 200)

        get_response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_text = get_response.get_data(as_text=True)
        self.assertIn(' <a href="/login">Log In</a>', response_text)

