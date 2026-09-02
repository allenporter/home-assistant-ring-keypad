"""Tests for the Ring Keypad component."""

import attr
import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.ring_keypad.const import (
    DOMAIN,
)


@pytest.fixture(autouse=True)
def mock_setup_integration(config_entry: MockConfigEntry) -> None:
    """Setup the integration"""


async def test_device_registry(
    hass: HomeAssistant,
    zwave_device_id: str,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test event entity default state."""

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry


async def test_remove_device(
    hass: HomeAssistant,
    zwave_device_id: str,
    zwave_config_entry: MockConfigEntry,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test removing the device and that everything is unloaded."""

    assert len(hass.config_entries.async_entries("ring_keypad")) == 1
    assert config_entry.state == config_entries.ConfigEntryState.LOADED

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry
    assert zwave_config_entry.entry_id in device_entry.config_entries

    # Entity is registered
    state = hass.states.get("event.device_name_button")
    assert state

    # Remove the device and our config entry should also get removed
    device_registry.async_remove_device(zwave_device_id)
    await hass.async_block_till_done()

    assert config_entry.state == config_entries.ConfigEntryState.NOT_LOADED

    # Entity is no longer registered
    state = hass.states.get("event.device_name_button")
    assert state is None

    # Config entry is gone
    assert len(hass.config_entries.async_entries("ring_keypad")) == 0


async def test_rename_device(
    hass: HomeAssistant,
    zwave_device_id: str,
    zwave_config_entry: MockConfigEntry,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test renaming the device and that everything is reloaded."""

    assert len(hass.config_entries.async_entries("ring_keypad")) == 1
    assert config_entry.state == config_entries.ConfigEntryState.LOADED

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry
    assert zwave_config_entry.entry_id in device_entry.config_entries

    # Entity is registered
    state = hass.states.get("event.device_name_button")
    assert state
    assert state.attributes.get("friendly_name") == "Device name Button"

    device_registry.async_update_device(zwave_device_id, name="Other name")
    await hass.async_block_till_done()

    # Entity is renamed
    state = hass.states.get("event.device_name_button")
    assert state
    assert state.attributes.get("friendly_name") == "Other name Button"


@pytest.mark.parametrize(
    ("alarm_state", "delay", "volume", "property", "property_key", "value"),
    [
        ("arming", "45", None, 18, "timeout", "0m45s"),
        ("arming", None, None, 18, "timeout", "1m0s"),
        ("arming", None, 50, 18, "timeout", "1m0s"),
        ("armed_home", None, None, 10, 1, 100),
        ("armed_home", None, 50, 10, 9, 50),
        ("triggered", None, None, 13, 9, 100),
        ("triggered", None, 50, 13, 9, 50),
    ],
)
async def test_set_alarm_state_services(
    hass: HomeAssistant,
    zwave_device_id: str,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    alarm_state: str,
    delay: str | None,
    volume: int | None,
    property: int,
    property_key: int,
    value: int,
) -> None:
    """Test event entity default state."""

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry

    call_service = async_mock_service(hass, "zwave_js", "set_value")

    await hass.services.async_call(
        DOMAIN,
        "update_alarm_state",
        service_data={
            "alarm_state": alarm_state,
            "delay": delay,
            "volume": volume,
        },
        blocking=True,
        target={"device_id": [zwave_device_id]},
    )
    assert call_service
    assert call_service[0].data == {
        "command_class": "135",
        "device_id": [zwave_device_id],
        "endpoint": 0,
        "property": property,
        "property_key": property_key,
        "value": value,
    }


@pytest.mark.parametrize(
    ("chime", "volume", "property", "property_key", "value"),
    [
        ("wind_chime", None, 98, 9, 100),
        ("wind_chime", 50, 98, 9, 50),
        ("bing_bong", None, 99, 9, 100),
        ("invalid_code", None, 9, 1, 100),
        ("invalid_code", 50, 9, 9, 50),
        ("need_bypass", None, 16, 1, 100),
    ],
)
async def test_chime_service(
    hass: HomeAssistant,
    zwave_device_id: str,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    chime: str,
    volume: int | None,
    property: int,
    property_key: int,
    value: int,
) -> None:
    """Test event entity default state."""

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry

    call_service = async_mock_service(hass, "zwave_js", "set_value")

    await hass.services.async_call(
        DOMAIN,
        "chime",
        service_data={
            "chime": chime,
            "volume": volume,
        },
        blocking=True,
        target={"device_id": [zwave_device_id]},
    )
    assert call_service
    assert call_service[0].data == {
        "command_class": "135",
        "device_id": [zwave_device_id],
        "endpoint": 0,
        "property": property,
        "property_key": property_key,
        "value": value,
    }


@pytest.mark.parametrize(
    ("alarm", "volume", "property", "property_key", "value"),
    [
        ("burglar", None, 13, 9, 100),
        ("smoke", None, 14, 9, 100),
        ("co2", 50, 15, 9, 50),
    ],
)
async def test_alarm_service(
    hass: HomeAssistant,
    zwave_device_id: str,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    alarm: str,
    volume: int | None,
    property: int,
    property_key: int,
    value: int,
) -> None:
    """Test event entity default state."""

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry

    call_service = async_mock_service(hass, "zwave_js", "set_value")

    await hass.services.async_call(
        DOMAIN,
        "alarm",
        service_data={
            "alarm": alarm,
            "volume": volume,
        },
        blocking=True,
        target={"device_id": [zwave_device_id]},
    )
    assert call_service
    assert call_service[0].data == {
        "command_class": "135",
        "device_id": [zwave_device_id],
        "endpoint": 0,
        "property": property,
        "property_key": property_key,
        "value": value,
    }


async def test_composite_device_id_resolution(
    hass: HomeAssistant,
    zwave_device_id: str,
    zwave_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test setup resolves composite device IDs to real Z-Wave JS device IDs and cleans up helper devices."""
    composite_id = "composite_device_123"

    ring_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "device_id": composite_id,
        },
        title="Ring Keypad",
    )
    ring_entry.add_to_hass(hass)

    helper_device = device_registry.async_get_or_create(
        config_entry_id=ring_entry.entry_id,
        identifiers={(DOMAIN, "keypad_helper")},
        name="Orphaned Keypad Helper",
    )
    assert helper_device

    zwave_device = device_registry.async_get(zwave_device_id)
    assert isinstance(zwave_device, dr.DeviceEntry)

    # Re-create real HA composite device split state using registry items
    device_registry._devices[zwave_device.id] = attr.evolve(
        zwave_device, composite_device_id=composite_id
    )
    device_registry._devices[helper_device.id] = attr.evolve(
        helper_device, composite_device_id=composite_id
    )

    assert await hass.config_entries.async_setup(ring_entry.entry_id)
    await hass.async_block_till_done()

    # CONF_DEVICE_ID in options should be updated from composite_id to zwave_device_id
    assert ring_entry.options["device_id"] == zwave_device_id
