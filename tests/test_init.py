"""Tests for the Ring Keypad component."""

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
    assert config_entry.entry_id in device_entry.config_entries


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
    assert config_entry.entry_id in device_entry.config_entries

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
    assert config_entry.entry_id in device_entry.config_entries

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
    ("alarm_state", "delay", "property", "property_key", "value"),
    [
        ("arming", "45", 18, "timeout", "0m45s"),
        ("arming", None, 18, "timeout", "1m0s"),
        ("armed_home", None, 10, 1, 100),
        ("triggered", None, 13, 9, 100),
    ],
)
async def test_set_alarm_state_services(
    hass: HomeAssistant,
    zwave_device_id: str,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    alarm_state: str,
    delay: str | None,
    property: int,
    property_key: int,
    value: int,
) -> None:
    """Test event entity default state."""

    device_entry = device_registry.async_get(zwave_device_id)
    assert device_entry
    assert config_entry.entry_id in device_entry.config_entries

    call_service = async_mock_service(hass, "zwave_js", "set_value")

    await hass.services.async_call(
        DOMAIN,
        "update_alarm_state",
        service_data={
            "alarm_state": alarm_state,
            "delay": delay,
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
    assert config_entry.entry_id in device_entry.config_entries

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
    assert config_entry.entry_id in device_entry.config_entries

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
