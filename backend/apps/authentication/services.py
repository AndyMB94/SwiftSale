from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AuthService:
    @staticmethod
    def login(email: str, password: str) -> tuple[User, str, str]:
        user = authenticate(username=email, password=password)
        if user is None:
            from apps.audit.models import AuditLog
            from apps.audit.services import log_action

            log_action(
                action=AuditLog.Action.LOGIN_FAILED,
                target_type="user",
                target_id=email,
                metadata={"email": email},
            )
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is disabled")
        refresh = RefreshToken.for_user(user)
        return user, str(refresh.access_token), str(refresh)

    @staticmethod
    def refresh_tokens(refresh_token: str) -> tuple[str, str]:
        try:
            old_token = RefreshToken(refresh_token)
            old_token.blacklist()
            user = User.objects.get(id=old_token["user_id"])
            new_refresh = RefreshToken.for_user(user)
            return str(new_refresh.access_token), str(new_refresh)
        except TokenError as e:
            raise ValueError(str(e))

    @staticmethod
    def logout(refresh_token: str) -> None:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass
