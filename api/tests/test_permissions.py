import os
import uuid
from unittest import mock

from django.test import TestCase
from model_mommy import mommy

from .. import models, permissions


class IsOwnerTestCase(TestCase):
    def setUp(self):
        self.permission = permissions.IsOwner()

        self.request = mock.MagicMock(user=mock.MagicMock())
        self.view = mock.MagicMock()

    def test_user_has_uuid_equal_to_pk_has_permission(self):
        some_doctor = mommy.make(models.Doctor)
        self.request.user.uid = some_doctor.pk
        self.view.kwargs = {"pk": str(some_doctor.pk)}
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertEqual(str(some_doctor.pk), self.view.kwargs["pk"])
        self.assertTrue(has_permission)

    def test_user_has_uuid_different_to_pk_has_no_permission(self):
        some_doctor = mommy.make(models.Doctor)
        some_patient = mommy.make(models.Patient)
        self.request.user.uid = some_doctor.pk
        self.view.kwargs = {"pk": str(some_patient.pk)}
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertNotEqual(str(some_doctor.pk), self.view.kwargs["pk"])
        self.assertFalse(has_permission)


class IsDoctorTestCase(TestCase):
    def setUp(self):
        self.permission = permissions.IsDoctor()

        self.request = mock.MagicMock(user=mock.MagicMock())
        self.view = mock.MagicMock()

    def test_user_is_doctor_has_permission(self):
        doctor = mommy.make(models.Doctor)
        doctor.save()
        self.request.user.uid = doctor.uuid
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertEqual(self.request.user.uid, doctor.pk)
        self.assertTrue(has_permission)

    def test_user_isnt_doctor_has_no_permission(self):
        doctor = mommy.make(models.Doctor)
        doctor.save()
        self.request.user.uid = uuid.uuid4()
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertNotEqual(self.request.user.uid, doctor.pk)
        self.assertFalse(has_permission)


class HasPatientInformationTestCase(TestCase):
    def setUp(self):
        self.permission = permissions.HasPatientInformation()
        self.patient = mommy.make(models.Patient)
        self.doctor = mommy.make(models.Doctor)

        self.request = mock.MagicMock(user=mock.MagicMock())
        self.view = mock.MagicMock()

    def test_user_is_queried_patient_has_permission(self):
        self.request.user.uid = self.patient.uuid
        self.view.kwargs = {"pk": str(self.patient.uuid)}
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertEqual(str(self.request.user.uid), self.view.kwargs["pk"])
        self.assertTrue(has_permission)

    def test_user_is_queried_patient_doctor_has_permission(self):
        self.patient.save()
        self.patient.doctors.add(self.doctor)
        self.request.user.uid = self.doctor.uuid
        self.view.kwargs = {"pk": str(self.patient.uuid)}
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertEqual(self.request.user.uid, self.doctor.pk)
        self.assertTrue(has_permission)

    def test_user_is_not_queried_patient_or_its_doctor_has_no_permission(self):
        self.request.user.uid = self.doctor.uuid
        self.view.kwargs = {"pk": str(self.patient.uuid)}
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertNotEquals(str(self.request.user.uid), self.view.kwargs["pk"])
        self.assertFalse(has_permission)


class HasSessionInformationTestCase(TestCase):
    def setUp(self):
        self.permission = permissions.HasSessionInformation()
        self.patient = mommy.make(models.Patient)
        self.doctor = mommy.make(models.Doctor)
        self.session = mommy.make(models.Session)
        self.session.doctor = self.doctor
        self.session.patient = self.patient
        self.session.save()

        self.request = mock.MagicMock(user=mock.MagicMock())
        self.view = mock.MagicMock()

    def test_non_POST_and_PUT_methods_have_permission(self):
        self.request.method = "CREATE"
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertTrue(has_permission)

    def test_user_is_session_patient_in_POST_and_PUT_methods_has_permission(self):
        self.request.method = "POST"
        self.request.user.uid = self.patient.uuid
        self.request.data = {
            "doctor_id": str(self.doctor.pk),
            "patient_id": str(self.patient.pk),
        }
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertTrue(has_permission)
        self.request.method = "PUT"
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertTrue(has_permission)

    def test_user_is_session_doctor_in_POST_and_PUT_methods_has_permission(self):
        self.request.method = "POST"
        self.request.user.uid = self.doctor.uuid
        self.request.data = {
            "doctor_id": str(self.doctor.pk),
            "patient_id": str(self.patient.pk),
        }
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertTrue(has_permission)
        self.request.method = "PUT"
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertTrue(has_permission)

    def test_user_is_neither_session_doctor_nor_patient_in_POST_and_PUT_methods_has_no_permission(
        self,
    ):
        self.request.method = "POST"
        self.request.user.uid = uuid.uuid4()
        self.request.data = {
            "doctor_id": str(self.doctor.pk),
            "patient_id": str(self.patient.pk),
        }
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertFalse(has_permission)
        self.request.method = "PUT"
        has_permission = self.permission.has_permission(self.request, self.view)
        self.assertFalse(has_permission)

    def test_user_is_session_patient_has_object_permission(self):
        self.request.user.uid = self.patient.uuid
        has_permission = self.permission.has_object_permission(
            self.request, self.view, self.session
        )
        self.assertEquals(self.session.patient.pk, self.request.user.uid)
        self.assertNotEqual(self.session.doctor.pk, self.request.user.uid)
        self.assertTrue(has_permission)

    def test_user_is_session_doctor_has_object_permission(self):
        self.request.user.uid = self.doctor.uuid
        has_permission = self.permission.has_object_permission(
            self.request, self.view, self.session
        )
        self.assertNotEquals(self.session.patient.pk, self.request.user.uid)
        self.assertEqual(self.session.doctor.pk, self.request.user.uid)
        self.assertTrue(has_permission)

    def test_user_is_neither_session_patient_nor_doctor_has_no_object_permission(self):
        self.request.user.uid = uuid.uuid4()
        has_permission = self.permission.has_object_permission(
            self.request, self.view, self.session
        )
        self.assertNotEquals(self.session.patient.pk, self.request.user.uid)
        self.assertNotEquals(self.session.doctor.pk, self.request.user.uid)
        self.assertFalse(has_permission)
