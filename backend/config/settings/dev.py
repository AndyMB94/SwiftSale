from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

SIMPLE_JWT["AUTH_COOKIE_SECURE"] = False  # noqa: F405
