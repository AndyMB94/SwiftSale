from django.http import HttpResponse
from ninja import Router
from ninja.errors import HttpError

from .models import User
from .schemas import LoginInput, LoginOut, MessageOut, UserOut
from .security import ACCESS_COOKIE, ACCESS_MAX_AGE, REFRESH_COOKIE, REFRESH_MAX_AGE, cookie_auth
from .services import AuthService

router = Router(tags=['Authentication'])


def _set_auth_cookies(response: HttpResponse, access: str, refresh: str) -> None:
    response.set_cookie(ACCESS_COOKIE, access, max_age=ACCESS_MAX_AGE, httponly=True, samesite='Lax')
    response.set_cookie(REFRESH_COOKIE, refresh, max_age=REFRESH_MAX_AGE, httponly=True, samesite='Lax')


def _clear_auth_cookies(response: HttpResponse) -> None:
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)


@router.post('/login', response=LoginOut, auth=None)
def login(request, response: HttpResponse, payload: LoginInput):
    from core.ratelimit import check_rate_limit
    check_rate_limit(request, key_prefix='login', rate='10/m')

    try:
        user, access, refresh = AuthService.login(payload.email, payload.password)
    except ValueError as e:
        raise HttpError(401, str(e))

    _set_auth_cookies(response, access, refresh)

    return LoginOut(
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role),
        message='Login successful',
    )


@router.post('/refresh', response=MessageOut, auth=None)
def refresh_token(request, response: HttpResponse):
    old_refresh = request.COOKIES.get(REFRESH_COOKIE)
    if not old_refresh:
        raise HttpError(401, 'Refresh token not found')

    try:
        access, new_refresh = AuthService.refresh_tokens(old_refresh)
    except ValueError as e:
        raise HttpError(401, str(e))

    _set_auth_cookies(response, access, new_refresh)
    return MessageOut(message='Token refreshed')


@router.post('/logout', response=MessageOut, auth=cookie_auth)
def logout(request, response: HttpResponse):
    refresh = request.COOKIES.get(REFRESH_COOKIE)
    if refresh:
        AuthService.logout(refresh)
    _clear_auth_cookies(response)
    return MessageOut(message='Logged out successfully')


@router.get('/me', response=UserOut, auth=cookie_auth)
def me(request):
    user: User = request.auth
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)
