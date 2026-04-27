import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise PermissionDenied("Authentication token required.")

        token = auth_header[len("Bearer "):]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise PermissionDenied("Token has expired.")
        except jwt.InvalidTokenError:
            raise PermissionDenied("Invalid token.")

        return (payload, token)
