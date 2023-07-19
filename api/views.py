import json

from django.utils.timezone import datetime
from rest_framework import exceptions as rest_exceptions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from . import authentication, enums, exceptions, models, permissions, serializers


class LoginUser(APIView):
    """
    View to validate firebase token and return the user's information

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasToken]

    def post(self, request, format=None):
        uid = request.user.uid

        try:
            doctor = models.Doctor.objects.get(pk=uid)
            is_doctor = True
            phone_number = doctor.phone_number
            name = doctor.name
        except:
            try:
                patient = models.Patient.objects.get(pk=uid)
                is_doctor = False
                phone_number = patient.phone_number
                name = patient.name
            except:
                raise exceptions.SignUpRequired()

        data = {
            "user_uuid": str(uid),
            "user_name": name,
            "phone_number": phone_number,
            "is_doctor": is_doctor,
        }
        return Response(data, status=200)


class RegisterUser(APIView):
    """
    View to validate firebase token and create a Doctor or a Patient,
    depending on what is passed to the "is_doctor" field in the request
    body

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasToken]

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
            data={
                "user_uuid": str(uid),
                "user_name": name,
                "phone_number": phone_number,
                "is_doctor": is_doctor,
            }
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data)


class InviteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for viewing and editing invites instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasToken, permissions.HasInviteInformation]

    serializer_class = serializers.InviteSerializer
    queryset = models.Invite.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.HasToken(), permissions.IsDoctor()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        uid = request.user.uid
        invites = models.Invite.objects.filter(
            doctor__pk=uid
        ) | models.Invite.objects.filter(patient__pk=uid)

        if invites.count() == 0:
            raise exceptions.NoInviteFound()

        serializer = serializers.InviteSerializer(invites, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        uid = request.user.uid

        phone_number = request.data.get("phone_number")
        if not phone_number:
            return rest_exceptions.bad_request(request, None)

        try:
            saved_invite = models.Invite.objects.get(
                doctor__pk=uid, phone_number=phone_number
            )
        except:
            pass
        else:
            raise exceptions.InviteAlreadySent()

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
        invite_serializer = serializers.InviteSerializer(invite)
        return Response(
            json.dumps(invite_serializer.data), status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[permissions.HasToken, permissions.IsInviteOwner],
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
    permission_classes = [permissions.HasToken, permissions.IsOwner]

    serializer_class = serializers.DoctorSerializer
    queryset = models.Doctor.objects.all()

    @action(detail=True, permission_classes=[permissions.HasToken, permissions.IsOwner])
    def patients(self, request, *args, **kwargs):
        uid = request.user.uid

        patients = models.Patient.objects.filter(doctors__pk=uid)
        serializer = serializers.SimplePatientSerializer(patients, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=[permissions.HasToken, permissions.IsOwner])
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

    @action(detail=True, permission_classes=[permissions.HasToken, permissions.IsOwner])
    def advices(self, request, *args, **kwargs):
        uid = request.user.uid

        advices = models.Advice.objects.filter(doctor__pk=uid)
        serializer = serializers.AdviceSerializer(advices, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=[permissions.HasToken])
    def schedule(self, request, *args, **kwargs):
        uid = request.user.uid

        schedule = models.Schedule.objects.filter(doctor__pk=uid)
        serializer = serializers.ScheduleSerializer(schedule, many=True)

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
    permission_classes = [permissions.HasToken]

    serializer_class = serializers.PatientSerializer
    queryset = models.Patient.objects.all()

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.HasToken(), permissions.HasPatientInformation()]
        elif self.action == "update":
            return [permissions.IsOwner()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]

        patient = self.get_object()
        serializer = serializers.PatientSerializer(patient)
        data = serializer.data

        if str(uid) != pk:
            try:
                data["doctors"] = [str(models.Doctor.objects.get(pk=uid).pk)]
            except:
                data["doctors"] = []

        return Response(data)

    @action(detail=True, permission_classes=[permissions.HasToken, permissions.IsOwner])
    def doctors(self, request, *args, **kwargs):
        uid = request.user.uid

        patient = models.Patient.objects.get(pk=uid)
        doctors = patient.doctors.all()
        serializer = serializers.SimpleDoctorSerializer(doctors, many=True)

        return Response(json.dumps(serializer.data), status=status.HTTP_200_OK)

    @action(
        detail=True,
        permission_classes=[permissions.HasToken, permissions.HasPatientInformation],
    )
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

    @action(
        detail=True,
        permission_classes=[permissions.HasToken, permissions.HasPatientInformation],
    )
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

    @action(
        detail=True,
        permission_classes=[permissions.HasToken, permissions.HasPatientInformation],
    )
    def advices(self, request, *args, **kwargs):
        uid = request.user.uid
        pk = kwargs["pk"]
        is_patient = str(uid) == pk

        if is_patient:
            advices = models.Advice.objects.filter(patients__pk=pk)
        else:
            advices = models.Advice.objects.filter(doctor__pk=uid, patients__pk=pk)

        serializer = serializers.AdviceSerializer(advices, many=True)
        data = serializer.data

        if is_patient:
            for advice in data:
                advice["patients"] = [pk]

        return Response(json.dumps(data), status=status.HTTP_200_OK)


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
    permission_classes = [permissions.HasToken, permissions.HasSessionInformation]

    serializer_class = serializers.SessionSerializer
    queryset = models.Session.objects.all()

    def create(self, request, *args, **kwargs):
        data = JSONParser().parse(request)

        session_serializer = serializers.SessionSerializer(data=data)
        session_serializer.is_valid(raise_exception=True)
        session = Session(**session_serializer.validated_data)

        if models.Session.objects.filter(
            doctor__pk=session.doctor.pk,
            patient__pk=session.patient.pk,
            date=session.date,
        ).exists():
            raise exceptions.SessionAlreadyBooked()

        return Response(
            json.dumps(session_serializer.data), status=status.HTTP_201_CREATED
        )


class ScheduleViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for creating and deleting schedule instances.

    * Requires token authentication.
    """

    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.HasToken, permissions.IsScheduleOwner]

    serializer_class = serializers.ScheduleSerializer
    queryset = models.Schedule.objects.all()


class AssignmentViewSet(
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
    permission_classes = [permissions.HasToken, permissions.HasAssignmentInformation]

    serializer_class = serializers.AssignmentSerializer
    queryset = models.Assignment.objects.all()


class AdviceViewSet(
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
    permission_classes = [permissions.HasToken, permissions.IsAdviceOwner]

    serializer_class = serializers.AdviceSerializer
    queryset = models.Advice.objects.all()

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.HasToken(), permissions.HasAdviceInformation()]
        return super().get_permissions()
