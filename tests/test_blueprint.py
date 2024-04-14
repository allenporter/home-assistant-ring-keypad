"""Tests for a Ring Keypad blueprint."""

import pathlib
import logging
from typing import Any
from collections.abc import Mapping
from unittest.mock import patch

import pytest
import yaml

from homeassistant.core import HomeAssistant, Event
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_mock_service,
)


_LOGGER = logging.getLogger(__name__)

CONFIG_DIR = pathlib.Path(__file__).parent.parent / "config" / "blueprints"
KEYPAD_INPUT_AUTOMATION_YAML = pathlib.Path("config/automations/keypad_input.yaml")
KEYPAD_MODE_AUTOMATION_YAML = pathlib.Path("config/automations/keypad_mode.yaml")
KEYPAD_INPUT_AUTOMATION_ENTITY = "automation.ring_keypad_input"
KEYPAD_MODE_AUTOMATION_ENTITY = "automation.ring_keypad_mode"
ALARM_CONTROL_PANEL_ENTITY = "alarm_control_panel.security"
CODE = "4444"

@pytest.fixture(name="error_caplog")
def caplog_fixture(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture error logs."""
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture(name="alarm_control_panel")
async def mock_alarm_control_panel(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(
        hass,
        "alarm_control_panel",
        {
            "alarm_control_panel": [
                {
                    "platform": "manual",
                    "name": "security",
                    "code": CODE,
                    "code_arm_required": False,
                    # Simplify testing
                    "arming_time": 0,
                    "delay_time": 0,
                }
            ]
        },
    )


@pytest.fixture(name="automation")
async def mock_automation(
    hass: HomeAssistant,
    # Load dependencies first
    config_entry: MockConfigEntry,
    alarm_control_panel: Any,
    automation_yaml: pathlib.Path,
    zwave_device_id: str,
) -> None:
    with automation_yaml.open("r") as fd:
        content = fd.read()
        content = content.replace("DEVICE_ID", zwave_device_id)
        config = yaml.load(content, Loader=yaml.Loader)

    with patch(
        "homeassistant.components.blueprint.models.BLUEPRINT_FOLDER",
        CONFIG_DIR,
    ):
        assert await async_setup_component(hass, "automation", {"automation": config})
        await hass.async_block_till_done()
        await hass.async_block_till_done()


@pytest.fixture
def events(hass: HomeAssistant) -> list[Event[Mapping[str, Any]]]:
    """Fixture that catches notify events."""
    return async_capture_events(hass, "notify")


@pytest.mark.parametrize(
    ("expected_lingering_timers", "automation_yaml"),
    [(True, KEYPAD_INPUT_AUTOMATION_YAML)],
)
async def test_keypad_input(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    automation: Any,
    caplog: pytest.LogCaptureFixture,
    zwave_device_id: str,
) -> None:
    """Test that the keypad button events."""
    # Verify automation is loaded
    state = hass.states.get(KEYPAD_INPUT_AUTOMATION_ENTITY)
    assert state
    assert state.state == "on"

    # Verify the starting control panel state
    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "disarmed"

    # Press a button on the control panel and it should update the alarm panel
    # entity. Test end to end with a Z-wave event.
    hass.bus.async_fire(
        "zwave_js_notification",
        {
            "domain": "zwave_js",
            "device_id": zwave_device_id,
            "command_class": 111,
            "event_type": 5,  # Arm Away
        },
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Verify the alarm is armed
    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "armed_away"

    # Disarm the alarm, but with an invalid code..
    hass.bus.async_fire(
        "zwave_js_notification",
        {
            "domain": "zwave_js",
            "device_id": zwave_device_id,
            "command_class": 111,
            "event_type": 3,  # Disarm
            "event_data": 4321,
        },
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "armed_away"

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 1
    assert "Invalid alarm code" in error_logs[0].message
    caplog.clear()

    # Enter the code correctly
    hass.bus.async_fire(
        "zwave_js_notification",
        {
            "domain": "zwave_js",
            "device_id": zwave_device_id,
            "command_class": 111,
            "event_type": 3,  # Disarm
            "event_data": int(CODE),
        },
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "disarmed"

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 0


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("automation_yaml", [KEYPAD_MODE_AUTOMATION_YAML])
@pytest.mark.parametrize(
    ("alarm_service", "service_data", "expected_property"),
    [
        ("alarm_arm_home", {}, 10),
        ("alarm_arm_away", {}, 11),
        ("alarm_trigger", {}, 13),
    ],
)
async def test_keypad_mode(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    automation: Any,
    caplog: pytest.LogCaptureFixture,
    zwave_device_id: str,
    alarm_service: str,
    service_data: dict[str, Any],
    expected_property: str,
) -> None:
    """Test alarm control panel states are passed on to the keypad."""
    # Verify automation is loaded
    state = hass.states.get(KEYPAD_MODE_AUTOMATION_ENTITY)
    assert state
    assert state.state == "on"

    set_value = async_mock_service(hass, "zwave_js", "set_value")
    assert not set_value

    # Set the alarm to armed and verify the keypad is notified
    await hass.services.async_call(
        "alarm_control_panel",
        alarm_service,
        service_data=service_data,
        target={"entity_id": ALARM_CONTROL_PANEL_ENTITY},
        blocking=True
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    assert len(set_value) == 1

    # Verify the alarm was armed
    assert len(set_value) == 1
    assert set_value[0].data == {
        "command_class": "135",
        "device_id": [ zwave_device_id ],
        "endpoint": 0,
        "property": expected_property,
        "property_key": 1,
        "value": 100,
    }

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 0
