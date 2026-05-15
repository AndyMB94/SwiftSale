from unittest.mock import MagicMock, patch

import pytest
from ninja.errors import HttpError

from core.ratelimit import _get_ip, check_rate_limit


def _make_request(ip="1.2.3.4"):
    request = MagicMock()
    request.META = {"REMOTE_ADDR": ip}
    return request


class TestGetIp:
    def test_uses_remote_addr(self):
        request = _make_request("9.9.9.9")
        assert _get_ip(request) == "9.9.9.9"

    def test_prefers_x_forwarded_for(self):
        request = MagicMock()
        request.META = {
            "REMOTE_ADDR": "10.0.0.1",
            "HTTP_X_FORWARDED_FOR": "203.0.113.5, 10.0.0.1",
        }
        assert _get_ip(request) == "203.0.113.5"


class TestCheckRateLimit:
    def test_allows_requests_under_limit(self):
        request = _make_request()
        with patch("core.ratelimit.get_redis_connection") as mock_conn:
            mock_redis = MagicMock()
            mock_pipe = MagicMock()
            mock_pipe.execute.return_value = [1, True]  # count=1, expire ok
            mock_redis.pipeline.return_value = mock_pipe
            mock_conn.return_value = mock_redis

            # Should not raise
            check_rate_limit(request, key_prefix="login", rate="10/m")

    def test_blocks_request_over_limit(self):
        request = _make_request()
        with patch("core.ratelimit.get_redis_connection") as mock_conn:
            mock_redis = MagicMock()
            mock_pipe = MagicMock()
            mock_pipe.execute.return_value = [11, True]  # count=11 > 10
            mock_redis.pipeline.return_value = mock_pipe
            mock_conn.return_value = mock_redis

            with pytest.raises(HttpError) as exc:
                check_rate_limit(request, key_prefix="login", rate="10/m")
            assert exc.value.status_code == 429

    def test_fails_open_when_redis_unavailable(self):
        request = _make_request()
        with patch(
            "core.ratelimit.get_redis_connection", side_effect=Exception("Redis down")
        ):
            # Should not raise — fail open
            check_rate_limit(request, key_prefix="login", rate="10/m")

    def test_different_ips_have_independent_limits(self):
        req_a = _make_request("1.1.1.1")
        req_b = _make_request("2.2.2.2")

        call_count = {"n": 0}

        def mock_execute():
            call_count["n"] += 1
            return [1, True]  # always count=1, always under limit

        with patch("core.ratelimit.get_redis_connection") as mock_conn:
            mock_redis = MagicMock()
            mock_pipe = MagicMock()
            mock_pipe.execute.side_effect = mock_execute
            mock_redis.pipeline.return_value = mock_pipe
            mock_conn.return_value = mock_redis

            check_rate_limit(req_a, key_prefix="login", rate="10/m")
            check_rate_limit(req_b, key_prefix="login", rate="10/m")
            assert call_count["n"] == 2


class TestPrometheusEndpoint:
    def test_metrics_endpoint_exists(self, db):
        from django.test import Client

        client = Client()
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_contains_django_counters(self, db):
        from django.test import Client

        client = Client()
        response = client.get("/metrics")
        content = response.content.decode()
        assert "django_http_requests_total" in content
