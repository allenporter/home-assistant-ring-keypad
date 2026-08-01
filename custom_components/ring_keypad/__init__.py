"""Ring Keypad custom component."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_ID, CONF_DEVICE_ID, Platform
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import Event, async_track_device_registry_updated_event
from homeassistant.helpers.helper_integration import async_remove_helper_devices

from .const import DOMAIN
from .model import alarm_command, alarm_state_command, chime_command

_LOGGER = logging.getLogger(__name__)


PLATFORMS: tuple[Platform] = (Platform.EVENT,)

CONF_ALARM_STATE = "alarm_state"
CONF_DELAY = "delay"
CONF_CHIME = "chime"
CONF_ALARM = "alarm"
CONF_VOLUME = "volume"

ZWAVE_DOMAIN = "zwave_js"
ZWAVE_SET_VALUE = "set_value"

UPDATE_ALARM_STATE_SERVICE = "update_alarm_state"
UPDATE_ALARM_STATE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_ALARM_STATE): cv.string,
            vol.Optional(CONF_DELAY): vol.Any(
                vol.All(vol.Coerce(int), vol.Range(min=0, max=300)), None
            ),
            vol.Required(ATTR_DEVICE_ID): cv.ensure_list,
        }
    ),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)

CHIME_SERVICE = "chime"
CHIME_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_CHIME): cv.string,
            vol.Optional(CONF_VOLUME): vol.Any(
                vol.All(vol.Coerce(int), vol.Range(min=1, max=100)), None
            ),
            vol.Required(ATTR_DEVICE_ID): cv.ensure_list,
        }
    ),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)

ALARM_SERVICE = "alarm"
ALARM_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_ALARM): cv.string,
            vol.Optional(CONF_VOLUME): vol.Any(
                vol.All(vol.Coerce(int), vol.Range(min=1, max=100)), None
            ),
            vol.Required(ATTR_DEVICE_ID): cv.ensure_list,
        }
    ),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ring Keypad component."""
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
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    device_registry = dr.async_get(hass)
    stored_device_id = entry.options[CONF_DEVICE_ID]

    if device_registry.async_is_composite_device_id(stored_device_id):
        split_devices = device_registry.async_get_devices_for_composite_device_id(
            stored_device_id
        )
        zwave_device = next(
            (
                d
                for d in split_devices
                if d.config_entry_id
                and (c_entry := hass.config_entries.async_get_entry(d.config_entry_id))
                and c_entry.domain == ZWAVE_DOMAIN
            ),
            None,
        )
        if zwave_device:
            stored_device_id = zwave_device.id
            hass.config_entries.async_update_entry(
                entry,
                options={**entry.options, CONF_DEVICE_ID: zwave_device.id},
            )

    async_remove_helper_devices(
        hass,
        helper_config_entry_id=entry.entry_id,
        source_device_id=stored_device_id,
        remove_all_devices=True,
    )

    try:
        device_entry = device_registry.async_get(stored_device_id)
    except vol.Invalid:
        _LOGGER.error(
            "Failed to setup ring_keypad for unknown device %s",
            stored_device_id,
        )
        return False

    if device_entry is None:
        _LOGGER.error(
            "Failed to setup ring_keypad for device not found %s",
            stored_device_id,
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
            changes = event.data["changes"]  # type: ignore[typeddict-item]  # ty:ignore[invalid-key]
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


def _resolve_zwave_device_ids(hass: HomeAssistant, device_ids: list[str]) -> list[str]:
    """Resolve target device IDs to underlying Z-Wave JS device IDs if needed."""
    device_registry = dr.async_get(hass)
    ring_entries = {
        entry.entry_id: entry.options.get(CONF_DEVICE_ID)
        for entry in hass.config_entries.async_entries(DOMAIN)
    }
    resolved_ids: list[str] = []
    for dev_id in device_ids:
        dev_entry = device_registry.async_get(dev_id)
        if (
            dev_entry
            and dev_entry.config_entry_id in ring_entries
            and (zwave_id := ring_entries[dev_entry.config_entry_id])
        ):
            resolved_ids.append(zwave_id)
        else:
            resolved_ids.append(dev_id)
    return resolved_ids


async def _zwave_set_value(
    hass: HomeAssistant,
    service_data: dict[str, Any],
    context: Context,
) -> None:
    if ATTR_DEVICE_ID in service_data:
        service_data[ATTR_DEVICE_ID] = _resolve_zwave_device_ids(
            hass, cv.ensure_list(service_data[ATTR_DEVICE_ID])
        )
    _LOGGER.debug("Sending Z-Wave JS set_value command: %s", service_data)
    await hass.services.async_call(
        ZWAVE_DOMAIN,
        ZWAVE_SET_VALUE,
        service_data=service_data,
        blocking=True,
        context=context,
    )


async def _async_update_alarm_state_service(call: ServiceCall) -> None:
    """Update the Ring Keypad to reflect the alarm state."""
    service_data: dict[str, Any] = {
        **alarm_state_command(call.data[CONF_ALARM_STATE], call.data.get(CONF_DELAY)),
        ATTR_DEVICE_ID: cv.ensure_list(call.data[ATTR_DEVICE_ID]),
    }
    await _zwave_set_value(
        call.hass,
        service_data=service_data,
        context=call.context,
    )


async def _async_chime_service(call: ServiceCall) -> None:
    """Send a chime to the Ring Keypad."""
    service_data: dict[str, Any] = {
        ATTR_DEVICE_ID: cv.ensure_list(call.data[ATTR_DEVICE_ID]),
        **chime_command(call.data[CONF_CHIME], call.data.get(CONF_VOLUME)),
    }
    await _zwave_set_value(
        call.hass,
        service_data=service_data,
        context=call.context,
    )


async def _async_alarm_service(call: ServiceCall) -> None:
    """Send an alarm to the Ring Keypad."""
    service_data: dict[str, Any] = {
        ATTR_DEVICE_ID: cv.ensure_list(call.data[ATTR_DEVICE_ID]),
        **alarm_command(call.data[CONF_ALARM], call.data.get(CONF_VOLUME)),
    }
    await _zwave_set_value(
        call.hass,
        service_data=service_data,
        context=call.context,
    )
