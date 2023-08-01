import os

import firebase_admin
from firebase_admin import auth, credentials
from rest_framework.authentication import BaseAuthentication

from . import exceptions

cred = credentials.Certificate(
    {
        "type": os.environ.get("FIREBASE_ACCOUNT_TYPE"),
        "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
        "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace(r"\n", "\n"),
        "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
        "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
        "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get(
            "FIREBASE_AUTH_PROVIDER_X509_CERT_URL"
        ),
        "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
    }
)
default_app = firebase_admin.initialize_app(cred)


class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """Get the authorization Token. It raises an exception when no token is given"""
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise exceptions.NoAuthToken()
        """Removes the 'Bearer' prefix of the token"""
        id_token = auth_header.split(" ").pop()
        """Decodes the token. It raises an exception when it fails."""
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise exceptions.InvalidAuthToken()
        """Get the uid from the decoded token, then use it to find and return the user object"""
        try:
            uid = decoded_token.get("uid")
            user = auth.get_user(uid)
        except Exception:
            raise exceptions.FirebaseError()
        return (user, None)
