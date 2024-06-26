"""Event entity platform for Ring Keypad."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .model import KEYAD_EVENTS

_LOGGER = logging.getLogger(__name__)

ZWAVE_NOTIFICATION = "zwave_js_notification"
CONF_EVENT_TYPE = "event_type"
CONF_EVENT_DATA = "event_data"

KEYPAD_EVENT_TYPES = {
    keypad_event_type: name for name, keypad_event_type, _ in KEYAD_EVENTS
}
ENTITY_EVENT_TYPES = {
    keypad_event_type: entity_event_type
    for _, keypad_event_type, entity_event_type in KEYAD_EVENTS
}
ENTITY_EVENT_TYPE_VALUES = list(set(ENTITY_EVENT_TYPES.values()))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize a config entry."""

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(config_entry.options[CONF_DEVICE_ID])
    if device_entry is None:
        raise HomeAssistantError("Unable to load device entry")
    async_add_entities(
        [
            RingKeypadEventEntity(
                config_entry.entry_id,
                device_entry,
            )
        ]
    )


class RingKeypadEventEntity(EventEntity):
    """Event entity for the Ring Keypad Z-Wave notification events."""

    _attr_has_entity_name = True
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = ENTITY_EVENT_TYPE_VALUES
    _attr_should_poll = False
    _attr_translation_key = "keypad_event"

    def __init__(self, config_entry_id: str, device_entry: dr.DeviceEntry) -> None:
        """Initialize RingKeypadEventEntity."""
        self._attr_unique_id = config_entry_id
        self._device_id = device_entry.id
        self._attr_device_info = DeviceInfo(
            identifiers=device_entry.identifiers,
        )

    @callback
    def _async_handle_event(self, event: Event[dict[str, Any]]) -> None:
        """Handle the demo button event."""
        _LOGGER.debug("Received ZWave notification: data=%s", event.data)
        event_data = event.data
        if (
            not (device_id := event_data.get(CONF_DEVICE_ID))
            or device_id != self._device_id
        ):
            return
        if (event_type := event_data.get(CONF_EVENT_TYPE)) is None:
            return
        _LOGGER.debug("Received ZWave notification for keypad: %s", event)
        if not (event_type_name := ENTITY_EVENT_TYPES.get(event_type)):
            _LOGGER.info(
                "Ring Keypad received ZWave notification with unknown event type: %s",
                event_type_name,
            )
            return
        keypad_event_type = KEYPAD_EVENT_TYPES[event_type]
        self._trigger_event(
            event_type_name,
            {"button": keypad_event_type, "code": event_data.get(CONF_EVENT_DATA)},
        )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks with your device API/library."""
        self.async_on_remove(
            self.hass.bus.async_listen(ZWAVE_NOTIFICATION, self._async_handle_event)
        )
