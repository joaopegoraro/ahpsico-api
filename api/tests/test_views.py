import json
import os
import uuid
from unittest import mock

from django.urls import reverse
from django.utils.timezone import datetime, timedelta, timezone
from model_mommy import mommy
from rest_framework import exceptions as rest_exceptions
from rest_framework import status
from rest_framework.test import APITestCase

from .. import enums, exceptions, models, utils


class BaseViewTestCase(APITestCase):
    user = mock.MagicMock(uid=uuid.uuid4(), phone_number="1234567890")
    maxDiff = None

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

    def test_user_has_no_invite_information_cant_retreive_invite(self):
        self.authenticate()
        mommy.make(models.Patient, uuid=self.user.uid)
        invite = mommy.make(models.Invite)
        detail_url = reverse("invites-detail", kwargs={"pk": invite.id})
        response = self.client.get(detail_url)
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_user_has_invite_information_can_retreive_invite(self):
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
        detail_url = reverse("invites-detail", kwargs={"pk": invite.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "id": invite.id,
            "doctor": {
                "uuid": str(doctor.pk),
                "name": doctor.name,
            },
            "patient": str(patient.pk),
            "phone_number": patient.phone_number,
        }
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


class DoctorViewSetTestCase(BaseViewTestCase):
    patients_url = "doctors-patients"
    sessions_url = "doctors-sessions"
    advices_url = "doctors-advices"

    def test_unauthenticated_user_cant_list_patients(self):
        response = self.client.get(
            reverse(self.patients_url, kwargs={"pk": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cant_list_sessions(self):
        response = self.client.get(
            reverse(self.sessions_url, kwargs={"pk": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cant_list_advices(self):
        response = self.client.get(
            reverse(self.advices_url, kwargs={"pk": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_has_uid_different_to_passed_pk_cant_list_patients(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patients = mommy.make(
            models.Patient, _quantity=2, _fill_optional=["phone_number"]
        )
        for patient in patients:
            patient.doctors.add(doctor)
        self.assertEqual(
            models.Patient.objects.filter(doctors__pk=self.user.uid).count(), 2
        )
        response = self.client.get(
            reverse(self.patients_url, kwargs={"pk": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_has_uid_equal_to_passed_pk_can_list_patients(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patients = mommy.make(
            models.Patient, _quantity=2, _fill_optional=["phone_number"]
        )
        for patient in patients:
            patient.doctors.add(doctor)
        self.assertEqual(
            models.Patient.objects.filter(doctors__pk=self.user.uid).count(), 2
        )
        response = self.client.get(
            reverse(self.patients_url, kwargs={"pk": str(doctor.pk)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        patients_list = []
        for patient in patients:
            patients_list.append(
                {
                    "uuid": str(patient.pk),
                    "name": patient.name,
                    "phone_number": patient.phone_number,
                }
            )
        expected_data = json.dumps(patients_list)
        self.assertEqual(response.data, expected_data)

    def test_user_has_uid_different_to_passed_pk_cant_list_sessions(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patient = mommy.prepare(models.Patient)
        patient.doctor = doctor
        patient.save()
        sessions = mommy.prepare(models.Session, _quantity=2)
        for session in sessions:
            session.doctor = doctor
            session.patient = patient
            session.save()
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            2,
        )
        response = self.client.get(
            reverse(self.sessions_url, kwargs={"pk": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_has_uid_equal_to_passed_pk_can_list_sessions(self):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.prepare(models.Patient, name="Jaime", phone_number="1234")
        patient.doctor = doctor
        patient.save()
        sessions = mommy.prepare(models.Session, _quantity=1)
        for session in sessions:
            session.doctor = doctor
            session.patient = patient
            session.save()
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            1,
        )
        response = self.client.get(
            reverse(self.sessions_url, kwargs={"pk": str(doctor.pk)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sessions_list = []
        for session in sessions:
            sessions_list.append(
                {
                    "id": session.id,
                    "doctor": {
                        "uuid": str(doctor.pk),
                        "name": doctor.name,
                    },
                    "patient": {
                        "uuid": str(patient.pk),
                        "name": patient.name,
                        "phone_number": patient.phone_number,
                    },
                    "date": session.date.strftime(models.Session.DATE_FORMAT),
                    "group_index": None,
                    "status": enums.SessionStatus.NOT_CONFIRMED,
                    "type": enums.SessionType.INDIVIDUAL,
                    "group_id": None,
                }
            )
        expected_data = json.dumps(sessions_list)
        self.assertEqual(response.data, expected_data)

    def test_passed_bad_formatted_date_cant_list_sessions(self):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.prepare(models.Patient, name="Jaime", phone_number="1234")
        patient.doctor = doctor
        patient.save()
        sessions = mommy.prepare(models.Session, _quantity=3)
        for session in sessions:
            session.doctor = doctor
            session.patient = patient
            session.save()
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            3,
        )
        url = utils.reverse_querystring(
            self.sessions_url,
            kwargs={"pk": str(doctor.pk)},
            query_kwargs={"date": "not_a_date"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.ParseError.default_code
        )

    def test_passed_well_formatted_date_can_list_sessions_filtered_by_date_day(self):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.prepare(models.Patient, name="Jaime", phone_number="1234")
        patient.doctor = doctor
        patient.save()
        now = datetime.now().replace(tzinfo=timezone.utc)
        mommy.make(  # session1
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now + timedelta(days=2),
        )
        session2 = mommy.make(
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now + timedelta(minutes=30),
        )
        session3 = mommy.make(
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now - timedelta(minutes=30),
        )
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            3,
        )
        url = utils.reverse_querystring(
            self.sessions_url,
            kwargs={"pk": str(doctor.pk)},
            query_kwargs={"date": now.strftime(models.Session.DATE_FORMAT)},
        )
        response = self.client.get(url)
        sessions_list = []
        for session in [session2, session3]:
            sessions_list.append(
                {
                    "id": session.id,
                    "doctor": {
                        "uuid": str(doctor.pk),
                        "name": doctor.name,
                    },
                    "patient": {
                        "uuid": str(patient.pk),
                        "name": patient.name,
                        "phone_number": patient.phone_number,
                    },
                    "date": session.date.strftime(models.Session.DATE_FORMAT),
                    "group_index": None,
                    "status": enums.SessionStatus.NOT_CONFIRMED,
                    "type": enums.SessionType.INDIVIDUAL,
                    "group_id": None,
                }
            )
        expected_data = json.dumps(sessions_list)
        self.assertEqual(response.data, expected_data)

    def test_user_has_uid_different_to_passed_pk_cant_list_advices(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patients = mommy.make(
            models.Patient, _quantity=2, _fill_optional=["phone_number"]
        )
        advices_count = 5
        advices = mommy.make(models.Advice, _quantity=advices_count)
        for advice in advices:
            advice.doctor = doctor
            advice.save()
            for patient in patients:
                advice.patients.add(patient)
        self.assertEqual(
            models.Advice.objects.filter(doctor__pk=self.user.uid).count(),
            advices_count,
        )
        response = self.client.get(
            reverse(self.advices_url, kwargs={"pk": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_has_uid_equal_to_passed_pk_can_list_advices(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid, name="Jaime")
        patients = mommy.make(
            models.Patient, _quantity=2, _fill_optional=["phone_number"]
        )
        advices_count = 1
        advices = mommy.make(models.Advice, _quantity=advices_count, message="opa")
        for advice in advices:
            advice.doctor = doctor
            advice.save()
            for patient in patients:
                advice.patients.add(patient)
        self.assertEqual(
            models.Advice.objects.filter(doctor__pk=self.user.uid).count(),
            advices_count,
        )
        response = self.client.get(
            reverse(self.advices_url, kwargs={"pk": str(doctor.pk)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        advices_list = []
        for advice in advices:
            advices_list.append(
                {
                    "id": advice.id,
                    "doctor": {
                        "uuid": str(doctor.pk),
                        "name": doctor.name,
                    },
                    "patients": sorted([*map(lambda p: str(p.pk), patients)]),
                    "message": advice.message,
                }
            )
        expected_data = json.dumps(advices_list)
        self.assertEqual(response.data, expected_data)


class PatientViewSetTestCase(BaseViewTestCase):
    assignments_url = "patients-assignments"
    sessions_url = "patients-sessions"
    advices_url = "patients-advices"
