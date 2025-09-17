from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services.auth_service import AuthService
from django.conf import settings
from rest_framework import generics
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]
        user = serializer.save()

        token, exp,refresh_token  = AuthService.login_user(user.username, password)
        response = Response({
            "access_token": token,
            "expires_at": int(exp.timestamp())
        }, status=status.HTTP_201_CREATED)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite='Lax',
            max_age=int(settings.JWT_REFRESH_EXP_DELTA.total_seconds())
        )
        return response

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        token, exp,refresh_token  = AuthService.login_user(username, password)
        
        response = Response({
            "access_token": token,
            "expires_at": int(exp.timestamp())
        }, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite='Lax',
            max_age=int(settings.JWT_REFRESH_EXP_DELTA.total_seconds())
        )
        return response
    

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        token, exp = AuthService.refresh_user_token(refresh_token)
        return Response({
            "access_token": token,
            "expires_at": int(exp.timestamp())
        }, status=status.HTTP_200_OK)
       
       
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": request.user.username, "email": request.user.email}, status=status.HTTP_200_OK)

