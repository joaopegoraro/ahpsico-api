import io

from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import datetime
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions as rest_exceptions
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from . import authentication, enums, exceptions, models, permissions, serializers


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

    @action(detail=True, permission_classes=[permissions.IsOwner])
    @extend_schema(
        request=None,
        responses=serializers.SessionSerializer,
    )
    def sessions(self, request, *args, **kwargs):
        uid = request.user.uid
        datestr = request.query_params.get("date")
        if not datestr:
            sessions = models.Session.objects.filter(doctor__id=uid)
        else:
            date = parse_datetime(datestr)
            sessions = models.Session.objects.filter(
                doctor__id=uid,
                date__year=date.year,
                date__month=date.month,
                date__day=date.day,
            )

        serializer = serializers.SessionSerializer(sessions, many=True)
        serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(serializer.data)
        return JsonResponse(json)

    @action(detail=True, permission_classes=[permissions.IsOwner])
    @extend_schema(
        request=None,
        responses=serializers.AdviceSerializer,
    )
    def advices(self, request, *args, **kwargs):
        uid = request.user.uid

        advices = models.Advice.objects.filter(doctor__id=uid)
        serializer = serializers.AdviceSerializer(advices, many=True)
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

    @action(detail=True, permission_classes=[permissions.HasPatientInformation])
    @extend_schema(
        request=None,
        responses=serializers.SessionSerializer,
    )
    def sessions(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = uid == pk
        upcoming = request.query_params.get("upcoming")
        now = datetime.now()
        if upcoming and is_patient:
            sessions = models.Session.objects.filter(patient__id=pk, date__gte=now)
        elif upcoming and not is_patient:
            sessions = models.Session.objects.filter(
                patient__id=pk,
                doctor_id=uid,
                date__gte=now,
            )
        elif not is_patient:
            sessions = models.Session.objects.filter(patient__id=pk, doctor__id=uid)
        else:
            sessions = models.Session.objects.filter(patient__id=pk)

        serializer = serializers.SessionSerializer(sessions, many=True)
        serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(serializer.data)
        return JsonResponse(json)

    @action(detail=True, permission_classes=[permissions.HasPatientInformation])
    @extend_schema(
        request=None,
        responses=serializers.AssignmentSerializer,
    )
    def assignments(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = uid == pk
        pending = request.query_params.get("pending")
        if pending and is_patient:
            sessions = models.Assignment.objects.filter(
                patient__id=pk,
                status=enums.AssignmentStatus.PENDING,
            )
        elif pending and not is_patient:
            sessions = models.Assignment.objects.filter(
                patient__id=pk,
                doctor__id=uid,
                status=enums.AssignmentStatus.PENDING,
            )
        elif not is_patient:
            sessions = models.Assignment.objects.filter(patient__id=pk, doctor__id=uid)
        else:
            sessions = models.Assignment.objects.filter(patient__id=pk)

        serializer = serializers.AssignmentSerializer(sessions, many=True)
        serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(serializer.data)
        return JsonResponse(json)

    @action(detail=True, permission_classes=[permissions.HasPatientInformation])
    @extend_schema(
        request=None,
        responses=serializers.AdviceSerializer,
    )
    def advices(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = uid == pk

        if is_patient:
            advices = models.Advice.objects.filter(patient__id=pk)
        else:
            advices = models.Advice.objects.filter(doctor__id=uid, patient__id=pk)

        serializer = serializers.AdviceSerializer(advices, many=True)
        serializer.is_valid(raise_exception=True)

        json = JSONRenderer().render(serializer.data)
        return JsonResponse(json)


class SessionViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing session instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasSessionInformation]

    serializer_class = serializers.SessionSerializer
    queryset = models.Session.objects.all()


class AssignmentViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing assignment instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasAssignmentInformation]

    serializer_class = serializers.AssignmentSerializer
    queryset = models.Assignment.objects.all()


class AdviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing advices instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.IsAdviceOwner]

    serializer_class = serializers.AdviceSerializer
    queryset = models.Advice.objects.all()

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.HasAdviceInformation]
        return super().get_permissions()
