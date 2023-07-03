import os
import uuid
from unittest import mock

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from model_mommy import mommy
from rest_framework import exceptions as rest_exceptions
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


class InviteUserTestCase(BaseViewTestCase):
    list_url = reverse("invites-list")

    def accept_url(self, pk):
        return reverse("invites-accept", kwargs={"pk": pk})

    def test_unauthenticated_user_cant_invite(self):
        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_request_cant_create_invite(self):
        self.authenticate()
        mommy.make(models.Doctor, uuid=self.user.uid)
        phone_number = "1234"
        request_data = {"some_other_thing_that_is_not_phone_number": phone_number}
        response = self.client.post(self.list_url, request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_is_not_doctor_cant_create_invite(self):
        self.authenticate()
        mommy.make(models.Patient, uuid=self.user.uid)
        phone_number = "1234"
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.list_url, request_data)
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_phone_number_not_tied_to_any_patient_cant_create_invite(self):
        self.authenticate()
        mommy.make(models.Doctor, uuid=self.user.uid)
        phone_number = "1234"
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.list_url, request_data)
        self.assertEqual(
            response.status_code, exceptions.PatientNotRegistered.status_code
        )
        self.assertEqual(
            response.data["detail"].code, exceptions.PatientNotRegistered.default_code
        )

    def test_user_doctor_with_correct_request_creates_invite(self):
        self.authenticate()
        mommy.make(models.Doctor, uuid=self.user.uid)
        phone_number = "1234"
        mommy.make(models.Patient, phone_number=phone_number)
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.list_url, request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_doctor_with_request_to_own_patient_cant_create_invite(self):
        self.authenticate()
        phone_number = "1234"
        request_data = {"phone_number": phone_number}
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patient = mommy.make(models.Patient, phone_number=phone_number)
        patient.doctors.add(doctor)
        response = self.client.post(self.list_url, request_data)
        self.assertEqual(
            response.status_code, exceptions.PatientAlreadyWithDoctor.status_code
        )
        self.assertEqual(
            response.data["detail"].code,
            exceptions.PatientAlreadyWithDoctor.default_code,
        )

    def test_user_doctor_with_correct_request_creates_invite(self):
        self.authenticate()
        mommy.make(models.Doctor, uuid=self.user.uid)
        phone_number = "1234"
        mommy.make(models.Patient, phone_number=phone_number)
        self.assertFalse(
            models.Invite.objects.filter(phone_number=phone_number).exists()
        )
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.list_url, request_data)
        self.assertTrue(
            models.Invite.objects.filter(phone_number=phone_number).exists()
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_not_the_invite_patient_cant_accept_invite(self):
        self.authenticate()
        mommy.make(models.Patient, uuid=self.user.uid)
        doctor = mommy.make(models.Doctor)
        phone_number = "1234"
        patient = mommy.make(models.Patient, phone_number=phone_number)
        invite = mommy.prepare(models.Invite, phone_number=phone_number)
        invite.doctor = doctor
        invite.patient = patient
        invite.save()
        self.assertTrue(models.Invite.objects.filter(pk=invite.pk).exists())
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.accept_url(invite.id), request_data)
        self.assertTrue(models.Invite.objects.filter(pk=invite.pk).exists())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_invite_patient_can_accept_invite(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor)
        phone_number = "1234"
        patient = mommy.make(
            models.Patient, phone_number=phone_number, uuid=self.user.uid
        )
        invite = mommy.prepare(models.Invite, phone_number=phone_number)
        invite.doctor = doctor
        invite.patient = patient
        invite.save()
        self.assertTrue(models.Invite.objects.filter(pk=invite.pk).exists())
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.accept_url(invite.id), request_data)
        self.assertFalse(models.Invite.objects.filter(pk=invite.pk).exists())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
