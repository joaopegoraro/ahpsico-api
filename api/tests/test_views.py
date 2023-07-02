import os
import uuid
from unittest import mock

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from model_mommy import mommy
from rest_framework import status
from rest_framework.test import APITestCase

from .. import exceptions, models, views


class BaseViewTestCase(APITestCase):
    user = mock.MagicMock(uid=uuid.uuid4())

    def authenticate(self):
        self.client.force_authenticate(user=self.user)


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


class RegisterUserTestCase(BaseViewTestCase):
    url = reverse("register-user")

    def test_unauthenticated_user_cant_signup(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_doctor_already_registered_cant_signup(self):
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        self.authenticate()
        request_data = {"name": doctor.name, "is_doctor": True}
        response = self.client.post(self.url, request_data)
        self.assertEqual(
            response.status_code, exceptions.UserAlreadyRegistered.status_code
        )
        self.assertEqual(
            response.data["detail"].code, exceptions.UserAlreadyRegistered.default_code
        )

    def test_patient_already_registered_cant_signup(self):
        patient = mommy.make(models.Patient, uuid=self.user.uid)
        self.authenticate()
        request_data = {"name": patient.name, "is_doctor": True}
        response = self.client.post(self.url, request_data)
        self.assertEqual(
            response.status_code, exceptions.UserAlreadyRegistered.status_code
        )
        self.assertEqual(
            response.data["detail"].code, exceptions.UserAlreadyRegistered.default_code
        )

    def test_doctor_not_registered_can_signup(self):
        doctor = mommy.prepare(models.Doctor, uuid=self.user.uid)
        self.assertFalse(models.Doctor.objects.filter(pk=doctor.pk).exists())
        self.authenticate()
        request_data = {"name": doctor.name, "is_doctor": True}
        response = self.client.post(self.url, request_data)
        expected_data = {"user_uuid": str(self.user.uid)}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
        saved_doctor = models.Doctor.objects.get(pk=doctor.pk)
        self.assertEqual(saved_doctor.pk, self.user.uid)

    def test_patient_not_registered_can_signup(self):
        patient = mommy.prepare(models.Patient, uuid=self.user.uid)
        self.assertFalse(models.Patient.objects.filter(pk=patient.pk).exists())
        self.authenticate()
        request_data = {"name": patient.name, "is_doctor": False}
        response = self.client.post(self.url, request_data)
        expected_data = {"user_uuid": str(self.user.uid)}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
        saved_patient = models.Patient.objects.get(pk=patient.pk)
        self.assertEqual(saved_patient.pk, self.user.uid)
