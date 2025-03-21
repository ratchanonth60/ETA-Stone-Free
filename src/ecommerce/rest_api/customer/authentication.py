import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


class JWTAuthentication(BaseAuthentication):

    def authenticate(self, request):

        access_token = self.get_access_token(request)

        if not access_token:
            return None

        payload = self.decode_jwt(access_token)
        user = self.get_associated_user(payload)

        self.enforce_csrf(request)
        return (user, None)

    def get_access_token(self, request):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return None

        try:
            return authorization_header.split(' ')[1]
        except IndexError as e:
            raise exceptions.AuthenticationFailed('Token prefix missing') from e

    def decode_jwt(self, access_token):
        try:
            return jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=settings.ALGO_HAS,
                audience="my_audience",   # Add audience check
                issuer="my_issuer"        # Add issuer check
            )
        except jwt.ExpiredSignatureError as e:
            raise exceptions.AuthenticationFailed('access_token expired') from e
        except jwt.DecodeError as e:
            raise exceptions.AuthenticationFailed('Token is invalid') from e
        except jwt.InvalidAudienceError as e:
            raise exceptions.AuthenticationFailed('Invalid audience') from e
        except jwt.InvalidIssuerError as e:
            raise exceptions.AuthenticationFailed('Invalid issuer') from e
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Fail {e}') from e

    def get_associated_user(self, payload):
        User = get_user_model()
        user = User.objects.filter(id=payload['user_id']).first()
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')
        if not user.is_active:
            raise exceptions.AuthenticationFailed('user is inactive')
        return user

    def enforce_csrf(self, request):
        if request.method in ['POST', 'PUT']:
            check = CSRFCheck()
            check.process_request(request)
            if reason := check.process_view(request, None, (), {}):
                raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
