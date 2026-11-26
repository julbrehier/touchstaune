"""HTTP client for the official Live Client Data API, served by the game on localhost."""

import logging
import ssl
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import httpx
from pydantic import ValidationError

from touchstaune.live_client.models import AllGameData

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://127.0.0.1:2999/liveclientdata"


class LiveClientError(RuntimeError):
    """The API answered, but with a payload that could not be interpreted."""


def build_ssl_context(ca_cert: Path | str | None) -> ssl.SSLContext | bool:
    """TLS settings for the local API.

    The game serves HTTPS with a Riot-signed certificate issued for ``rclient``, not for
    ``127.0.0.1``. With Riot's root certificate (``riotgames.pem``) we verify the chain but
    not the hostname. Without it we skip verification: the traffic never leaves the machine.
    """
    if ca_cert is None:
        return False
    context = ssl.create_default_context(cafile=str(ca_cert))
    context.check_hostname = False
    return context


def parse_all_game_data(payload: dict[str, Any]) -> AllGameData:
    """Validate an ``/allgamedata`` payload, raising :class:`LiveClientError` if malformed."""
    try:
        return AllGameData.model_validate(payload)
    except ValidationError as exc:
        raise LiveClientError(f"Unexpected /allgamedata payload: {exc}") from exc


class LiveClient:
    """Thin, synchronous client for the Live Client Data API.

    "No game running" is a normal state, not an error: fetch methods return ``None`` when
    the API is unreachable or not ready. Malformed payloads raise :class:`LiveClientError`.

    Use as a context manager so the underlying connection pool is closed::

        with LiveClient() as client:
            data = client.all_game_data()
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        ca_cert: Path | str | None = None,
        timeout: float = 2.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            verify=build_ssl_context(ca_cert),
            timeout=timeout,
            transport=transport,
        )

    def fetch_raw(self, endpoint: str) -> dict[str, Any] | None:
        """GET ``endpoint`` and return its JSON object, or ``None`` if no game is available."""
        try:
            response = self._http.get(endpoint)
        except httpx.TransportError as exc:
            logger.debug("Live Client API unreachable (%s): %s", endpoint, exc)
            return None

        if response.status_code != httpx.codes.OK:
            # The API answers 404 while the game is still loading.
            logger.debug("Live Client API %s returned HTTP %s", endpoint, response.status_code)
            return None

        try:
            payload = response.json()
        except ValueError as exc:
            raise LiveClientError(f"Non-JSON response from {endpoint}") from exc
        if not isinstance(payload, dict):
            raise LiveClientError(
                f"Expected a JSON object from {endpoint}, got {type(payload).__name__}"
            )
        return payload

    def all_game_data(self) -> AllGameData | None:
        """Parsed ``/allgamedata`` snapshot, or ``None`` if no game is running."""
        payload = self.fetch_raw("allgamedata")
        return None if payload is None else parse_all_game_data(payload)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
