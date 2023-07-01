import io
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from django.http import JsonResponse
from rest_framework import exceptions as rest_exceptions
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import permission_classes

from . import exceptions
from . import models
from . import serializers
from . import authentication
from . import permissions


class LoginUser(APIView):
    """
    View to validate firebase token and return the user's uuid and type

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]

    @extend_schema(
        request=None,
        responses=serializers.LoginSerializer,
    )
    def post(self, request, format=None):
        uid = request.user.uid

        if models.Doctor.objects.filter(pk=uid).exists():
            is_doctor = True
        elif models.Patient.objects.filter(pk=uid).exists():
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

    authentication_classes = [authentication.FirebaseAuthentication]

    @extend_schema(
        request=serializers.SignUpRequestSerializer,
        responses=serializers.SignUpResponseSerializer,
    )
    def post(self, request, format=None):
        uid = request.user.uid

        user_is_doctor = models.Doctor.objects.filter(pk=uid).exists()
        user_is_patient = models.Patient.objects.filter(pk=uid).exists()
        if user_is_doctor or user_is_patient:
            raise exceptions.UserAlreadyRegistered()

        data = JSONParser().parse(request)
        request_serializer = serializers.SignUpRequestSerializer(data=data)
        request_serializer.is_valid(raise_exception=True)

        name = request_serializer.data["name"]
        is_doctor = request_serializer.data["is_doctor"]
        try:
            if is_doctor:
                doctor = models.Doctor(pk=uid, name=name)
                doctor.save()
            else:
                patient = models.Patient(pk=uid, name=name)
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

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.IsOwner]

    serializer_class = serializers.DoctorSerializer
    queryset = models.Doctor.objects.all()

    @action(detail=True, permission_classes=[permissions.IsOwner])
    @extend_schema(
        request=None,
        responses=serializers.PatientSerializer,
    )
    def patients(self, request, *args, **kwargs):
        uid = request.user.uid

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

    authentication_classes = [authentication.FirebaseAuthentication]

    serializer_class = serializers.PatientSerializer
    queryset = models.Patient.objects.all()

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.HasPatientInformation]
        elif self.action == "update":
            return [permissions.IsOwner]
        return super().get_permissions()


class SessionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing session instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasSessionInformation]

    serializer_class = serializers.SessionSerializer
    queryset = models.Session.objects.all()
