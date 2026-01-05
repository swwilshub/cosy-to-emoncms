"""Data update coordinator for Octopus Cosy to Emoncms integration."""
import json
import logging
import re
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OctopusCosyEmoncmsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from entities and sending to Emoncms."""

    def __init__(
        self,
        hass: HomeAssistant,
        emoncms_url: str,
        api_key: str,
        node_name: str,
        entities: list[str],
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.emoncms_url = emoncms_url.rstrip("/")
        self.api_key = api_key
        self.node_name = node_name
        self.entities = entities
        self.hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    @staticmethod
    def _clean_sensor_name(name: str) -> str:
        """
        Clean and shorten sensor name for Emoncms compatibility.

        Works with both entity IDs and friendly names.

        Emoncms restrictions:
        - Reserved chars: ! # $ & ' ( ) * + , / : ; = ? @ [ ]
        - Recommended length: ~10 characters max
        """
        # Remove domain prefix if present (e.g., "sensor.")
        if "." in name:
            name = name.split(".", 1)[1]

        # Convert to lowercase for consistency
        name = name.lower()

        # Replace spaces with underscores (common in friendly names)
        name = name.replace(" ", "_")

        # Common patterns to shorten (works for both entity IDs and friendly names)
        replacements = {
            "octopus_energy_heat_pump_": "hp_",
            "heat_pump_": "hp_",
            "current_temperature": "cur_t",
            "temperature": "temp",
            "outdoor": "out",
            "middle_landing": "mid_land",
            "hvac_action_numeric": "hvac_num",
            "hvac_action": "hvac",
            "hot_water": "hw",
            "heating": "heat",
            "sensor": "sens",
        }

        # Apply replacements
        for old, new in replacements.items():
            name = name.replace(old, new)

        # Remove MAC-like addresses (00_1e_5e_09_02_ba_5a_f0)
        name = re.sub(r'_[0-9a-f]{2}(_[0-9a-f]{2})+', '', name)

        # Remove reserved characters for Emoncms (including parentheses from friendly names)
        reserved = "!#$&'()*+,/:;=?@[]"
        for char in reserved:
            name = name.replace(char, "")

        # Replace multiple underscores/spaces with single underscore
        name = re.sub(r'[_\s]+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip("_")

        return name

    async def _async_update_data(self):
        """Fetch data from entities and send to Emoncms."""
        if not self.entities:
            _LOGGER.debug("No entities configured, skipping update")
            return {}

        # Collect entity data
        data = {}
        for entity_id in self.entities:
            state = self.hass.states.get(entity_id)
            if state is None:
                _LOGGER.warning(
                    "Entity %s not found. Check Developer Tools -> States to find the correct entity ID. "
                    "For Octopus heat pump entities, search for 'climate.octopus' or 'water_heater.octopus'",
                    entity_id
                )
                continue

            # Use friendly name if available, otherwise fall back to entity_id
            # This gives much better names in Emoncms (e.g., "Temperature (middle landing)")
            friendly_name = state.attributes.get("friendly_name", entity_id)

            # Clean sensor name base for Emoncms (remove reserved chars, shorten)
            sensor_base_name = self._clean_sensor_name(friendly_name)

            # Check if this is a climate entity - extract useful attributes
            domain = entity_id.split(".")[0] if "." in entity_id else ""

            if domain == "climate":
                # Climate entities have multiple useful attributes
                _LOGGER.debug("Processing climate entity %s ('%s')", entity_id, friendly_name)

                # Extract and send useful climate attributes
                climate_attrs = {
                    "current_temperature": "cur_t",
                    "temperature": "target_t",
                    "hvac_action": "hvac_act",
                    "hvac_mode": "hvac_mode",
                    "current_humidity": "humid",
                }

                for attr_name, suffix in climate_attrs.items():
                    attr_value = state.attributes.get(attr_name)
                    if attr_value is not None:
                        field_name = f"{sensor_base_name}_{suffix}"

                        # Try to convert to numeric
                        try:
                            numeric_value = float(attr_value)
                            data[field_name] = numeric_value
                            _LOGGER.debug("Collected %s: %s", field_name, numeric_value)
                        except (ValueError, TypeError):
                            # Send as text (e.g., hvac_action: "heating")
                            data[field_name] = str(attr_value)
                            _LOGGER.debug("Collected %s: %s (text)", field_name, attr_value)

                # Also send the main state (the HVAC mode)
                data[sensor_base_name] = state.state
                _LOGGER.debug("Collected %s (state): %s", sensor_base_name, state.state)

            elif domain == "water_heater":
                # Water heater entities (for hot water heat pump)
                _LOGGER.debug("Processing water_heater entity %s ('%s')", entity_id, friendly_name)

                # Extract and send useful water heater attributes
                water_heater_attrs = {
                    "current_temperature": "cur_t",
                    "temperature": "target_t",
                    "operation_mode": "mode",
                }

                for attr_name, suffix in water_heater_attrs.items():
                    attr_value = state.attributes.get(attr_name)
                    if attr_value is not None:
                        field_name = f"{sensor_base_name}_{suffix}"

                        # Try to convert to numeric
                        try:
                            numeric_value = float(attr_value)
                            data[field_name] = numeric_value
                            _LOGGER.debug("Collected %s: %s", field_name, numeric_value)
                        except (ValueError, TypeError):
                            # Send as text
                            data[field_name] = str(attr_value)
                            _LOGGER.debug("Collected %s: %s (text)", field_name, attr_value)

                # Also send the main state
                data[sensor_base_name] = state.state
                _LOGGER.debug("Collected %s (state): %s", sensor_base_name, state.state)

            else:
                # Regular sensor - just send the state
                _LOGGER.debug("Mapped %s ('%s') -> %s", entity_id, friendly_name, sensor_base_name)

                try:
                    # Try to convert state to numeric value
                    numeric_value = float(state.state)
                    data[sensor_base_name] = numeric_value
                    _LOGGER.debug(
                        "Collected %s: %s", sensor_base_name, numeric_value
                    )
                except (ValueError, TypeError):
                    # If not numeric, send as is (for string states like 'heating', 'idle', etc.)
                    # Emoncms can handle text in log feeds
                    data[sensor_base_name] = state.state
                    _LOGGER.debug(
                        "Collected %s: %s (non-numeric)", sensor_base_name, state.state
                    )

        if not data:
            _LOGGER.debug("No valid entity data collected")
            return {}

        # Send to Emoncms
        try:
            await self._send_to_emoncms(data)
            _LOGGER.debug("Successfully sent data to Emoncms: %s", data)
            return data
        except Exception as err:
            _LOGGER.error("Error sending data to Emoncms: %s", err)
            raise UpdateFailed(f"Error sending data to Emoncms: {err}") from err

    async def _send_to_emoncms(self, data: dict) -> None:
        """Send data to Emoncms Input API."""
        url = f"{self.emoncms_url}/input/post"

        # Build the JSON data string
        # Emoncms expects: node=X&fulljson={data}&apikey=KEY
        params = {
            "node": self.node_name,
            "apikey": self.api_key,
            "fulljson": json.dumps(data),  # Properly encode dict as JSON
        }

        _LOGGER.debug("Sending to Emoncms: %s with params: %s", url, {**params, "apikey": "***"})

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(
                        f"Emoncms API returned status {response.status}: {text}"
                    )

                result = await response.text()
                _LOGGER.debug("Emoncms response: %s", result)

                if "ok" not in result.lower():
                    raise Exception(f"Emoncms API returned unexpected response: {result}")

    async def async_update_entities(self, entities: list[str]) -> None:
        """Update the list of entities to monitor."""
        self.entities = entities
        await self.async_refresh()

    async def async_update_interval(self, interval: int) -> None:
        """Update the scan interval."""
        self.update_interval = timedelta(seconds=interval)
