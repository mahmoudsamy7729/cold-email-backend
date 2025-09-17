import datetime
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from ..jwt_utils import create_jwt, create_refresh_jwt, decode_refresh_jwt


class AuthService:
    @staticmethod
    def login_user(username: str, password: str) -> tuple[str, datetime.datetime, str]:
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials")

        access_token, exp = create_jwt(user.id)
        refresh_token = create_refresh_jwt(user.id)
        return access_token, exp, refresh_token
    
    @staticmethod
    def refresh_user_token(refresh_token: str) -> tuple[str, datetime.datetime]:
        if not refresh_token:
            raise AuthenticationFailed("Refresh token is missing")
        
        payload = decode_refresh_jwt(refresh_token)
        user_id = payload.get("user_id")
        token, exp = create_jwt(user_id)
        return token, exp