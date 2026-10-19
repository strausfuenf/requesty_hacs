"""Small asynchronous client for the Requesty OpenAI-compatible API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_BASE_URL, REQUEST_TIMEOUT


class RequestyError(Exception):
    """Raised when Requesty returns an error."""


class RequestyClient:
    """Requesty HTTP API client."""

    def __init__(self, hass, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        self._session = async_get_clientsession(hass)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    @property
    def headers(self) -> dict[str, str]:
        """Return API request headers."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Title": "Home Assistant Requesty",
        }

    async def list_models(self) -> list[dict[str, Any]]:
        """Fetch available models."""
        try:
            async with self._session.get(
                f"{self._base_url}/models",
                headers=self.headers,
                timeout=self._timeout,
            ) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    message = payload.get("error", {}).get("message", response.reason)
                    raise RequestyError(str(message))
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise RequestyError("Could not connect to Requesty.") from err

        models = payload.get("data", [])
        return sorted(
            [item for item in models if isinstance(item, dict) and item.get("id")],
            key=lambda item: item["id"].lower(),
        )

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a chat completion."""
        try:
            async with self._session.post(
                f"{self._base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self._timeout,
            ) as response:
                result = await response.json(content_type=None)
                if response.status >= 400:
                    error = result.get("error", {})
                    message = error.get("message", response.reason)
                    raise RequestyError(str(message))
                return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise RequestyError("Could not connect to Requesty.") from err
