"""User view function tests"""
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, session, g
from werkzeug.exceptions import Unauthorized
from unittest import TestCase
from sqlalchemy.exc import IntegrityError, DatabaseError

from models import db, User, Message, Follow
from forms import CSRFForm



# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

app.config['WTF_CSRF_ENABLED'] = False

#app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

load_dotenv()

CURR_USER_KEY = "curr_user"

db.drop_all()
db.create_all()

class UserViewTestCase(TestCase):
    """Test case for the user-related view functions."""
    def setUp(self):
        User.query.delete()
        app.config["SECRET_KEY"] = "secret"

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        u3 = User.signup("u3", "u3@email.com", "password", None)
        u1.location = "Buffalo, NY"

        msg1 = Message(text="test text 1")
        u1.messages.append(msg1)

        msg2 = Message(text="test text 2")
        u2.messages.append(msg2)

        msg3 = Message(text="test text 3")
        u3.messages.append(msg3)

        #add a message to messages_liked lists of u1 and u2
        u1.messages_liked.append(msg2)
        u2.messages_liked.append(msg1)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u3_id = u3.id
        self.msg1_id = msg1.id
        self.msg2_id = msg2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_add_user_to_g_logged_out(self):
        """Test a logged out user is removed from g"""

        with self.client as c:
            resp = c.get("/")
            self.assertEqual(g.user, None)

    def test_add_user_to_g_logged_in(self):
        """Tests g.user is the logged in user"""

        u1 = User.query.get(self.u1_id)

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.get("/")
            self.assertEqual(g.user, u1)

    def test_csrf_from_in_g(self):
        """Tests csrf form is added to g"""

        with self.client as c:
            resp = c.get("/")
            self.assertIsInstance(g.csrf_form, CSRFForm)

    # def test_do_login(user="random_id"):
    #     """Test the do_login helper function."""
    #     with self.client.session_transaction() as session:

    #         assertEqual(session[CURR_USER_KEY], "random_id")

    def test_signup_get_logged_out(self):
        """Test signup route when logged out."""

        with self.client as c:
            resp = c.get("/signup")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Sign me up!", html)

    def test_signup_get_logged_in(self):
        """Test signup route when logged in."""

        u1 = User.query.get(self.u1_id)

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.get("/signup", follow_redirects=True)
            html = resp.get_data(as_text = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Profile", html)

    def test_signup_post(self):
        """Test submitting a form to the signup route."""
        with self.client as c:
            resp = c.post("/signup", data={"username":"user3",
                                           "email":"user3@email.com",
                                           "password": "password"},
                                           follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("user3", html)

    def test_signup_post_taken_username(self):
        """Test submitting a signup form with a username that has
        been taken already."""
        with self.client as c:
            resp = c.post("/signup", data={"username":"u1",
                                           "email":"user3@email.com",
                                           "password": "password"},
                                           follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", html)

    def test_login_fails(self):
        """Test user who logs in with invalid password fails"""

        with self.client as c:
            resp = c.post("/login", data={"username": "u1",
                                          "password": "1234567"},
                                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", html)

    def test_login_succeeds(self):
        """Test a user successful login"""
        with self.client as c:
            resp = c.post("/login", data={"username": "u1",
                                          "password": "password"},
                                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, u1!", html)

    def test_login_get(self):
        """Tests login page loads"""

        with self.client as c:
            resp = c.get("/login")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Welcome back.", html)

    def test_successful_logout(self):
        """Tests a successful logout"""

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.post("/logout", data={}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Successfully logged out", html)

    def test_list_users(self):
        """Tests showing the list of all users"""

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("col-lg-4 col-md-6 col-12", html)

    def test_show_user_logged_in(self):
        """Test the showing of a single user when logged in."""

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.get(f"/users/{self.u1_id}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Buffalo, NY", html)

    def test_show_following(self):
        """Test the showing of the users a user is following"""
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u1.following.append(u2)
        db.session.commit()

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.get(f"/users/{self.u1_id}/following")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("u2", html)

    def test_show_followers(self):
        """Test showing of the users who follow a user."""
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u1.following.append(u2)
        db.session.commit()

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.get(f"/users/{self.u2_id}/followers")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("u1", html)

    def test_start_following(self):
        """Test function for a user to begin following another user."""

        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.u1_id

        with self.client as c:
            resp = c.post(f"/users/follow/{self.u2_id}")













