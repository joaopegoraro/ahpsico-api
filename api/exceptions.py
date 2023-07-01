from rest_framework import status
from rest_framework.exceptions import APIException


class NoAuthToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "No authentication token provided"
    default_code = "no_auth_token"


class InvalidAuthToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid authentication token provided"
    default_code = "invalid_token"


class FirebaseError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "The user provided with the auth token is not a valid Firebase user, it has no Firebase UID"
    default_code = "no_firebase_uid"


class SignUpRequired(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "The user is not yet registered in the app"
    default_code = "signup_required"


class UserAlreadyRegistered(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "The user is already registered in the app"
    default_code = "user_already_registered"


class PatientNotRegistered(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "There are no patients registered with this phone number yet"
    default_code = "patient_not_registered"


class PatientAlreadyWithDoctor(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "You can't send the invite, the patient is already with the doctor"
    default_code = "patient_already_with_doctor"
