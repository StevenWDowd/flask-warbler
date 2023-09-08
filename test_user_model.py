"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError, DatabaseError
from psycopg2.errors import UniqueViolation

from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Tests the attributes of created users."""
        u1 = User.query.get(self.u1_id)

        # User should have no messages, no followers, and no liked messages
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)
        self.assertEqual(len(u1.messages_liked), 0)

    def test_is_followed_by(self):
        """Tests for a user being followed"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        u2.following.append(u1)
        self.assertEqual(u1.is_followed_by(u2), True)
        self.assertEqual(u2.is_followed_by(u1), False)

    def test_is_following(self):
        """Tests for a user following another user"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        u2.following.append(u1)
        self.assertEqual(u1.is_following(u2), False)
        self.assertEqual(u2.is_following(u1), True)

    def test_valid_user_signup(self):
        """Tests signup function correctly handles new users.
        """
        u3 = User.signup("u3", "u3@email.com", "password", None)
        self.assertIsInstance(u3, User)
        self.assertEqual(u3.username, "u3")
        self.assertEqual(u3.email, "u3@email.com")
        self.assertEqual(u3.password[0:3], "$2b")


    def test_invalid_user_signup(self):
        """Tests signup function handling of duplicate, improper,
        or missing data."""
        with self.assertRaises(IntegrityError):
            User.signup("u4", "u1@email.com", "password", None)
            db.session.commit()

        with self.assertRaises(ValueError):
            User.signup("u5", "password", None)
            db.session.commit()


    def test_duplicate_username_signup(self):
        """Tests attempted signup with an already-taken username."""
        with self.assertRaises(IntegrityError):
            User.signup("u1", "u5@email.com", "password", None)
            db.session.commit()


    def test_valid_user_authenticate(self):
        """Tests user authentication function with valid inputs."""

        u1 = User.authenticate("u1", "password")

        self.assertIsInstance(u1, User)
        self.assertEqual(u1.username, "u1")
        self.assertEqual(u1.email, "u1@email.com")
        self.assertEqual(u1.password[0:3], "$2b")

    def test_invalid_user_authenticate(self):
        """Test user authentication with invalid username and password
        inputs."""

        u1 = User.authenticate("u1", "password")

        self.assertEqual(User.authenticate("u4", "password"), False)
        self.assertEqual(User.authenticate("u1", "12345678"), False)