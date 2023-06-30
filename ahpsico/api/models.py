from django.db import models


class Doctor(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    crp = models.CharField(max_length=200)
    pix_key = models.CharField(max_length=200)
    payment_details = models.CharField(max_length=200)


class Patient(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200)
    doctors = models.ManyToManyField(Doctor)


class Invite(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=200)


class Advice(models.Model):
    message = models.CharField(max_length=200)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patients = models.ManyToManyField(Patient)


class SessionGroup(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)


class Session(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    group_id = models.ForeignKey(SessionGroup, on_delete=models.CASCADE)
    group_index = models.IntegerField()
    status = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    date = models.DateField()


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    delivery_session = models.ForeignKey(Session, on_delete=models.CASCADE)
