import uuid
from ninja import Router
from ninja.errors import HttpError

from apps.authentication.security import cookie_auth
from core.permissions import require_admin, require_admin_or_supervisor
from .schemas import UserCreateInput, UserListOut, UserOut, UserUpdateInput
from .services import UserService

router = Router(tags=['Users'])


@router.get('/', response=UserListOut, auth=cookie_auth)
def list_users(request):
    require_admin_or_supervisor(request)
    users = UserService.list_users()
    return {'count': len(users), 'results': users}


@router.post('/', response={201: UserOut}, auth=cookie_auth)
def create_user(request, payload: UserCreateInput):
    require_admin(request)
    try:
        user = UserService.create_user(
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            password=payload.password,
        )
    except ValueError as e:
        raise HttpError(400, str(e))
    return 201, user


@router.get('/{user_id}', response=UserOut, auth=cookie_auth)
def get_user(request, user_id: uuid.UUID):
    require_admin_or_supervisor(request)
    try:
        user = UserService.get_user(user_id)
    except ValueError as e:
        raise HttpError(404, str(e))
    return user


@router.put('/{user_id}', response=UserOut, auth=cookie_auth)
def update_user(request, user_id: uuid.UUID, payload: UserUpdateInput):
    require_admin(request)
    try:
        user = UserService.update_user(
            user_id,
            payload.full_name,
            payload.role,
            payload.is_active,
        )
    except ValueError as e:
        raise HttpError(404, str(e))
    return user
