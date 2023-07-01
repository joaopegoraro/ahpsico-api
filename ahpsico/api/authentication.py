from rest_framework.authentication import BaseAuthentication
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings

from . import exceptions

"""SETUP FIREBASE CREDENTIALS"""
cred = credentials.Certificate(
    {
        "type": settings.FIREBASE_ACCOUNT_TYPE,
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "auth_uri": settings.FIREBASE_AUTH_URI,
        "token_uri": settings.FIREBASE_TOKEN_URI,
        "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL,
    }
)
default_app = firebase_admin.initialize_app(cred)


class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """Get the authorization Token. It raises an exception when no token is given"""
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise exceptions.NoAuthToken("No auth token provided")
        """Decodes the token. It raises an exception when it fails."""
        id_token = auth_header.split(" ").pop()
        decoded_token = None
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise exceptions.InvalidAuthToken("Invalid auth token")
        """Get the uid from the decoded token, then use it to find and return the user object"""
        try:
            uid = decoded_token.get("uid")
            user = auth.get_user(uid)
        except Exception:
            raise exceptions.FirebaseError()
        return (user, None)
