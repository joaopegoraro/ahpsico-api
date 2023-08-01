import uuid
from unittest import mock

from rest_framework.test import APITestCase


class BaseViewTestCase(APITestCase):
    user = mock.MagicMock(uid=uuid.uuid4(), phone_number="1234567890")
    maxDiff = None

    def authenticate(self):
        self.client.force_authenticate(user=self.user)
