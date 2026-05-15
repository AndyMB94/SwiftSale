import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Authenticated WebSocket consumer. Each user joins their own group
    `user_{user_id}` so tasks can push targeted notifications.
    """

    async def connect(self):
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f'user_{user.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Clients do not send messages — server-push only
        pass

    async def notification_message(self, event):
        """Handler for group messages sent by Celery tasks."""
        await self.send(text_data=json.dumps(event['payload']))

    # ── Private ──────────────────────────────────────────────────────────────

    async def _authenticate(self):
        from channels.db import database_sync_to_async

        from apps.authentication.models import User
        from apps.authentication.security import ACCESS_COOKIE

        cookies = self._parse_cookies()
        token_str = cookies.get(ACCESS_COOKIE)
        if not token_str:
            return None

        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
        except (TokenError, KeyError):
            return None

        @database_sync_to_async
        def get_user():
            try:
                return User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                return None

        return await get_user()

    def _parse_cookies(self) -> dict:
        headers = dict(self.scope.get('headers', []))
        raw = headers.get(b'cookie', b'').decode('utf-8', errors='ignore')
        cookies = {}
        for part in raw.split(';'):
            if '=' in part:
                key, _, value = part.strip().partition('=')
                cookies[key.strip()] = value.strip()
        return cookies
