import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from apps.authentication.models import User
from config.asgi import application


def make_token(user):
    from rest_framework_simplejwt.tokens import AccessToken

    return str(AccessToken.for_user(user))


def ws_scope(token: str) -> dict:
    return {
        "type": "websocket",
        "path": "/ws/notifications/",
        "headers": [(b"cookie", f"access_token={token}".encode())],
        "query_string": b"",
    }


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email="ws_cashier@test.com",
        password="testpass",
        full_name="WS Cashier",
        role=User.Role.CASHIER,
    )


@pytest.fixture
def supervisor(db):
    return User.objects.create_user(
        email="ws_supervisor@test.com",
        password="testpass",
        full_name="WS Supervisor",
        role=User.Role.SUPERVISOR,
    )


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email="ws_admin@test.com",
        password="testpass",
        full_name="WS Admin",
        role=User.Role.ADMIN,
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cashier_rejected_without_token():
    communicator = WebsocketCommunicator(
        application,
        "/ws/notifications/",
        headers=[(b"cookie", b"")],
    )
    connected, code = await communicator.connect()
    assert not connected
    assert code == 4001


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cashier_connects_and_joins_own_group(cashier):
    token = make_token(cashier)
    communicator = WebsocketCommunicator(application, "/ws/notifications/", headers=list(ws_scope(token)["headers"]))
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{cashier.id}",
        {"type": "notification.message", "payload": {"event": "test"}},
    )
    msg = await communicator.receive_json_from(timeout=2)
    assert msg["event"] == "test"

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cashier_does_not_receive_staff_notifications(cashier):
    token = make_token(cashier)
    communicator = WebsocketCommunicator(application, "/ws/notifications/", headers=list(ws_scope(token)["headers"]))
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "staff_notifications",
        {"type": "notification.message", "payload": {"event": "inventory.low_stock"}},
    )
    assert await communicator.receive_nothing(timeout=1)

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_supervisor_receives_staff_notifications(supervisor):
    token = make_token(supervisor)
    communicator = WebsocketCommunicator(application, "/ws/notifications/", headers=list(ws_scope(token)["headers"]))
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "staff_notifications",
        {"type": "notification.message", "payload": {"event": "inventory.low_stock", "product_name": "Test"}},
    )
    msg = await communicator.receive_json_from(timeout=2)
    assert msg["event"] == "inventory.low_stock"

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_admin_receives_staff_notifications(admin):
    token = make_token(admin)
    communicator = WebsocketCommunicator(application, "/ws/notifications/", headers=list(ws_scope(token)["headers"]))
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "staff_notifications",
        {"type": "notification.message", "payload": {"event": "inventory.low_stock", "product_name": "Test"}},
    )
    msg = await communicator.receive_json_from(timeout=2)
    assert msg["event"] == "inventory.low_stock"

    await communicator.disconnect()
