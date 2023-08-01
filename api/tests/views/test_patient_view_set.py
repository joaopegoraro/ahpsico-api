import json

from django.urls import reverse
from django.utils.timezone import datetime, timedelta, timezone
from model_mommy import mommy
from rest_framework import exceptions as rest_exceptions
from rest_framework import status

from ... import enums, models, utils
from .base_view_test_case import BaseViewTestCase


class PatientViewSetTestCase(BaseViewTestCase):
    list_url = "patients-list"
    detail_url = "patients-detail"
    assignments_url = "patients-assignments"
    sessions_url = "patients-sessions"
    advices_url = "patients-advices"

    def test_user_not_authenticated_cant_list_sessions(self):
        patient = mommy.make(models.Patient, uuid=self.user.uid)
        url = reverse(self.sessions_url, kwargs={"pk": str(patient.pk)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_not_authenticated_cant_list_assignments(self):
        patient = mommy.make(models.Patient, uuid=self.user.uid)
        url = reverse(self.assignments_url, kwargs={"pk": str(patient.pk)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_not_authenticated_cant_list_advices(self):
        patient = mommy.make(models.Patient, uuid=self.user.uid)
        url = reverse(self.advices_url, kwargs={"pk": str(patient.pk)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_has_patient_information_can_retrieve(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patient = mommy.make(models.Patient)
        patient.doctors.add(doctor)
        url = reverse(self.detail_url, kwargs={"pk": str(patient.pk)})
        response = self.client.get(url)
        expected_data = {
            "uuid": str(patient.pk),
            "doctors": [str(doctor.pk)],
            "name": patient.name,
            "phone_number": patient.phone_number,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(response.data), json.dumps(expected_data))

    def test_user_has_no_patient_information_cant_retrieve(self):
        self.authenticate()
        mommy.make(models.Doctor, uuid=self.user.uid)
        patient = mommy.make(models.Patient)
        url = reverse(self.detail_url, kwargs={"pk": str(patient.pk)})
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_user_is_not_queried_patient_cant_update(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, uuid=self.user.uid)
        patient = mommy.make(models.Patient)
        patient.doctors.add(doctor)
        url = reverse(self.detail_url, kwargs={"pk": str(patient.pk)})
        request_data = {
            "uuid": str(patient.pk),
            "name": "some_other_name",
            "phone_number": patient.phone_number,
        }
        response = self.client.put(url, request_data)
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_user_is_queried_patient_can_update(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor)
        patient = mommy.make(models.Patient, uuid=self.user.uid)
        patient.doctors.add(doctor)
        url = reverse(self.detail_url, kwargs={"pk": str(patient.pk)})
        new_name = "some_other_name"
        request_data = {
            "uuid": str(patient.pk),
            "name": new_name,
            "phone_number": patient.phone_number,
        }
        response = self.client.put(url, request_data)
        expected_data = {
            "uuid": str(patient.pk),
            "doctors": [str(doctor.pk)],
            "name": new_name,
            "phone_number": patient.phone_number,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(response.data), json.dumps(expected_data))

    def test_user_has_no_patient_information_cant_list_sessions(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor)
        patient = mommy.prepare(models.Patient)
        patient.doctor = doctor
        patient.save()
        sessions_count = 3
        sessions = mommy.prepare(models.Session, _quantity=sessions_count)
        for session in sessions:
            session.doctor = doctor
            session.patient = patient
            session.save()
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=doctor.pk, patient__pk=patient.pk
            ).count(),
            sessions_count,
        )
        response = self.client.get(
            reverse(self.sessions_url, kwargs={"pk": str(patient.pk)})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_has_patient_information_can_list_its_own_sessions_with_patient(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        session1 = mommy.make(
            models.Session,
            doctor=doctor,
            patient=patient,
        )
        mommy.make(  # session2
            models.Session,
            patient=patient,
        )
        session3 = mommy.make(  # session3
            models.Session,
            doctor=doctor,
            patient=patient,
        )
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.sessions_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        sessions_list = []
        for session in [session1, session3]:
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

    def test_doctor_passed_upcoming_as_true_can_list_its_sessions_with_patient_filtered_by_date_greater_than_now(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        now = datetime.now().replace(tzinfo=timezone.utc)
        session1 = mommy.make(
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now + timedelta(days=2),
        )
        mommy.make(  # session2
            models.Session,
            patient=patient,
            date=now + timedelta(minutes=30),
        )
        mommy.make(  # session3
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now - timedelta(minutes=30),
        )
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.sessions_url,
            kwargs={"pk": str(patient.pk)},
            query_kwargs={"upcoming": True},
        )
        response = self.client.get(url)
        sessions_list = []
        for session in [session1]:
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

    def test_patient_passed_upcoming_as_true_can_list_sessions_filtered_by_date_greater_than_now(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient, uuid=self.user.uid, name="Jaime", phone_number="1234"
        )
        patient.doctors.add(doctor)
        now = datetime.now().replace(tzinfo=timezone.utc)
        session1 = mommy.make(
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
        mommy.make(  # session3
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now - timedelta(minutes=30),
        )
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=doctor.pk, patient__pk=self.user.uid
            ).count(),
            3,
        )
        url = utils.reverse_querystring(
            self.sessions_url,
            kwargs={"pk": str(patient.pk)},
            query_kwargs={"upcoming": True},
        )
        response = self.client.get(url)
        sessions_list = []
        for session in [session1, session2]:
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

    def test_patient_with_uid_equal_to_passed_pk_can_list_sessions(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient, uuid=self.user.uid, name="Jaime", phone_number="1234"
        )
        patient.doctors.add(doctor)
        now = datetime.now().replace(tzinfo=timezone.utc)
        session1 = mommy.make(
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
        session3 = mommy.make(  # session3
            models.Session,
            doctor=doctor,
            patient=patient,
            date=now - timedelta(minutes=30),
        )
        self.assertEqual(
            models.Session.objects.filter(
                doctor__pk=doctor.pk, patient__pk=self.user.uid
            ).count(),
            3,
        )
        url = reverse(self.sessions_url, kwargs={"pk": str(patient.pk)})
        response = self.client.get(url)
        sessions_list = []
        for session in [session1, session2, session3]:
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

    def test_user_has_no_patient_information_cant_list_assignments(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        url = utils.reverse_querystring(
            self.assignments_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_doctor_has_patient_information_can_list_its_own_assignments_with_patient(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        session = mommy.make(models.Session, doctor=doctor, patient=patient)
        ass1 = mommy.make(
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            title="title1",
            description="desc1",
        )
        mommy.make(  # ass2
            models.Assignment,
            patient=patient,
            delivery_session=session,
            title="title2",
            description="desc2",
        )
        ass3 = mommy.make(
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            title="title3",
            description="desc3",
        )
        self.assertEqual(
            models.Assignment.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.assignments_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        ass_list = []
        for ass in [ass1, ass3]:
            ass_list.append(
                {
                    "id": ass.id,
                    "doctor": {
                        "uuid": str(doctor.pk),
                        "name": doctor.name,
                    },
                    "patient": str(patient.pk),
                    "delivery_session": {
                        "id": session.id,
                        "date": session.date.strftime(models.Session.DATE_FORMAT),
                    },
                    "title": ass.title,
                    "description": ass.description,
                    "status": enums.AssignmentStatus.PENDING,
                }
            )
        expected_data = json.dumps(ass_list)
        self.assertEqual(response.data, expected_data)

    def test_doctor_passed_pending_as_true_can_list_its_own_assignments_with_patient(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        session = mommy.make(models.Session, doctor=doctor, patient=patient)
        ass1 = mommy.make(
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            title="title1",
            description="desc1",
        )
        mommy.make(  # ass2
            models.Assignment,
            patient=patient,
            delivery_session=session,
            title="title2",
            description="desc2",
        )
        mommy.make(  # ass3
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            status=enums.AssignmentStatus.DONE,
            title="title3",
            description="desc3",
        )
        self.assertEqual(
            models.Assignment.objects.filter(
                doctor__pk=self.user.uid, patient__pk=patient.pk
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.assignments_url,
            kwargs={"pk": str(patient.pk)},
            query_kwargs={"pending": True},
        )
        response = self.client.get(url)
        ass_list = []
        for ass in [ass1]:
            ass_list.append(
                {
                    "id": ass.id,
                    "doctor": {
                        "uuid": str(doctor.pk),
                        "name": doctor.name,
                    },
                    "patient": str(patient.pk),
                    "delivery_session": {
                        "id": session.id,
                        "date": session.date.strftime(models.Session.DATE_FORMAT),
                    },
                    "title": ass.title,
                    "description": ass.description,
                    "status": enums.AssignmentStatus.PENDING,
                }
            )
        expected_data = json.dumps(ass_list)
        self.assertEqual(response.data, expected_data)

    def test_patient_has_patient_information_can_list_assignments(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient, uuid=self.user.uid, name="Jaime", phone_number="1234"
        )
        patient.doctors.add(doctor)
        session = mommy.make(models.Session, doctor=doctor, patient=patient)
        ass1 = mommy.make(
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            title="title1",
            description="desc1",
        )
        ass2 = mommy.make(
            models.Assignment,
            patient=patient,
            delivery_session=session,
            title="title2",
            description="desc2",
        )
        ass3 = mommy.make(
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            title="title3",
            description="desc3",
        )
        self.assertEqual(
            models.Assignment.objects.filter(
                doctor__pk=doctor.pk, patient__pk=self.user.uid
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.assignments_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        ass_list = []
        for ass in [ass1, ass2, ass3]:
            ass_list.append(
                {
                    "id": ass.id,
                    "doctor": {
                        "uuid": str(ass.doctor.pk),
                        "name": ass.doctor.name,
                    },
                    "patient": str(ass.patient.pk),
                    "delivery_session": {
                        "id": session.id,
                        "date": session.date.strftime(models.Session.DATE_FORMAT),
                    },
                    "title": ass.title,
                    "description": ass.description,
                    "status": ass.status,
                }
            )
        expected_data = json.dumps(ass_list)
        self.assertEqual(response.data, expected_data)

    def test_patient_passed_pending_as_true_can_list_assignments_with_patient(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient, uuid=self.user.uid, name="Jaime", phone_number="1234"
        )
        patient.doctors.add(doctor)
        session = mommy.make(models.Session, doctor=doctor, patient=patient)
        ass1 = mommy.make(
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            title="title1",
            description="desc1",
        )
        ass2 = mommy.make(
            models.Assignment,
            patient=patient,
            delivery_session=session,
            title="title2",
            description="desc2",
        )
        mommy.make(  # ass3
            models.Assignment,
            doctor=doctor,
            patient=patient,
            delivery_session=session,
            status=enums.AssignmentStatus.DONE,
            title="title3",
            description="desc3",
        )
        self.assertEqual(
            models.Assignment.objects.filter(
                doctor__pk=doctor.pk, patient__pk=self.user.uid
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.assignments_url,
            kwargs={"pk": str(patient.pk)},
            query_kwargs={"pending": True},
        )
        response = self.client.get(url)
        ass_list = []
        for ass in [ass1, ass2]:
            ass_list.append(
                {
                    "id": ass.id,
                    "doctor": {
                        "uuid": str(ass.doctor.pk),
                        "name": ass.doctor.name,
                    },
                    "patient": str(ass.patient.pk),
                    "delivery_session": {
                        "id": session.id,
                        "date": session.date.strftime(models.Session.DATE_FORMAT),
                    },
                    "title": ass.title,
                    "description": ass.description,
                    "status": ass.status,
                }
            )
        expected_data = json.dumps(ass_list)
        self.assertEqual(response.data, expected_data)

    def test_user_has_no_patient_information_cant_list_advices(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        url = utils.reverse_querystring(
            self.advices_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_doctor_has_patient_information_can_list_its_own_advices_with_patient(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        patient.doctors.add(doctor)
        advice1 = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        advice2 = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        mommy.make(models.Advice, patients=[patient])  # advice3
        self.assertEqual(
            models.Advice.objects.filter(
                doctor__pk=self.user.uid, patients__pk=patient.pk
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.advices_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        advice_list = []
        for advice in [advice1, advice2]:
            advice_list.append(
                {
                    "id": advice.id,
                    "doctor": {
                        "uuid": str(advice.doctor.pk),
                        "name": advice.doctor.name,
                    },
                    "patients": [str(patient.pk)],
                    "message": advice.message,
                }
            )
        expected_data = json.dumps(advice_list)
        self.assertEqual(response.data, expected_data)

    def test_patient_can_list_its_own_advices(
        self,
    ):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient, uuid=self.user.uid, name="Jaime", phone_number="1234"
        )
        patient.doctors.add(doctor)
        advice1 = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        advice2 = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        advice3 = mommy.make(models.Advice, patients=[patient])
        self.assertEqual(
            models.Advice.objects.filter(
                doctor__pk=doctor.pk,
                patients__pk=self.user.uid,
            ).count(),
            2,
        )
        url = utils.reverse_querystring(
            self.advices_url,
            kwargs={"pk": str(patient.pk)},
        )
        response = self.client.get(url)
        advice_list = []
        for advice in [advice1, advice2, advice3]:
            advice_list.append(
                {
                    "id": advice.id,
                    "doctor": {
                        "uuid": str(advice.doctor.pk),
                        "name": advice.doctor.name,
                    },
                    "patients": [str(patient.pk)],
                    "message": advice.message,
                }
            )
        expected_data = json.dumps(advice_list)
        self.assertEqual(response.data, expected_data)
