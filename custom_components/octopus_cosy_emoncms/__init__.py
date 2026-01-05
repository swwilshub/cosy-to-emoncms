"""The Octopus Cosy to Emoncms integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_API_KEY,
    CONF_EMONCMS_URL,
    CONF_ENTITIES,
    CONF_NODE_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import OctopusCosyEmoncmsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Octopus Cosy to Emoncms from a config entry."""
    emoncms_url = entry.data[CONF_EMONCMS_URL]
    api_key = entry.data[CONF_API_KEY]
    node_name = entry.data[CONF_NODE_NAME]
    entities = entry.data.get(CONF_ENTITIES, [])
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.info(
        "Setting up Octopus Cosy to Emoncms integration: URL=%s, Node=%s, Entities=%s, Interval=%ss",
        emoncms_url,
        node_name,
        len(entities),
        scan_interval,
    )

    # Create the coordinator
    coordinator = OctopusCosyEmoncmsCoordinator(
        hass,
        emoncms_url,
        api_key,
        node_name,
        entities,
        scan_interval,
    )

    # Store the coordinator and setup data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "cancel_interval": None,
    }

    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()

    # Set up periodic updates using time interval tracker
    # DataUpdateCoordinator needs listeners to keep running, but we don't have entities
    # So we manually trigger updates at the configured interval
    async def _async_update(_now):
        """Trigger coordinator update."""
        await coordinator.async_request_refresh()

    # Schedule periodic updates
    cancel_interval = async_track_time_interval(
        hass,
        _async_update,
        timedelta(seconds=scan_interval),
    )

    # Store the cancel callback so we can restart it when interval changes
    hass.data[DOMAIN][entry.entry_id]["cancel_interval"] = cancel_interval

    # Also register it for cleanup on unload
    entry.async_on_unload(cancel_interval)

    # Listen for config entry updates
    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Octopus Cosy to Emoncms integration")

    # Remove the coordinator
    hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update a config entry."""
    _LOGGER.info("Updating Octopus Cosy to Emoncms integration")

    # Get the coordinator and cancel callback
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OctopusCosyEmoncmsCoordinator = entry_data["coordinator"]
    old_cancel_interval = entry_data["cancel_interval"]

    # Update entities and interval
    entities = entry.data.get(CONF_ENTITIES, [])
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    await coordinator.async_update_entities(entities)
    await coordinator.async_update_interval(scan_interval)

    # Cancel the old time tracker and create a new one with the updated interval
    if old_cancel_interval:
        old_cancel_interval()

    async def _async_update(_now):
        """Trigger coordinator update."""
        await coordinator.async_request_refresh()

    # Schedule periodic updates with the new interval
    cancel_interval = async_track_time_interval(
        hass,
        _async_update,
        timedelta(seconds=scan_interval),
    )

    # Store the new cancel callback
    entry_data["cancel_interval"] = cancel_interval
    entry.async_on_unload(cancel_interval)

    _LOGGER.info(
        "Updated Octopus Cosy to Emoncms: Entities=%s, Interval=%ss",
        len(entities),
        scan_interval,
    )
