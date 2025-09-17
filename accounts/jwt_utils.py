import jwt
import datetime
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

 


def create_jwt(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + settings.JWT_EXP_DELTA,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "sub": str(user_id),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, payload.get('exp')

def create_refresh_jwt(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + settings.JWT_REFRESH_EXP_DELTA,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "sub": str(user_id),
    }
    token = jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_access_jwt(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Access token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid access token")
    
def decode_refresh_jwt(token: str) -> dict | None: 
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Refresh token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid refresh token")
