"""Config flow for Octopus Cosy to Emoncms integration."""
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_API_KEY,
    CONF_EMONCMS_URL,
    CONF_ENTITIES,
    CONF_NODE_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_EMONCMS_URL,
    DEFAULT_NODE_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import OctopusCosyEmoncmsCoordinator

_LOGGER = logging.getLogger(__name__)


class OctopusCosyEmoncmsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Octopus Cosy to Emoncms."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._config_data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the API key and URL
            if not user_input.get(CONF_API_KEY):
                errors[CONF_API_KEY] = "api_key_required"
            elif not user_input.get(CONF_EMONCMS_URL):
                errors[CONF_EMONCMS_URL] = "url_required"
            elif not user_input.get(CONF_NODE_NAME):
                errors[CONF_NODE_NAME] = "node_name_required"
            else:
                # Create entry directly
                return self.async_create_entry(
                    title=f"Emoncms: {user_input[CONF_NODE_NAME]}",
                    data=user_input,
                )

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_EMONCMS_URL, default=DEFAULT_EMONCMS_URL
                ): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
                vol.Required(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_NODE_NAME, default=DEFAULT_NODE_NAME
                ): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Optional(CONF_ENTITIES, default=[]): EntitySelector(
                    EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10,
                        max=3600,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="seconds",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OctopusCosyEmoncmsOptionsFlow()


class OctopusCosyEmoncmsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Octopus Cosy to Emoncms."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    CONF_ENTITIES: user_input.get(CONF_ENTITIES, []),
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                },
            )
            return self.async_create_entry(title="", data={})

        # Get current values
        current_entities = self.config_entry.data.get(CONF_ENTITIES, [])
        current_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ENTITIES, default=current_entities
                ): EntitySelector(EntitySelectorConfig(multiple=True)),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_interval
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10,
                        max=3600,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="seconds",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
