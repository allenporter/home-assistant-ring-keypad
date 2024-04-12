"""Ring Keypad custom component."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import Event, async_track_device_registry_updated_event
from homeassistant.helpers import device_registry as dr


_LOGGER = logging.getLogger(__name__)


PLATFORMS: tuple[Platform] = (Platform.EVENT,)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    device_registry = dr.async_get(hass)

    try:
        device_entry = device_registry.async_get(entry.options[CONF_DEVICE_ID])
    except vol.Invalid:
        _LOGGER.error(
            "Failed to setup ring_keypad for unknown device %s",
            entry.options[CONF_DEVICE_ID],
        )
        return False

    async def async_registry_updated(
        event: Event[dr.EventDeviceRegistryUpdatedData],
    ) -> None:
        """Handle device registry update."""
        _LOGGER.debug("Device registry updated for Ring Keypad: %s", event.data)
        action = event.data["action"]
        if action == "remove":
            _LOGGER.debug("Removing Ring Keypad configuration entry")
            await hass.config_entries.async_remove(entry.entry_id)
        elif action == "update":
            changes = event.data["changes"]
            if "name" in changes:
                _LOGGER.debug("Reloading Ring Keypad configuration entry")
                await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(
        async_track_device_registry_updated_event(
            hass, device_entry.id, async_registry_updated
        )
    )

    await hass.config_entries.async_forward_entry_setups(
        entry,
        platforms=PLATFORMS,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
