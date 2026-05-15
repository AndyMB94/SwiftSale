import uuid

from apps.authentication.models import User


class UserService:
    @staticmethod
    def list_users() -> list[User]:
        return list(User.objects.all().order_by("-created_at"))

    @staticmethod
    def get_user(user_id: uuid.UUID) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("User not found")

    @staticmethod
    def create_user(email: str, full_name: str, role: str, password: str) -> User:
        if User.objects.filter(email=email).exists():
            raise ValueError("A user with this email already exists")
        return User.objects.create_user(
            email=email,
            full_name=full_name,
            role=role,
            password=password,
        )

    @staticmethod
    def update_user(
        user_id: uuid.UUID,
        full_name: str | None,
        role: str | None,
        is_active: bool | None,
    ) -> User:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("User not found")

        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role
        was_active = user.is_active
        if is_active is not None:
            user.is_active = is_active

        user.save()

        if is_active is False and was_active:
            from apps.audit.models import AuditLog
            from apps.audit.services import log_action

            log_action(
                action=AuditLog.Action.USER_DEACTIVATED,
                target_type="user",
                target_id=str(user.id),
                metadata={"email": user.email, "role": user.role},
            )

        return user
