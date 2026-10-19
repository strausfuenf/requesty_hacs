"""Tests for the Requesty API client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.requesty.api import RequestyClient, RequestyError


@pytest.mark.asyncio
async def test_list_models_returns_sorted_models():
    hass = MagicMock()
    client = RequestyClient(hass, "test-key")
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={
        "data": [{"id": "z-model"}, {"id": "a-model"}, {"name": "ignored"}]
    })
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    client._session.get = MagicMock(return_value=response)

    models = await client.list_models()

    assert [model["id"] for model in models] == ["a-model", "z-model"]
