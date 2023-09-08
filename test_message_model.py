import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Like

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

class MessageModelTestCase(TestCase):

    def setUp(self):
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        msg1 = Message(text="test text 1")
        u1.messages.append(msg1)

        msg2 = Message(text="test text 2")
        u2.messages.append(msg2)

        #add a message to each user's messages_liked list
        u1.messages_liked.append(msg2)
        u2.messages_liked.append(msg1)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.msg1_id = msg1.id
        self.msg2_id = msg2.id

    def tearDown(self):
        db.session.rollback()

    def test_message_is_created(self):
        """ Tests the attributes of created messages"""

        msg1 = Message.query.get(self.msg1_id)
        u1 = User.query.get(self.u1_id)

        self.assertEqual(msg1.user_id, u1.id)
        self.assertEqual(msg1.text, "test text 1")

    def test_invalid_text_in_message(self):
        """Test for invalid inputs to message text """

        u1 = User.query.get(self.u1_id)

        with self.assertRaises(TypeError):
            msg3 = Message(3)
            u1.messages.append(msg3)
            db.session.commit()

    def test_invalid_missing_text_message(self):
        """Tests an invalid message with no text."""

        u1 = User.query.get(self.u1_id)

        with self.assertRaises(IntegrityError):
            msg3 = Message()
            u1.messages.append(msg3)
            db.session.commit()

    def test_user_for_valid_messages(self):
        """Tests a user for their messages"""
        u1 = User.query.get(self.u1_id)
        msg3 = Message(text="test text 3")
        u1.messages.append(msg3)
        db.session.commit()

        self.assertEqual(u1.messages[0].id, self.msg1_id)
        self.assertEqual(len(u1.messages), 2)
        self.assertIn(msg3, u1.messages)
        self.assertEqual(msg3.user, u1)

    def test_user_for_invalid_messages(self):
        """Test a user does not have messages by another user"""

        u1 = User.query.get(self.u1_id)
        msg2 = Message.query.get(self.msg2_id)

        self.assertNotIn(msg2, u1.messages)
        self.assertNotEqual(msg2.user, u1)

    def test_liked_messages(self):
        """Test relationship of a like between a user and a message."""
        like1 = Like.query.get((self.u1_id, self.msg2_id))
        u1 = User.query.get(self.u1_id)
        msg2 = Message.query.get(self.msg2_id)

        self.assertIn(msg2, u1.messages_liked)
        self.assertIn(u1, msg2.users_who_liked)
        self.assertEqual(u1.id, like1.user_id)
        self.assertEqual(msg2.id, like1.message_id)

    def test_invalid_like(self):
        """Test to ensure that no like relationship exists between a message
        and user if that user did not like that message."""
        like1 = Like.query.get((self.u1_id, self.msg2_id))
        u2 = User.query.get(self.u2_id)
        msg2 = Message.query.get(self.msg2_id)

        self.assertNotEqual(u2.id, like1.user_id)
        self.assertNotEqual(self.msg1_id, like1.message_id)
        self.assertNotIn(msg2, u2.messages_liked)
        self.assertNotIn(u2, msg2.users_who_liked)

#tests:
    #if message is assocated with creator (user.messages)
    #match Messsage.user_id to user.id

    #if a user's message is associated with them

    #if we add a new message its output is as expected

    #test if we can create an empty message


