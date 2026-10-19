## AI Disclosure
Readme was designed with Copilot.
Code is from me assisted by Copilot. Mainly for Comments and refactoring

# Requesty AI Conversation for Home Assistant

A custom Home Assistant conversation agent that uses [Requesty](https://requesty.ai)'s OpenAI-compatible API. It supports model discovery from `GET /v1/models`, text conversations, and Home Assistant LLM tool calling for device control.

> **Status:** initial community integration. It has not yet been validated against every Home Assistant release or every Requesty model. Tool calling depends on the selected model/provider supporting OpenAI-compatible function calling.

## Features

- Configure from **Settings → Devices & services → Add integration → Requesty**.
- Fetch models available to your API key and choose one in the setup flow.
- Change model and system prompt later in integration options.
- Use Home Assistant's built-in LLM API to expose the tools/entities you have authorized.
- Works with Requesty model IDs and policies returned by `/v1/models`.

## Install with HACS

1. Push this repository to your own GitHub repository.
2. In HACS, open **Integrations → ⋮ → Custom repositories**.
3. Add the repository URL and select category **Integration**.
4. Download **Requesty AI Conversation**.
5. Restart Home Assistant.
6. Add the Requesty integration and enter your Requesty API key.

For HACS, the repository root must contain `custom_components/requesty/manifest.json`. Update `documentation` in `manifest.json` to your actual GitHub URL before publishing.

## Setup and use

1. Create an API key in the Requesty dashboard.
2. Add the integration in Home Assistant.
3. The integration queries `https://router.requesty.ai/v1/models`; select the model you want.
4. Enable **Allow Home Assistant device control** if you want the agent to call Home Assistant tools.
5. Select the Requesty agent in your Assist/voice pipeline.

The integration does not bypass Home Assistant's exposed-entity settings. Expose only the devices and services you want an LLM to control.

## Development

```bash
python -m pip install pytest pytest-asyncio
pytest -q
```

The integration uses Home Assistant's `aiohttp` session and has no external Python package requirements.

## Security notes

- Treat the Requesty API key as a secret. Do not commit it to Git.
- Device-control tool calls can operate real devices. Limit exposed entities and test with non-critical devices first.
- Requests go to Requesty's hosted API and then to the selected model/provider. Review Requesty's and the underlying provider's data handling and retention terms.
- The first version does not stream tokens to the UI.

## Troubleshooting

- **Cannot connect:** verify the API key, internet access, and the `/v1/models` endpoint.
- **Model missing:** only models returned by Requesty for the configured key are selectable. Check the Requesty dashboard/key permissions.
- **No device control:** enable device control in integration settings, select an agent/model with tool-calling support, and expose the relevant entities to Home Assistant's Assist/LLM API.
- **Tool calls fail:** try a model documented to support function calling. Models differ in tool-call compatibility.

## Repository layout

```text
custom_components/requesty/
  __init__.py
  api.py
  config_flow.py
  const.py
  conversation.py
  manifest.json
  strings.json
  translations/en.json
tests/
  test_api.py
  test_config_flow.py
```

## License

MIT
