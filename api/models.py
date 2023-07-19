from django.db import models

from . import enums


class Doctor(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=200, blank=True, default="")
    crp = models.CharField(max_length=200, blank=True, default="")
    pix_key = models.CharField(max_length=200, blank=True, default="")
    payment_details = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"{self.name} (CRP {self.crp})"


class Patient(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, unique=True)
    doctors = models.ManyToManyField(Doctor)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class Invite(models.Model):
    phone_number = models.CharField(max_length=200)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    def __str__(self):
        return f"to {self.patient} - from {self.doctor})"


class Advice(models.Model):
    message = models.CharField(max_length=200)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patients = models.ManyToManyField(Patient)

    def __str__(self):
        return f"{self.message} - from {self.doctor})"


class SessionGroup(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    def __str__(self):
        return f"Doctor: {self.doctor} - Patient: ${self.patient}"


class Session(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    group_id = models.ForeignKey(SessionGroup, on_delete=models.CASCADE, null=True)
    group_index = models.IntegerField(null=True)
    status = models.CharField(
        max_length=200,
        choices=enums.SessionStatus.choices(),
        default=enums.SessionStatus.NOT_CONFIRMED,
    )
    type = models.CharField(
        max_length=200,
        choices=enums.SessionType.choices(),
        default=enums.SessionType.INDIVIDUAL,
    )
    date = models.DateTimeField()

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    def __str__(self):
        return f"Doctor: {self.doctor} - Patient: ${self.patient}"


class Schedule(models.Model):
    date = models.DateTimeField()
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    def __str__(self):
        return f"Schedule: {self.date} Doctor: {self.doctor}"


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=200,
        choices=enums.AssignmentStatus.choices(),
        default=enums.AssignmentStatus.PENDING,
    )
    delivery_session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title}"
