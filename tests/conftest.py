"""Fixtures for the custom component."""

from collections.abc import Generator
import logging
from unittest.mock import patch

import pytest

from homeassistant.const import Platform, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.helpers import device_registry as dr

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)


from custom_components.ring_keypad.const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

TEST_DOMAIN = "test"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable custom integration."""
    _ = enable_custom_integrations  # unused
    yield


@pytest.fixture(name="platforms")
def mock_platforms() -> list[Platform]:
    """Fixture for platforms loaded by the integration."""
    return [Platform.ALARM_CONTROL_PANEL]


@pytest.fixture(name="setup_integration")
async def mock_setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platforms: list[Platform],
) -> None:
    """Set up the integration."""
    config_entry.add_to_hass(hass)

    with patch(f"custom_components.{DOMAIN}.PLATFORMS", platforms):
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        yield


@pytest.fixture(name="zwave_config_entry")
async def mock_zwave_config_entry(
    hass: HomeAssistant,
) -> MockConfigEntry:
    zwave_config_entry = MockConfigEntry(domain="zwave_js")
    zwave_config_entry.add_to_hass(hass)
    return zwave_config_entry


@pytest.fixture(name="zwave_device_id")
async def mock_zwave_device_id(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    zwave_config_entry: MockConfigEntry,
) -> None:
    device_entry = device_registry.async_get_or_create(
        config_entry_id=zwave_config_entry.entry_id,
        identifiers={("zwave_js", "12:34:56:AB:CD:EF")},
        name="Device name",
    )
    return device_entry.id


@pytest.fixture(name="config_entry")
async def mock_config_entry(
    hass: HomeAssistant, zwave_device_id: str
) -> MockConfigEntry:
    """Fixture to create a configuration entry."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_DEVICE_ID: zwave_device_id,
        },
        title="Device name",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
