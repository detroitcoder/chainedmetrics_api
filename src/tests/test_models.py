from unittest import TestCase
from app.models import User

class TestModels(TestCase):

    def test_password_hash(self):
        user = User(email='test@gmail.com', admin=True, active=True, first_name='michael', last_name='watson')
        user.set_password('password')
        self.assertTrue(user.check_password('password'))