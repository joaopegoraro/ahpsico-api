from rest_framework import permissions

from . import exceptions, models


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        pk = view.kwargs["pk"]
        return uid == pk


class HasPatientInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    patient information, which is their doctors or themselves.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        pk = view.kwargs["pk"]
        if uid != pk:
            qs = models.Patient.objects.filter(uuid=pk, doctors__id=uid)
            return qs.exists()
        return True


class HasSessionInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    session information, which is the patient or the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = uid == request.data["doctor_id"]
            is_patient = uid == request.data["patient_id"]
            return is_doctor or is_patient
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.id == uid
        is_patient = obj.patient.id == uid
        return is_doctor or is_patient


class HasAssignmentInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    assignment information, which is the patient or the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = uid == request.data["doctor_id"]
            is_patient = uid == request.data["patient_id"]
            return is_doctor or is_patient
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.id == uid
        is_patient = obj.patient.id == uid
        return is_doctor or is_patient


class IsAdviceOwner(permissions.BasePermission):
    """
    Custom permission to only allow only who owns the advice,
    which is the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = uid == request.data["doctor_id"]
            return is_doctor
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.id == uid
        return is_doctor


class HasAdviceInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    advice information, which is the patient or the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = uid == request.data["doctor_id"]
            is_patient = uid in request.data["patient_ids"]
            return is_doctor or is_patient
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.uuid == uid
        is_patient = any(patient.id == uid for patient in obj.patients)
        return is_doctor or is_patient
