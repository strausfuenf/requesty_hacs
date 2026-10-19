"""Config flow for Requesty."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .api import RequestyClient, RequestyError
from .const import (
    CONF_API_KEY,
    CONF_LLM_HASS_API,
    CONF_MODEL,
    CONF_PROMPT,
    DEFAULT_PROMPT,
    DOMAIN,
)


class RequestyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure Requesty."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Set up Requesty from the UI."""
        errors = {}
        if user_input is not None:
            client = RequestyClient(self.hass, user_input[CONF_API_KEY])
            try:
                models = await client.list_models()
            except RequestyError:
                errors["base"] = "cannot_connect"
            else:
                if not models:
                    errors["base"] = "no_models"
                else:
                    self._models = [item["id"] for item in models]
                    self._api_key = user_input[CONF_API_KEY]
                    return self.async_show_form(
                        step_id="model",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_MODEL, default=self._models[0]):
                                    vol.In(self._models),
                                vol.Optional(CONF_NAME, default="Requesty"): str,
                                vol.Optional(CONF_PROMPT, default=DEFAULT_PROMPT): str,
                                vol.Optional(CONF_LLM_HASS_API, default=True): bool,
                            }
                        ),
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_model(self, user_input=None):
        """Choose a model and finish setup."""
        if user_input is not None:
            await self.async_set_unique_id("requesty")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.pop(CONF_NAME, "Requesty"),
                data={
                    CONF_API_KEY: self._api_key,
                    **user_input,
                },
            )
        return self.async_abort(reason="unknown")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RequestyOptionsFlow(config_entry)


class RequestyOptionsFlow(config_entries.OptionsFlow):
    """Options flow to change model and prompt."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._models = []

    async def async_step_init(self, user_input=None):
        """Fetch models and display options."""
        errors = {}
        client = RequestyClient(
            self.hass, self.config_entry.data[CONF_API_KEY]
        )
        try:
            models = await client.list_models()
            self._models = [item["id"] for item in models]
        except RequestyError:
            errors["base"] = "cannot_connect"

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        if not self._models:
            self._models = [self.config_entry.options.get(
                CONF_MODEL, self.config_entry.data.get(CONF_MODEL, "")
            )]
            self._models = [model for model in self._models if model]

        if not self._models:
            return self.async_abort(reason="cannot_connect")

        current_model = self.config_entry.options.get(
            CONF_MODEL, self.config_entry.data.get(CONF_MODEL, self._models[0])
        )
        if current_model not in self._models:
            self._models.insert(0, current_model)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=current_model): vol.In(self._models),
                    vol.Optional(
                        CONF_PROMPT,
                        default=self.config_entry.options.get(
                            CONF_PROMPT,
                            self.config_entry.data.get(CONF_PROMPT, DEFAULT_PROMPT),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_LLM_HASS_API,
                        default=self.config_entry.options.get(
                            CONF_LLM_HASS_API,
                            self.config_entry.data.get(CONF_LLM_HASS_API, True),
                        ),
                    ): bool,
                }
            ),
            errors=errors,
        )
