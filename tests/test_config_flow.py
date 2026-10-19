"""Basic tests for Requesty config flow validation."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries

from custom_components.requesty.const import DOMAIN


@pytest.mark.asyncio
async def test_user_step_shows_model_selection(hass):
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert flow["type"] == "form"
    assert flow["step_id"] == "user"

    with patch(
        "custom_components.requesty.config_flow.RequestyClient.list_models",
        new=AsyncMock(return_value=[{"id": "openai/example"}]),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], {"api_key": "test-key"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "model"
