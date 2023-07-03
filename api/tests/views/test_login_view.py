from django.urls import reverse
from model_mommy import mommy
from rest_framework import status

from ... import exceptions, models
from .base_view_test_case import BaseViewTestCase


class LoginUserTestCase(BaseViewTestCase):
    url = reverse("login-user")

    def test_unauthenticated_user_cant_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_not_registered_cant_login(self):
        self.authenticate()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, exceptions.SignUpRequired.status_code)
        self.assertEqual(
            response.data["detail"].code, exceptions.SignUpRequired.default_code
        )

    def test_user_is_doctor_can_login(self):
        mommy.make(models.Doctor, uuid=self.user.uid)
        self.authenticate()
        response = self.client.post(self.url)
        expected_data = {"user_uuid": str(self.user.uid), "is_doctor": True}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
