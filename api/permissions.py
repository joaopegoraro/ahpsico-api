from rest_framework import permissions

from . import models


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        pk = view.kwargs["pk"]
        return str(uid) == pk


class IsDoctor(permissions.BasePermission):
    """
    Custom permission to only allow users who are doctor
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        is_doctor = models.Doctor.objects.filter(pk=uid).exists()
        return is_doctor


class HasPatientInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    patient information, which is their doctors or themselves.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        pk = view.kwargs["pk"]
        if str(uid) != pk:
            qs = models.Patient.objects.filter(pk=pk, doctors__pk=uid)
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
            is_doctor = str(uid) == request.data["doctor_id"]
            is_patient = str(uid) == request.data["patient_id"]
            return is_doctor or is_patient
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.pk == uid
        is_patient = obj.patient.pk == uid
        return is_doctor or is_patient


class HasAssignmentInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    assignment information, which is the patient or the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = str(uid) == request.data["doctor_id"]
            is_patient = str(uid) == request.data["patient_id"]
            return is_doctor or is_patient
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.pk == uid
        is_patient = obj.patient.pk == uid
        return is_doctor or is_patient


class IsAdviceOwner(permissions.BasePermission):
    """
    Custom permission to only allow only who owns the advice,
    which is the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = str(uid) == request.data["doctor_id"]
            return is_doctor
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.pk == uid
        return is_doctor


class HasAdviceInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    advice information, which is the patient or the doctor.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        if request.method == "POST" or request.method == "PUT":
            is_doctor = str(uid) == request.data["doctor_id"]
            is_patient = str(uid) in request.data["patient_ids"]
            return is_doctor or is_patient
        return True

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.pk == uid
        is_patient = obj.patients.filter(pk=uid).exists()
        return is_doctor or is_patient


class IsInviteOwner(permissions.BasePermission):
    """
    Custom permission to only allow only who owns the invite,
    which is the patient.
    """

    def has_permission(self, request, view):
        uid = request.user.uid
        pk = view.kwargs["pk"]
        qs = models.Invite.objects.filter(pk=pk, patient__pk=uid)
        return qs.exists()


class HasInviteInformation(permissions.BasePermission):
    """
    Custom permission to only allow only who should have access to the
    invite information, which is the patient or the doctor.
    """

    def has_object_permission(self, request, view, obj):
        uid = request.user.uid
        is_doctor = obj.doctor.pk == uid
        is_patient = obj.patient.pk == uid
        return is_doctor or is_patient
