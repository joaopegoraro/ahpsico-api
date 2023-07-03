import json
import uuid

from django.urls import reverse
from django.utils.timezone import datetime, timedelta, timezone
from model_mommy import mommy
from rest_framework import exceptions as rest_exceptions
from rest_framework import status

from ... import enums, models, utils
from .base_view_test_case import BaseViewTestCase


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
                    "doctors": [str(doctor.pk)],
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
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
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
                        "doctors": [str(doctor.pk)],
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
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
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
                        "doctors": [str(doctor.pk)],
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
