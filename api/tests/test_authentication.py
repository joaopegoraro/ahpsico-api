import os
from unittest import mock

from django.test import RequestFactory, TestCase

from .. import exceptions
from ..authentication import FirebaseAuthentication


class FirebaseAuthenticationTestCase(TestCase):
    def setUp(self) -> None:
        token = os.environ.get("DUMMY_FIREBASE_TOKEN")
        self.token_header = {"Authorization": "Bearer " + token}
        self.firebase_user = {"uid": "12345"}

    def test_no_auth_header_should_fail(self):
        factory = RequestFactory()
        request = factory.get("/")
        auth = FirebaseAuthentication()
        with self.assertRaises(exceptions.NoAuthToken):
            auth.authenticate(request)

    @mock.patch("firebase_admin.auth.verify_id_token", side_effect=Exception())
    def test_invalid_token_should_fail(self, verify_id_token):
        factory = RequestFactory()
        request = factory.get("/", **self.token_header)
        auth = FirebaseAuthentication()
        with self.assertRaises(exceptions.InvalidAuthToken):
            auth.authenticate(request)

    @mock.patch("firebase_admin.auth.verify_id_token")
    def test_user_retrieval_error_should_fail(self, verify_id_token):
        verify_id_token.return_value = self.firebase_user
        factory = RequestFactory()

        request = factory.get("/", **self.token_header)

        auth = FirebaseAuthentication()
        with self.assertRaises(exceptions.FirebaseError):
            auth.authenticate(request)

    @mock.patch("firebase_admin.auth.verify_id_token")
    @mock.patch("firebase_admin.auth.get_user")
    def test_successful_authentication_returns_user(self, verify_id_token, get_user):
        verify_id_token.return_value = self.firebase_user
        get_user.return_value = self.firebase_user
        factory = RequestFactory()

        request = factory.get("/", **self.token_header)

        try:
            auth = FirebaseAuthentication()
            user = auth.authenticate(request)
            expected_return = (self.firebase_user, None)
            self.assertEqual(user, expected_return)
        except Exception as e:
            self.fail(e)
