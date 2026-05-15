from ninja.security import APIKeyCookie
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'
ACCESS_MAX_AGE = 15 * 60
REFRESH_MAX_AGE = 7 * 24 * 60 * 60


class CookieJWTAuth(APIKeyCookie):
    param_name = ACCESS_COOKIE

    def authenticate(self, request, key):
        if not key:
            return None
        try:
            validated_token = AccessToken(key)
            from apps.authentication.models import User
            user = User.objects.get(id=validated_token['user_id'])
            return user if user.is_active else None
        except (TokenError, Exception):
            return None


cookie_auth = CookieJWTAuth()
