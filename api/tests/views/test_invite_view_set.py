import json

from django.urls import reverse
from model_mommy import mommy
from rest_framework import exceptions as rest_exceptions
from rest_framework import status

from ... import exceptions, models
from .base_view_test_case import BaseViewTestCase


class InviteViewSetTestCase(BaseViewTestCase):
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

    def test_invite_already_sent_cant_be_created(self):
        self.authenticate()
        patient = mommy.make(models.Patient)
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        invite = mommy.make(
            models.Invite,
            phone_number=patient.phone_number,
            doctor=doctor,
            patient=patient,
        )
        saved_invite = models.Invite.objects.get(
            doctor__pk=doctor.pk, phone_number=invite.phone_number
        )
        request_data = {"phone_number": invite.phone_number}
        response = self.client.post(self.list_url, request_data)
        self.assertEqual(response.status_code, exceptions.InviteAlreadySent.status_code)
        self.assertEqual(
            response.data["detail"].code, exceptions.InviteAlreadySent.default_code
        )

    def test_user_has_no_invite_information_cant_retrieve_invites(self):
        self.authenticate()
        mommy.make(models.Patient, uuid=self.user.uid)
        detail_url = reverse("invites-list")
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, exceptions.NoInviteFound.status_code)
        self.assertEqual(
            response.data["detail"].code, exceptions.NoInviteFound.default_code
        )

    def test_user_has_invite_information_can_retrieve_invites(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Jaime", phone_number="123")
        patient = mommy.make(models.Patient, uuid=self.user.uid, phone_number="1234")
        patient.doctors.add(doctor)
        invite = mommy.make(
            models.Invite,
            patient=patient,
            doctor=doctor,
            phone_number=patient.phone_number,
        )
        detail_url = reverse("invites-list")
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                "id": invite.id,
                "doctor": {
                    "uuid": str(doctor.pk),
                    "name": doctor.name,
                    "description": doctor.description,
                },
                "patient": str(patient.pk),
                "phone_number": patient.phone_number,
            }
        ]
        self.assertEqual(json.dumps(response.data), json.dumps(expected_data))

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
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        phone_number = "1234"
        patient = mommy.make(models.Patient, phone_number=phone_number)
        self.assertFalse(
            models.Invite.objects.filter(phone_number=phone_number).exists()
        )
        request_data = {"phone_number": phone_number}
        response = self.client.post(self.list_url, request_data)
        expected_data = {
            "id": 1,
            "doctor": {
                "uuid": str(doctor.pk),
                "name": doctor.name,
                "description": doctor.description,
            },
            "patient": str(patient.pk),
            "phone_number": phone_number,
        }
        self.assertEqual(response.data, json.dumps(expected_data))
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
