from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account.adapter import get_adapter
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from dj_rest_auth.serializers import JWTSerializer
from django.conf import settings
from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model
# TOKEN
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.conf import settings
from multiprocessing import AuthenticationError
from datetime import datetime
from django.http import JsonResponse  

class CustomRegisterSerializer(RegisterSerializer):

  def validate_username(self, username):
        codes = ['사과', '오이', '호박', '당근' , '시금치', '열무' , '토란', '감자', '브로콜리', '양배추', '비트', '테스트1', '테스트2', '테스트3', '테스트4', '테스트5', 'nuseum',
        'NPP01', 'NPP02', 'NPP03', 'NPP04', 'NPP05', 'NPP06', 'NPP07', 'NPP08', 'NPP09', 'NPP10', 'NPP11', 'NPP12', 'NPP13', 'NPP14', 'NPP15', 'NPP16', 'NPP17', 'NPP18', 'NPP19', 'NPP20']
        username = get_adapter().clean_username(username)
        if username not in codes:
          raise serializers.ValidationError(_("올바른 코드를 입력하세요!"))
        return username

class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ['id', 'username', 'is_superuser']

class UserListSerializer(serializers.Serializer):
  userList = UserSerializer(many=True)

# 로그인 response 처리
# Get the UserModel
UserModel = get_user_model()

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """

    @staticmethod
    def validate_username(username):
        if 'allauth.account' not in settings.INSTALLED_APPS:
            # We don't need to call the all-auth
            # username validator unless its installed
            return username

        from allauth.account.adapter import get_adapter
        username = get_adapter().clean_username(username)
        return username

    class Meta:
        extra_fields = []
        # see https://github.com/iMerica/dj-rest-auth/issues/181
        # UserModel.XYZ causing attribute error while importing other
        # classes from `serializers.py`. So, we need to check whether the auth model has
        # the attribute or not
        if hasattr(UserModel, 'USERNAME_FIELD'):
            extra_fields.append(UserModel.USERNAME_FIELD)
        if hasattr(UserModel, 'EMAIL_FIELD'):
            extra_fields.append(UserModel.EMAIL_FIELD)
        if hasattr(UserModel, 'first_name'):
            extra_fields.append('first_name')
        if hasattr(UserModel, 'last_name'):
            extra_fields.append('last_name')
        if hasattr(UserModel, 'is_superuser'): # 추가
            extra_fields.append('is_superuser')
        model = UserModel
        fields = ('pk', *extra_fields)
        read_only_fields = ('email',)


class CustomJWTSerializer(JWTSerializer):
  """
  Serializer for JWT authentication.
  """
  access_token = serializers.CharField()
  refresh_token = serializers.CharField()
  user = serializers.SerializerMethodField()

  def get_user(self, obj):
      """
      Required to allow using custom USER_DETAILS_SERIALIZER in
      JWTSerializer. Defining it here to avoid circular imports
      """
      rest_auth_serializers = getattr(settings, 'REST_AUTH_SERIALIZERS', {})

      JWTUserDetailsSerializer = import_string(
          rest_auth_serializers.get(
              'USER_DETAILS_SERIALIZER',
              # 'dj_rest_auth.serializers.UserDetailsSerializer',
              'accounts.serializers.UserDetailsSerializer',
          ),
      )

      user_data = JWTUserDetailsSerializer(obj['user'], context=self.context).data
      return user_data

# TOKEN
class CustomTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    token_class = RefreshToken

    # AssertionError: .validate() should return the validated data
    def validate(self, attrs):
        # TEST
        # token = self.context['request'].COOKIES.get('my-app-auth')

        # request header에서 access token 추출 (**Bearer parsing 필요!**)
        # DEPLOY
        try:
            token = self.context['request'].META['HTTP_AUTHORIZATION'].split(" ")[1]
        except KeyError:
            data = {
                'err_msg' : 'request header에 Authorization 필드(access token)가 존재하지 않습니다.',
                'err_code' : 'NOT_ACCEPTABLE'
            }
            return data

        # refresh = self.token_class(attrs["refresh"])
        # print(self.context['request'].META)
        # print(f"my-refresh-token : {self.context['request'].COOKIES.get('my-refresh-token')}")
        # cookie에 refresh token이 삭제된 경우 예외처리**
        if self.context['request'].COOKIES.get('my-refresh-token') == None:
            data = {
                'err_msg' : 'cookie에 refresh token이 없습니다.',
                'err_code' : 'NOT_ACCEPTABLE'
            }
            return data
        refresh = self.token_class(self.context['request'].COOKIES.get('my-refresh-token'))
        # print(refresh)
        if not token:
            raise AuthenticationError('UnAuthenticated!')
        try: # access 토큰 만료 X
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            access_token_expired_time = datetime.fromtimestamp(payload['exp'])
            now = datetime.now()
            # print(f"ACCESS_TOKEN_EXP_TIME : {access_token_expired_time}")
            # print(f"NOW : {now}")
            # 예외처리 : 비정상적인 처리
            if now < access_token_expired_time:
                # refresh 토큰 blacklist추가 == 강제 로그아웃
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass
                data = {
                    'err_msg' : '비정상적인 토큰 발급입니다. 강제 로그아웃 되었습니다.'
                }
                return data

        except jwt.ExpiredSignatureError: # access 토큰 만료시 에러 발생
            # 여기서 토큰 재발급?
            # 만료 시간 이후에 발급받는 경우 : 정상적인 처리
            data = {"access": str(refresh.access_token)}

            if settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS']:
                if settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION']:
                    try:
                        # Attempt to blacklist the given refresh token
                        refresh.blacklist()
                    except AttributeError:
                        # If blacklist app not installed, `blacklist` method will
                        # not be present
                        pass

                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()

                data["refresh"] = str(refresh)
 
                    
            return data

        
        