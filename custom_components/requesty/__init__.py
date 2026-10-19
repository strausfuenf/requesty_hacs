"""Requesty AI Conversation integration."""

from __future__ import annotations

import importlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = ["conversation"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up a Requesty config entry."""

    # Import the platform in the executor to avoid blocking the event loop.
    await hass.async_add_executor_job(
        importlib.import_module,
        f"{__package__}.conversation",
    )

    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a Requesty config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
