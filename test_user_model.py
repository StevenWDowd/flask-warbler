"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
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
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_is_followed_by(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        u2.following.append(u1)
        self.assertEqual(u1.is_followed_by(u2), True)
        self.assertEqual(u2.is_followed_by(u1), False)

    def test_is_following(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        u2.following.append(u1)
        self.assertEqual(u1.is_following(u2), False)
        self.assertEqual(u2.is_following(u1), True)

    def test_user_signup(self):
        u3 = User.signup("u3", "u3@email.com", "password", None)
        u4 = User.signup("u4", "u3@email.com", "password", None)
        self.assertIsInstance(u3, User)
        with self.assertRaises(IntegrityError):
            u4 = User.signup("u4", "u3@email.com", "password", None)
