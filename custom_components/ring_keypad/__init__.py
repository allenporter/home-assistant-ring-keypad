"""Ring Keypad custom component."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, ATTR_DEVICE_ID, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, Context
from homeassistant.helpers.event import Event, async_track_device_registry_updated_event
from homeassistant.helpers import device_registry as dr, config_validation as cv

from .const import DOMAIN
from .model import alarm_state_command, chime_command, alarm_command

_LOGGER = logging.getLogger(__name__)


PLATFORMS: tuple[Platform] = (Platform.EVENT,)

CONF_ALARM_STATE = "alarm_state"
CONF_DELAY = "delay"
CONF_CHIME = "chime"
CONF_ALARM = "alarm"

ZWAVE_DOMAIN = "zwave_js"
ZWAVE_SET_VALUE = "set_value"

UPDATE_ALARM_STATE_SERVICE = "update_alarm_state"
UPDATE_ALARM_STATE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_ALARM_STATE): cv.string,
            vol.Optional(CONF_DELAY): vol.Any(cv.positive_int, None),
            **cv.ENTITY_SERVICE_FIELDS,
        }
    ),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)

CHIME_SERVICE = "chime"
CHIME_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_CHIME): cv.string,
            **cv.ENTITY_SERVICE_FIELDS,
        }
    ),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)

ALARM_SERVICE = "alarm"
ALARM_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_ALARM): cv.string,
            **cv.ENTITY_SERVICE_FIELDS,
        }
    ),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)


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
        target_device: str | list[str], service_data: dict[str, str], context: Context
    ) -> None:
        await hass.services.async_call(
            ZWAVE_DOMAIN,
            ZWAVE_SET_VALUE,
            service_data=service_data,
            blocking=True,
            context=context,
            target={"device_id": target_device},
        )

    async def _async_update_alarm_state_service(call: ServiceCall) -> None:
        """Update the Ring Keypad to reflect the alarm state."""
        await _zwave_set_value(
            target_device=call.data[ATTR_DEVICE_ID],
            service_data=alarm_state_command(
                call.data[CONF_ALARM_STATE], call.data.get(CONF_DELAY)
            ),
            context=call.context,
        )

    async def _async_chime_service(call: ServiceCall) -> None:
        """Send a chime to the Ring Keypad."""
        await _zwave_set_value(
            target_device=call.data[ATTR_DEVICE_ID],
            service_data=chime_command(call.data[CONF_CHIME]),
            context=call.context,
        )

    async def _async_alarm_service(call: ServiceCall) -> None:
        """Send an alarm to the Ring Keypad."""
        await _zwave_set_value(
            target_device=call.data[ATTR_DEVICE_ID],
            service_data=alarm_command(call.data[CONF_ALARM]),
            context=call.context,
        )

    if DOMAIN not in hass.data:
        _LOGGER.debug("Registering Ring Keypad services")
        hass.services.async_register(
            DOMAIN,
            UPDATE_ALARM_STATE_SERVICE,
            _async_update_alarm_state_service,
            UPDATE_ALARM_STATE_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            CHIME_SERVICE,
            _async_chime_service,
            CHIME_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            ALARM_SERVICE,
            _async_alarm_service,
            ALARM_SCHEMA,
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
