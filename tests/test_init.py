"""Tests for the Ring Keypad component."""

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from pytest_homeassistant_custom_component.common import MockConfigEntry


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
