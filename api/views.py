import io
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from django.http import JsonResponse
from rest_framework import exceptions as rest_exceptions

from . import exceptions
from . import models
from . import serializers


class LoginUser(APIView):
    """
    View to validate firebase token and return the user's uuid and type

    * Requires token authentication.
    """

    def post(self, request, format=None):
        uid = request.user.uid

        if models.Doctor.objects.filter(uuid=uid).exists():
            is_doctor = True
        elif models.Patient.objects.filter(uuid=uid).exists():
            is_doctor = False
        else:
            raise exceptions.SignUpRequired()

        serializer = serializers.LoginSerializer(
            data={"user_uuid": uid, "is_doctor": is_doctor}
        )
        serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(serializer.data)
        return JsonResponse(json)


class RegisterUser(APIView):
    """
    View to validate firebase token and create a Doctor or a Patient,
    depending on what is passed to the "is_doctor" field in the request
    body

    * Requires token authentication.
    """

    def post(self, request, format=None):
        uid = request.user.uid

        user_is_doctor = models.Doctor.objects.filter(uuid=uid).exists()
        user_is_patient = models.Patient.objects.filter(uuid=uid).exists()
        if user_is_doctor or user_is_patient:
            raise exceptions.UserAlreadyRegistered()

        data = JSONParser().parse(request)
        request_serializer = serializers.SignUpRequestSerializer(data=data)
        request_serializer.is_valid(raise_exception=True)

        name = request_serializer.data["name"]
        is_doctor = request_serializer.data["is_doctor"]
        try:
            if is_doctor:
                doctor = models.Doctor(uuid=uid, name=name)
                doctor.save()
            else:
                patient = models.Patient(uuid=uid, name=name)
                patient.save()
        except Exception:
            raise rest_exceptions.ParserError()

        response_serializer = serializers.SignUpResponseSerializer(
            data={"user_uuid": uid}
        )
        response_serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(response_serializer.data)
        return JsonResponse(json)


class DoctorViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing doctor instances.

    * Requires token authentication.
    """

    serializer_class = serializers.DoctorSerializer
    queryset = models.Doctor.objects.all()

    def update(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = self.kwargs["pk"]
        if uid != pk:
            raise rest_exceptions.PermissionDenied()

        return super().update(request, *args, **kwargs)

    @action(detail=True)
    def patients(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = self.kwargs["pk"]
        if uid != pk:
            raise rest_exceptions.PermissionDenied()

        patients = models.Patient.objects.filter(doctors__id=uid)
        serializer = serializers.PatientSerializer(patients, many=True)
        serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(serializer.data)
        return JsonResponse(json)


class PatientViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing patient instances.

    * Requires token authentication.
    """

    serializer_class = serializers.PatientSerializer
    queryset = models.Patient.objects.all()

    def retrieve(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = self.kwargs["pk"]
        if uid != pk:
            qs = models.Patient.objects.filter(uuid=pk, doctors__id=uid)
            is_patients_doctor = qs.exists()
            if not is_patients_doctor:
                raise rest_exceptions.PermissionDenied()

        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = self.kwargs["pk"]
        if uid != pk:
            raise rest_exceptions.PermissionDenied()

        return super().update(request, *args, **kwargs)
