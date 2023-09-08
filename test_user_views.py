"""User view function tests"""
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, session, g
from werkzeug.exceptions import Unauthorized
from unittest import TestCase
from sqlalchemy.exc import IntegrityError, DatabaseError

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
        with self.client as c:
            resp = c.get("/")
            self.assertEqual(g.user, None)

    def test_add_user_to_g_logged_in(self):
        session[CURR_USER_KEY] = self.u1_id
        u1 = User.query.get(self.u1_id)

        with self.client as c:
            resp = c.get("/")
            self.assertEqual(g.user, u1)


