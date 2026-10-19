"""Requesty conversation agent with Home Assistant tool calling."""

from __future__ import annotations

import json
import logging
from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.json import json_dumps

from .api import RequestyClient, RequestyError
from .const import (
    CONF_API_KEY,
    CONF_MODEL,
    DEFAULT_PROMPT,
    DOMAIN,
    MAX_TOOL_ITERATIONS,
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


def _tool_schema(tool: llm.Tool, custom_serializer=None) -> dict:
    """Convert a Home Assistant tool into the OpenAI-compatible function schema."""
    try:
        import probatio

        parameters = probatio.to_openapi(
            tool.parameters,
            custom_serializer=custom_serializer,
            openapi_version="3.1.0",
        )
    except (ImportError, TypeError, ValueError):
        parameters = {"type": "object", "properties": {}}

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or tool.name,
            "parameters": parameters,
        },
    }


def _normalize_content(value) -> str:
    """Normalize Requesty content payloads into a plain string."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item and isinstance(item["text"], str):
                    parts.append(item["text"])
                elif "content" in item and isinstance(item["content"], str):
                    parts.append(item["content"])
        return "".join(parts)

    if isinstance(value, dict):
        for key in ("text", "content"):
            item = value.get(key)
            if isinstance(item, str):
                return item
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def _content_to_messages(contents) -> list[dict]:
    """Convert Home Assistant chat log content to Chat Completions messages."""
    messages: list[dict] = []

    for item in contents:
        role = getattr(item, "role", None)
        content = getattr(item, "content", None)
        tool_calls = getattr(item, "tool_calls", None)

        if role in ("system", "user", "assistant") and content and not tool_calls:
            messages.append({"role": role, "content": _normalize_content(content)})

        if role == "assistant" and tool_calls:
            calls = []
            for call in tool_calls:
                calls.append(
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.tool_name,
                            "arguments": json.dumps(call.tool_args),
                        },
                    }
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": _normalize_content(content),
                    "tool_calls": calls,
                }
            )

        if isinstance(item, conversation.ToolResultContent):
            result = item.result
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": item.tool_call_id,
                    "content": json_dumps(
                        {"data": result.data, "error": result.error}
                    ),
                }
            )

    return messages


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Requesty conversation entity."""
    async_add_entities([RequestyConversationEntity(hass, entry)])


class RequestyConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """A Home Assistant conversation agent backed by Requesty."""

    _attr_has_entity_name = True
    _attr_name = "Chat"
    _attr_icon = "mdi:robot"
    _attr_supports_streaming = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._client = RequestyClient(hass, entry.data[CONF_API_KEY])

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Support all languages."""
        return MATCH_ALL

    @property
    def _settings(self) -> dict:
        return {**self.entry.data, **self.entry.options}

    @property
    def supported_features(self):
        """Advertise device control only when enabled."""
        if self._settings.get(CONF_LLM_HASS_API, True):
            return conversation.ConversationEntityFeature.CONTROL
        return conversation.ConversationEntityFeature(0)

    async def async_added_to_hass(self) -> None:
        """Register this entity as the active conversation agent."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the conversation agent."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Handle a user message and execute supported HA tools."""
        settings = self._settings

        if settings.get(CONF_LLM_HASS_API, True):
            try:
                await chat_log.async_provide_llm_data(
                    user_input.as_llm_context(DOMAIN),
                    "assist",
                    settings.get(CONF_PROMPT, DEFAULT_PROMPT),
                    user_input.extra_system_prompt,
                )
            except conversation.ConverseError as err:
                return err.as_conversation_result()

        for _ in range(MAX_TOOL_ITERATIONS):
            messages = _content_to_messages(chat_log.content)

            if not messages or messages[0].get("role") != "system":
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": settings.get(CONF_PROMPT, DEFAULT_PROMPT),
                    },
                )

            payload = {
                "model": settings[CONF_MODEL],
                "messages": messages,
                "max_tokens": 1024,
            }

            if chat_log.llm_api:
                tools = [
                    _tool_schema(tool, chat_log.llm_api.custom_serializer)
                    for tool in chat_log.llm_api.tools
                ]
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

            try:
                result = await self._client.chat_completion(payload)
            except RequestyError as err:
                _LOGGER.error("Requesty API request failed: %s", err)
                raise HomeAssistantError("Requesty API request failed.") from err
            
            _LOGGER.debug("Requesty raw completion result: %s", result)
            choices = result.get("choices", [])
            if not choices:
                raise HomeAssistantError("Requesty returned no response choices.")

            message = choices[0].get("message", {}) or {}
            text = _normalize_content(message.get("content"))

            calls = message.get("tool_calls") or []

            if calls:
                tool_inputs = []
                for call in calls:
                    function = call.get("function", {})
                    try:
                        arguments = json.loads(function.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        arguments = {}

                    tool_inputs.append(
                        llm.ToolInput(
                            id=call.get("id", ""),
                            tool_name=function.get("name", ""),
                            tool_args=arguments,
                        )
                    )

                chat_log.async_add_assistant_content(
                    conversation.AssistantContent(
                        agent_id=self.entity_id,
                        content=text,
                        tool_calls=tool_inputs,
                    )
                )

                if not chat_log.unresponded_tool_results:
                    break

                continue

            chat_log.async_add_assistant_content(
                conversation.AssistantContent(
                    agent_id=self.entity_id,
                    content=text or "",
                )
            )
            break

        else:
            _LOGGER.warning("Requesty reached maximum tool-call iterations.")

        return conversation.async_get_result_from_chat_log(user_input, chat_log)
