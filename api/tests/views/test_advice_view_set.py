import json

from django.urls import reverse
from django.utils.timezone import datetime, timedelta, timezone
from model_mommy import mommy
from rest_framework import exceptions as rest_exceptions
from rest_framework import status

from ... import enums, models, utils
from .base_view_test_case import BaseViewTestCase


class AdviceViewSetTestCase(BaseViewTestCase):
    list_url = "advices-list"
    detail_url = "advices-detail"

    def test_user_has_advice_information_can_retrieve_advices(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient,
            uuid=self.user.uid,
            name="Jaime",
            phone_number="1234",
        )
        advice = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        mommy.make(models.Advice, patients=[patient])  # advice3
        url = utils.reverse_querystring(
            self.detail_url,
            kwargs={"pk": advice.id},
        )
        response = self.client.get(url)
        expected_data = {
            "id": advice.id,
            "doctor": {
                "uuid": str(advice.doctor.pk),
                "name": advice.doctor.name,
                "description": doctor.description,
            },
            "patients": [str(patient.pk)],
            "message": advice.message,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(response.data), json.dumps(expected_data))

    def test_user_has_no_advice_information_cant_retrieve_advices(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        advice = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        mommy.make(models.Advice, patients=[patient])  # advice3
        url = utils.reverse_querystring(
            self.detail_url,
            kwargs={"pk": advice.id},
        )
        response = self.client.get(url)
        expected_data = {
            "id": advice.id,
            "doctor": {
                "uuid": str(advice.doctor.pk),
                "name": advice.doctor.name,
            },
            "patients": [str(patient.pk)],
            "message": advice.message,
        }
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )

    def test_user_is_advice_doctor_can_delete_advice(self):
        self.authenticate()
        doctor = mommy.make(
            models.Doctor, uuid=self.user.uid, name="Marcos", phone_number="123"
        )
        patient = mommy.make(models.Patient, name="Jaime", phone_number="1234")
        advice = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        self.assertTrue(
            models.Advice.objects.filter(
                pk=advice.id, doctor__pk=doctor.pk, patients__pk=patient.pk
            ).exists()
        )
        mommy.make(models.Advice, patients=[patient])  # advice3
        url = utils.reverse_querystring(
            self.detail_url,
            kwargs={"pk": advice.id},
        )
        response = self.client.delete(url)
        self.assertFalse(
            models.Advice.objects.filter(
                pk=advice.id, doctor__pk=doctor.pk, patients__pk=patient.pk
            ).exists()
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_is_not_advice_doctor_cant_delete_advice(self):
        self.authenticate()
        doctor = mommy.make(models.Doctor, name="Marcos", phone_number="123")
        patient = mommy.make(
            models.Patient, uuid=self.user.uid, name="Jaime", phone_number="1234"
        )
        advice = mommy.make(models.Advice, doctor=doctor, patients=[patient])
        self.assertTrue(
            models.Advice.objects.filter(
                pk=advice.id, doctor__pk=doctor.pk, patients__pk=patient.pk
            ).exists()
        )
        mommy.make(models.Advice, patients=[patient])  # advice3
        url = utils.reverse_querystring(
            self.detail_url,
            kwargs={"pk": advice.id},
        )
        response = self.client.delete(url)
        self.assertTrue(
            models.Advice.objects.filter(
                pk=advice.id, doctor__pk=doctor.pk, patients__pk=patient.pk
            ).exists()
        )
        self.assertEqual(
            response.status_code, rest_exceptions.PermissionDenied.status_code
        )
        self.assertEqual(
            response.data["detail"].code, rest_exceptions.PermissionDenied.default_code
        )
