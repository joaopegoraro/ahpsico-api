import json

from django.http import JsonResponse
from django.utils.timezone import datetime
from rest_framework import exceptions as rest_exceptions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from . import authentication, enums, exceptions, models, permissions, serializers


class LoginUser(APIView):
    """
    View to validate firebase token and return the user's uuid and type

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]

    def post(self, request, format=None):
        uid = request.user.uid

        if models.Doctor.objects.filter(pk=uid).exists():
            is_doctor = True
        elif models.Patient.objects.filter(pk=uid).exists():
            is_doctor = False
        else:
            raise exceptions.SignUpRequired()

        data = {"user_uuid": str(uid), "is_doctor": is_doctor}
        return Response(data, status=200)


class RegisterUser(APIView):
    """
    View to validate firebase token and create a Doctor or a Patient,
    depending on what is passed to the "is_doctor" field in the request
    body

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]

    def post(self, request, format=None):
        uid = request.user.uid
        phone_number = request.user.phone_number

        user_is_doctor = models.Doctor.objects.filter(pk=uid).exists()
        user_is_patient = models.Patient.objects.filter(pk=uid).exists()
        if user_is_doctor or user_is_patient:
            raise exceptions.UserAlreadyRegistered()

        request_serializer = serializers.SignUpRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        name = request_serializer.data["name"]
        is_doctor = request_serializer.data["is_doctor"]
        if is_doctor:
            doctor = models.Doctor(pk=uid, name=name, phone_number=phone_number)
            doctor.save()
        else:
            patient = models.Patient(pk=uid, name=name, phone_number=phone_number)
            patient.save()

        response_serializer = serializers.SignUpResponseSerializer(
            data={"user_uuid": uid}
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data)


class InviteViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing invites instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasInviteInformation]

    serializer_class = serializers.InviteSerializer
    queryset = models.Invite.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsDoctor()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        uid = request.user.uid

        phone_number = request.data.get("phone_number")
        if not phone_number:
            return rest_exceptions.bad_request(request, None)

        try:
            doctor = models.Doctor.objects.get(pk=uid)
        except models.Doctor.DoesNotExist:
            return rest_exceptions.PermissionDenied()

        try:
            patient = models.Patient.objects.get(phone_number=phone_number)
            if patient.doctors.filter(pk=doctor.pk).exists():
                raise exceptions.PatientAlreadyWithDoctor()
        except models.Patient.DoesNotExist:
            raise exceptions.PatientNotRegistered()

        invite = models.Invite(
            phone_number=phone_number,
            doctor=doctor,
            patient=patient,
        )
        invite.save()

        return Response(status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[permissions.IsInviteOwner],
    )
    def accept(self, request, *args, **kwargs):
        invite = self.get_object()
        invite.patient.doctors.add(invite.doctor)
        invite.delete()

        return Response(status=status.HTTP_200_OK)


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
    def patients(self, request, *args, **kwargs):
        uid = request.user.uid

        patients = models.Patient.objects.filter(doctors__pk=uid)
        serializer = serializers.PatientSerializer(patients, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=[permissions.IsOwner])
    def sessions(self, request, *args, **kwargs):
        uid = request.user.uid
        datestr = request.query_params.get("date")
        if not datestr:
            sessions = models.Session.objects.filter(doctor__pk=uid)
        else:
            try:
                date = datetime.strptime(datestr, models.Session.DATE_FORMAT)
                sessions = models.Session.objects.filter(
                    doctor__pk=uid,
                    date__year=date.year,
                    date__month=date.month,
                    date__day=date.day,
                )
            except Exception:
                raise rest_exceptions.ParseError(
                    "Date not in the correct format. Please use the 'YYYY-mm-ddTHH:MM:SSZ' format"
                )

        serializer = serializers.SessionSerializer(sessions, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=[permissions.IsOwner])
    def advices(self, request, *args, **kwargs):
        uid = request.user.uid

        advices = models.Advice.objects.filter(doctor__pk=uid)
        serializer = serializers.AdviceSerializer(advices, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)


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
            return [permissions.HasPatientInformation()]
        elif self.action == "update":
            return [permissions.IsOwner()]
        return super().get_permissions()

    @action(detail=True, permission_classes=[permissions.HasPatientInformation])
    def sessions(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = str(uid) == pk
        upcoming = request.query_params.get("upcoming")
        now = datetime.now()
        if upcoming and is_patient:
            sessions = models.Session.objects.filter(patient__pk=pk, date__gte=now)
        elif upcoming and not is_patient:
            sessions = models.Session.objects.filter(
                patient__pk=pk,
                doctor__pk=uid,
                date__gte=now,
            )
        elif not is_patient:
            sessions = models.Session.objects.filter(patient__pk=pk, doctor__pk=uid)
        else:
            sessions = models.Session.objects.filter(patient__pk=pk)

        serializer = serializers.SessionSerializer(sessions, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=[permissions.HasPatientInformation])
    def assignments(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = str(uid) == pk
        pending = request.query_params.get("pending")
        if pending and is_patient:
            assignments = models.Assignment.objects.filter(
                patient__pk=pk,
                status=enums.AssignmentStatus.PENDING,
            )
        elif pending and not is_patient:
            assignments = models.Assignment.objects.filter(
                patient__pk=pk,
                doctor__pk=uid,
                status=enums.AssignmentStatus.PENDING,
            )
        elif not is_patient:
            assignments = models.Assignment.objects.filter(
                patient__pk=pk, doctor__pk=uid
            )
        else:
            assignments = models.Assignment.objects.filter(patient__pk=pk)

        serializer = serializers.AssignmentSerializer(assignments, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=[permissions.HasPatientInformation])
    def advices(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = str(uid) == pk

        if is_patient:
            advices = models.Advice.objects.filter(patients__pk=pk)
        else:
            advices = models.Advice.objects.filter(doctor__pk=uid, patients__pk=pk)

        serializer = serializers.AdviceSerializer(advices, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)


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
            return [permissions.HasAdviceInformation()]
        return super().get_permissions()
