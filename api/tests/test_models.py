from django.test import TestCase
from model_mommy import mommy

from .. import models


class DoctorTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        doctor = mommy.make(models.Doctor)
        self.assertEqual(str(doctor), f"{doctor.name} (CRP {doctor.crp})")


class PatientTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        patient = mommy.make(models.Patient)
        self.assertEqual(str(patient), f"{patient.name} ({patient.phone_number})")


class InviteTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        invite = mommy.make(models.Invite)
        self.assertEqual(str(invite), f"to {invite.patient} - from {invite.doctor})")


class AdviceTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        advice = mommy.make(models.Advice)
        self.assertEqual(str(advice), f"{advice.message} - from {advice.doctor})")


class SessionGroupTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        group = mommy.make(models.SessionGroup)
        self.assertEqual(
            str(group), f"Doctor: {group.doctor} - Patient: ${group.patient}"
        )


class SessionTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        session = mommy.make(models.Session)
        self.assertEqual(
            str(session), f"Doctor: {session.doctor} - Patient: ${session.patient}"
        )


class AssignmentTestCase(TestCase):
    def test_string_method_should_return_correct_representation(self):
        assignment = mommy.make(models.Assignment)
        self.assertEqual(str(assignment), f"{assignment.title}")
