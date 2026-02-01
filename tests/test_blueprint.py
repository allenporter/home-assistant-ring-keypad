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
KEYPAD_ALARM_AUTOMATION_YAML = pathlib.Path("config/automations/keypad_alarm.yaml")
KEYPAD_INPUT_AUTOMATION_YAML = pathlib.Path("config/automations/keypad_input.yaml")
KEYPAD_MODE_AUTOMATION_YAML = pathlib.Path("config/automations/keypad_mode.yaml")
KEYPAD_ALARM_AUTOMATION_ENTITY = "automation.ring_keypad_alarm"
KEYPAD_INPUT_AUTOMATION_ENTITY = "automation.ring_keypad_input"
KEYPAD_MODE_AUTOMATION_ENTITY = "automation.ring_keypad_mode"
ALARM_CONTROL_PANEL_ENTITY = "alarm_control_panel.security"
CODE = "4444"


@pytest.fixture(name="error_caplog")
def caplog_fixture(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture error logs."""
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture(name="arming_time")
async def mock_arming_time() -> int:
    """Fixture to provide arming time."""
    return 0


@pytest.fixture(name="delay_time")
async def mock_delay_time() -> int:
    """Fixture to provide delay time."""
    return 0


@pytest.fixture(name="alarm_control_panel")
async def mock_alarm_control_panel(
    hass: HomeAssistant, arming_time: int, delay_time: int
) -> MockConfigEntry:
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
                    "arming_time": arming_time,
                    "delay_time": delay_time,
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
    [(True, KEYPAD_ALARM_AUTOMATION_YAML)],
)
async def test_keypad_input(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    automation: Any,
    caplog: pytest.LogCaptureFixture,
    zwave_device_id: str,
) -> None:
    """Test that the keypad button events."""

    assert await async_setup_component(hass, "system_log", {})

    # Verify automation is loaded
    state = hass.states.get(KEYPAD_ALARM_AUTOMATION_ENTITY)
    assert state
    assert state.state == "on"

    # Verify the starting control panel state
    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "disarmed"

    # Device not notified
    set_value = async_mock_service(hass, "zwave_js", "set_value")
    assert not set_value

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert not error_logs

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
    await hass.async_block_till_done()  # Update device

    # Verify the alarm is armed
    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "armed_away"

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert not error_logs

    # Device notified to update its state
    assert len(set_value) == 1
    set_value.clear()

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
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "armed_away"

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 3
    assert "Invalid alarm code" in error_logs[0].message
    caplog.clear()

    # Verify device was not notified
    assert not set_value

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
    await hass.async_block_till_done()  # Update device

    # Device notified to update its state
    assert len(set_value) == 1

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "disarmed"

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 0


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("automation_yaml", [KEYPAD_ALARM_AUTOMATION_YAML])
@pytest.mark.parametrize(
    (
        "alarm_service",
        "service_data",
        "arming_time",
        "delay_time",
        "expected_state",
        "expected_zwave_value",
    ),
    [
        (
            "alarm_arm_home",
            {},
            0,
            0,
            "armed_home",
            {"property": 10, "property_key": 1, "value": 100},
        ),
        (
            "alarm_arm_away",
            {},
            0,
            0,
            "armed_away",
            {"property": 11, "property_key": 1, "value": 100},
        ),
        (
            "alarm_trigger",
            {},
            0,
            0,
            "triggered",
            {"property": 13, "property_key": 9, "value": 100},
        ),
        (
            "alarm_trigger",
            {},
            0,
            60,
            "pending",
            {"property": 17, "property_key": "timeout", "value": "0m45s"},
        ),
        (
            "alarm_arm_away",
            {},
            60,
            0,
            "arming",
            {"property": 18, "property_key": "timeout", "value": "0m50s"},
        ),
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
    expected_state: str,
    expected_zwave_value: dict[str, Any],
) -> None:
    """Test alarm control panel states are passed on to the keypad."""
    # Verify automation is loaded
    state = hass.states.get(KEYPAD_ALARM_AUTOMATION_ENTITY)
    assert state
    assert state.state == "on"

    set_value = async_mock_service(hass, "zwave_js", "set_value")
    assert not set_value

    # Set the alarm and verify the keypad is notified
    await hass.services.async_call(
        "alarm_control_panel",
        alarm_service,
        service_data=service_data,
        target={"entity_id": ALARM_CONTROL_PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == expected_state

    # Verify the command was sent
    assert len(set_value) == 1
    assert set_value[0].data == {
        "command_class": "135",
        "device_id": [zwave_device_id],
        "endpoint": 0,
        **expected_zwave_value,
    }

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 0


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("automation_yaml", [KEYPAD_ALARM_AUTOMATION_YAML])
async def test_disarm(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    automation: Any,
    caplog: pytest.LogCaptureFixture,
    zwave_device_id: str,
) -> None:
    """Test alarm control panel states are passed on to the keypad."""
    # Verify automation is loaded
    state = hass.states.get(KEYPAD_ALARM_AUTOMATION_ENTITY)
    assert state
    assert state.state == "on"

    set_value = async_mock_service(hass, "zwave_js", "set_value")
    assert not set_value

    # Arm the alarm
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        service_data={},
        target={"entity_id": ALARM_CONTROL_PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "armed_away"

    set_value.clear()

    # Disarm the alarm
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        service_data={"code": CODE},
        target={"entity_id": ALARM_CONTROL_PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_CONTROL_PANEL_ENTITY)
    assert state
    assert state.state == "disarmed"

    # Verify the keypad is notified
    assert len(set_value) == 1
    assert set_value[0].data == {
        "command_class": "135",
        "device_id": [zwave_device_id],
        "endpoint": 0,
        "property": 2,
        "property_key": 1,
        "value": 100,
    }

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) == 0
