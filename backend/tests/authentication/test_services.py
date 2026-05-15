import pytest
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import User
from apps.authentication.services import AuthService


@pytest.fixture
def active_user(db):
    return User.objects.create_user(
        email="cashier@test.com",
        password="securepass123",
        full_name="Test Cashier",
        role=User.Role.CASHIER,
    )


@pytest.fixture
def inactive_user(db):
    return User.objects.create_user(
        email="inactive@test.com",
        password="securepass123",
        full_name="Inactive User",
        role=User.Role.CASHIER,
        is_active=False,
    )


class TestAuthServiceLogin:
    def test_login_returns_user_and_tokens(self, active_user):
        user, access, refresh = AuthService.login("cashier@test.com", "securepass123")
        assert user.id == active_user.id
        assert isinstance(access, str) and len(access) > 0
        assert isinstance(refresh, str) and len(refresh) > 0

    def test_login_invalid_password_raises(self, active_user):
        with pytest.raises(ValueError, match="Invalid credentials"):
            AuthService.login("cashier@test.com", "wrongpassword")

    def test_login_unknown_email_raises(self, db):
        with pytest.raises(ValueError, match="Invalid credentials"):
            AuthService.login("nobody@test.com", "anypassword")

    def test_login_inactive_user_raises(self, inactive_user):
        with pytest.raises(ValueError, match="Invalid credentials"):
            AuthService.login("inactive@test.com", "securepass123")


class TestAuthServiceLogout:
    def test_logout_blacklists_refresh_token(self, active_user):
        _, _, refresh = AuthService.login("cashier@test.com", "securepass123")
        jti = RefreshToken(refresh)["jti"]
        AuthService.logout(refresh)
        assert BlacklistedToken.objects.filter(token__jti=jti).exists()

    def test_logout_with_invalid_token_does_not_raise(self, db):
        AuthService.logout("not-a-valid-token")


class TestAuthServiceRefresh:
    def test_refresh_returns_new_tokens(self, active_user):
        _, _, refresh = AuthService.login("cashier@test.com", "securepass123")
        new_access, new_refresh = AuthService.refresh_tokens(refresh)
        assert isinstance(new_access, str) and len(new_access) > 0
        assert new_refresh != refresh

    def test_refresh_blacklists_old_token(self, active_user):
        _, _, refresh = AuthService.login("cashier@test.com", "securepass123")
        old_jti = RefreshToken(refresh)["jti"]
        AuthService.refresh_tokens(refresh)
        assert BlacklistedToken.objects.filter(token__jti=old_jti).exists()

    def test_refresh_with_blacklisted_token_raises(self, active_user):
        _, _, refresh = AuthService.login("cashier@test.com", "securepass123")
        AuthService.logout(refresh)
        with pytest.raises(ValueError):
            AuthService.refresh_tokens(refresh)

    def test_refresh_with_invalid_token_raises(self, db):
        with pytest.raises(ValueError):
            AuthService.refresh_tokens("invalid-token")
