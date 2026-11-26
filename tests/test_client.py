"""Tests for the Live Client Data API HTTP client (network replaced by a mock transport)."""

import ssl
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from touchstaune.live_client import LiveClient, LiveClientError
from touchstaune.live_client.client import build_ssl_context

Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler) -> LiveClient:
    return LiveClient(transport=httpx.MockTransport(handler))


def test_fetches_and_parses_all_game_data(raw_game: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "127.0.0.1"
        assert request.url.port == 2999
        assert request.url.path == "/liveclientdata/allgamedata"
        return httpx.Response(200, json=raw_game)

    with make_client(handler) as client:
        data = client.all_game_data()

    assert data is not None
    assert data.game_data.game_mode == "CLASSIC"


def test_returns_none_when_game_not_running() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with make_client(handler) as client:
        assert client.all_game_data() is None


def test_returns_none_while_loading() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"errorCode": "RESOURCE_NOT_FOUND"})

    with make_client(handler) as client:
        assert client.all_game_data() is None


def test_raises_on_non_json_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    with make_client(handler) as client, pytest.raises(LiveClientError, match="Non-JSON"):
        client.all_game_data()


def test_raises_on_non_object_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[1, 2, 3])

    with make_client(handler) as client, pytest.raises(LiveClientError, match="JSON object"):
        client.all_game_data()


def test_raises_on_schema_mismatch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    with make_client(handler) as client, pytest.raises(LiveClientError, match="allgamedata"):
        client.all_game_data()


def test_ssl_context_without_cert_disables_verification() -> None:
    assert build_ssl_context(None) is False


def test_ssl_context_with_missing_cert_file_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises((FileNotFoundError, ssl.SSLError)):
        build_ssl_context(tmp_path / "does-not-exist.pem")
