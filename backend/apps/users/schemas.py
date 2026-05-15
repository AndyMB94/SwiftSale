import uuid
from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import EmailStr


class UserCreateInput(Schema):
    email: EmailStr
    full_name: str
    role: Literal['admin', 'supervisor', 'cashier']
    password: str


class UserUpdateInput(Schema):
    full_name: str | None = None
    role: Literal['admin', 'supervisor', 'cashier'] | None = None
    is_active: bool | None = None


class UserOut(Schema):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserListOut(Schema):
    count: int
    results: list[UserOut]
