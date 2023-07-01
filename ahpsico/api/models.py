from django.db import models

from . import enums


class Doctor(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    crp = models.CharField(max_length=200)
    pix_key = models.CharField(max_length=200)
    payment_details = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} (CRP {self.crp})"


class Patient(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200)
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
    group_id = models.ForeignKey(SessionGroup, on_delete=models.CASCADE)
    group_index = models.IntegerField()
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
    date = models.DateField()

    def __str__(self):
        return f"Doctor: {self.doctor} - Patient: ${self.patient}"


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
