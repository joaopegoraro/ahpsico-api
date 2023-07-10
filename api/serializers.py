from rest_framework import serializers

from . import models


class SignUpRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    is_doctor = serializers.BooleanField()


class SignUpResponseSerializer(serializers.Serializer):
    user_uuid = serializers.UUIDField()
    user_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=200)
    is_doctor = serializers.BooleanField()


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Doctor
        fields = "__all__"


class SimpleDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Doctor
        fields = [
            "uuid",
            "name",
            "description",
        ]


class PatientSerializer(serializers.ModelSerializer):
    doctors = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    class Meta:
        model = models.Patient
        fields = "__all__"


class SimplePatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Patient
        fields = [
            "uuid",
            "name",
            "phone_number",
        ]


class InviteSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patient = serializers.PrimaryKeyRelatedField(
        read_only=True,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    class Meta:
        model = models.Invite
        fields = "__all__"


class AdviceSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patients = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    class Meta:
        model = models.Advice
        fields = "__all__"


class SessionSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patient = SimplePatientSerializer()
    date = serializers.DateTimeField(format=models.Session.DATE_FORMAT)

    class Meta:
        model = models.Session
        fields = "__all__"


class SimpleSessionSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format=models.Session.DATE_FORMAT)

    class Meta:
        model = models.Session
        fields = [
            "id",
            "date",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patient = serializers.PrimaryKeyRelatedField(
        read_only=True,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    delivery_session = SimpleSessionSerializer()

    class Meta:
        model = models.Assignment
        fields = "__all__"
