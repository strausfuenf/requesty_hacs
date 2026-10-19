"""Constants for the Requesty integration."""

from typing import Final

DOMAIN: Final = "requesty"
CONF_API_KEY: Final = "api_key"
CONF_MODEL: Final = "model"
CONF_PROMPT: Final = "prompt"
CONF_LLM_HASS_API: Final = "llm_hass_api"
DEFAULT_BASE_URL: Final = "https://router.requesty.ai/v1"
DEFAULT_PROMPT: Final = (
    "You are a helpful assistant for Home Assistant. "
    "Use the available Home Assistant tools when the user asks to control or inspect "
    "devices. Never claim an action succeeded unless a tool result confirms it."
)
REQUEST_TIMEOUT: Final = 60
MAX_TOOL_ITERATIONS: Final = 8
