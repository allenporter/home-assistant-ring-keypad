"""Ring Keypad custom component."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, Context
from homeassistant.helpers.event import Event, async_track_device_registry_updated_event
from homeassistant.helpers import device_registry as dr, config_validation as cv

from .const import DOMAIN, CONF_ALARM_STATE
from .model import alarm_state_command, chime_command, alarm_command

_LOGGER = logging.getLogger(__name__)


PLATFORMS: tuple[Platform] = (Platform.EVENT,)

UPDATE_ALARM_STATE_SERVICE = "update_alarm_state"
CHIME_SERVICE = "chime"
ALARM_SERVICE = "alarm"
CONF_CHIME = "chime"
CONF_ALARM = "alarm"

ZWAVE_DOMAIN = "zwave_js"
CONST_ZWAVE_SET_VALUE = "set_value"


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

    async def _zwave_set_value(
        device_id: str, service_data: dict[str, str], context: Context
    ) -> None:
        await hass.services.async_call(
            ZWAVE_DOMAIN,
            CONST_ZWAVE_SET_VALUE,
            service_data=service_data,
            blocking=True,
            context=context,
            target={"device_id": device_id},
        )

    async def _async_update_alarm_state_service(call: ServiceCall) -> None:
        """Update the Ring Keypad to reflect the alarm state."""
        await _zwave_set_value(
            device_id=call.data[CONF_DEVICE_ID],
            service_data=alarm_state_command(call.data[CONF_ALARM_STATE]),
            context=call.context,
        )

    async def _async_chime_service(call: ServiceCall) -> None:
        """Send a chime to the Ring Keypad."""
        await _zwave_set_value(
            device_id=call.data[CONF_DEVICE_ID],
            service_data=chime_command(call.data[CONF_CHIME]),
            context=call.context,
        )

    async def _async_alarm_service(call: ServiceCall) -> None:
        """Send an alarm to the Ring Keypad."""
        await _zwave_set_value(
            device_id=call.data[CONF_DEVICE_ID],
            service_data=alarm_command(call.data[CONF_ALARM]),
            context=call.context,
        )

    if DOMAIN not in hass.data:
        _LOGGER.debug("Registering Ring Keypad services")
        hass.services.async_register(
            DOMAIN,
            UPDATE_ALARM_STATE_SERVICE,
            _async_update_alarm_state_service,
            schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Required(CONF_ALARM_STATE): cv.string,
                }
            ),
        )
        hass.services.async_register(
            DOMAIN,
            CHIME_SERVICE,
            _async_chime_service,
            schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Required(CONF_CHIME): cv.string,
                }
            ),
        )
        hass.services.async_register(
            DOMAIN,
            ALARM_SERVICE,
            _async_alarm_service,
            schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Required(CONF_ALARM): cv.string,
                }
            ),
        )
        hass.data[DOMAIN] = {}

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
