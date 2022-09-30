from dj_rest_auth.views import LoginView
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
# from dj_rest_auth import jwt_auth
from dj_rest_auth.serializers import JWTSerializerWithExpiration, TokenSerializer
from .serializers import CustomJWTSerializer
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.http import JsonResponse
# TOKEN
from dj_rest_auth.models import get_token_model
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.app_settings import create_token
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken 

class CustomLoginView(LoginView):

  def get_response_serializer(self):
        if getattr(settings, 'REST_USE_JWT', False):

            if getattr(settings, 'JWT_AUTH_RETURN_EXPIRATION', False):
                response_serializer = JWTSerializerWithExpiration
            else:
                response_serializer = CustomJWTSerializer

        else:
            response_serializer = TokenSerializer
        return response_serializer

  # 토큰 생성 로직
  def login(self):
        self.user = self.serializer.validated_data['user']
        token_model = get_token_model()

        if getattr(settings, 'REST_USE_JWT', False):
            # 토큰 생성 => REFRESH 체크
            # 이때 user_id의 가장 최근(latest) token을 outstanding/blacklistedtoken 테이블에서 확인
            # => 가장 최근에 발급된 해당유저의 refresh 토큰이 blacklistedtoken에 존재하는지 확인 
            print(OutstandingToken.objects.filter(user_id=self.user).latest('created_at').id)
            latest_refresh_token = OutstandingToken.objects.filter(user_id=self.user).latest('created_at')
            # print(BlacklistedToken.objects.get(token_id=latest_refresh_token_id)) # 없으면 에러 발생 -> 생성X
            print(BlacklistedToken.objects.filter(token_id=latest_refresh_token.id)) # 없으면 빈 리스트 -> 생성O
            # check : 로그아웃 된 적 없이 다시 로그인이 된다면... (이 경우 브라우저를 닫아도 자동적으로 로그아웃(blacklist에 저장)되는 로직 필요?) 
            print(f"유저의 가장 최근 REFRESH TOKEN이 blacklist에 존재하는지 CHECK(정상 로그아웃됨): {BlacklistedToken.objects.filter(token_id=latest_refresh_token.id).exists()}")
            if not BlacklistedToken.objects.filter(token_id=latest_refresh_token.id).exists():
                BlacklistedToken.objects.create(token_id=latest_refresh_token.id)
                self.access_token, self.refresh_token = "", ""
                # data = {
                #     'err_msg' : '이전에 로그아웃을 하지 않고 브라우저를 종료하여 로그아웃 처리되었습니다. 다시 로그인해주세요!'
                # }
                # return Response(data=data, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                self.access_token, self.refresh_token = jwt_encode(self.user)
            # self.access_token, self.refresh_token = jwt_encode(self.user)
            
        elif token_model:
            self.token = create_token(token_model, self.user, self.serializer)

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            self.process_login()

  def get_response(self):
        serializer_class = self.get_response_serializer()

        if getattr(settings, 'REST_USE_JWT', False):
            from rest_framework_simplejwt.settings import (
                api_settings as jwt_settings,
            )
            access_token_expiration = (timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME)
            refresh_token_expiration = (timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME)
            return_expiration_times = getattr(settings, 'JWT_AUTH_RETURN_EXPIRATION', False)
            auth_httponly = getattr(settings, 'JWT_AUTH_HTTPONLY', False)

            data = {
                'user': self.user,
                'access_token': self.access_token,
            }
            # print(data['user'].is_superuser)
            
            # 중복 로그인처리
            if self.refresh_token == "":
                data = {
                    'err_msg' : '이전에 로그아웃을 하지 않고 브라우저를 종료하여 로그아웃 처리되었습니다. 다시 로그인해주세요!',
                    'err_code' : 'NOT_ACCEPTABLE'
                }
                return Response(data=data, status=status.HTTP_406_NOT_ACCEPTABLE)

            if not auth_httponly:
                data['refresh_token'] = self.refresh_token
            else:
                # Wasnt sure if the serializer needed this
                data['refresh_token'] = ""

            if return_expiration_times:
                data['access_token_expiration'] = access_token_expiration
                data['refresh_token_expiration'] = refresh_token_expiration

            serializer = serializer_class(
                instance=data,
                context=self.get_serializer_context(),
            )
        elif self.token:
            serializer = serializer_class(
                instance=self.token,
                context=self.get_serializer_context(),
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

        response = Response(serializer.data, status=status.HTTP_200_OK)
        if getattr(settings, 'REST_USE_JWT', False):
            from dj_rest_auth.jwt_auth import set_jwt_cookies
            set_jwt_cookies(response, self.access_token, self.refresh_token)
            # custom_set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response

# TOKEN
class CustomTokenRefreshView(TokenViewBase):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """

    _serializer_class = settings.SIMPLE_JWT['TOKEN_REFRESH_SERIALIZER']

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # cookie에 refresh token이 삭제된 경우 예외처리 **
        # print(f"RESULT : {serializer.validated_data}")
        if 'err_code' in serializer.validated_data.keys():
            return JsonResponse(serializer.validated_data, status=406)

        response = JsonResponse(serializer.validated_data, status=200)
        # try:
        #     response.set_cookie('my-app-auth', serializer.validated_data['access'],secure=True, httponly=True, samesite='None')
        # except KeyError:
        #     pass

        # return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return response

# token_refresh = TokenRefreshView.as_view()
