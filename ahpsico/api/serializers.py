from rest_framework import serializers

from .models import Advice, Assignment, Doctor, Invite, Patient, Session


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            "uuid",
            "name",
            "phone_number",
            "description",
            "crp",
            "pix_key",
            "payment_details",
        ]


class SimpleDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            "uuid",
            "name",
        ]


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "uuid",
            "name",
            "phone_number",
        ]


class InviteSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Invite
        fields = [
            "phone_number",
            "patient",
            "doctor",
        ]


class AdviceSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patients = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = Advice
        fields = [
            "message",
            "patients",
            "doctor",
        ]


class SessionSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()

    class Meta:
        model = Session
        fields = [
            "patient",
            "doctor",
            "group_id",
            "group_index",
            "status",
            "type",
            "date",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    doctor = SimpleDoctorSerializer()
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    delivery_session = serializers.SlugRelatedField(read_only=True, slug_field="date")

    class Meta:
        model = Assignment
        fields = [
            "title",
            "description",
            "doctor",
            "patient",
            "status",
            "delivery_session",
        ]
