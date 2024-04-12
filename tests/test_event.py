"""Tests for the Event Ring Keypad platform."""

import yaml

from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry


import pytest


MESSAGE = """
---
domain: zwave_js
node_id: 30
home_id: 3949593794
endpoint: 0
device_id: {device_id}
command_class: 111
command_class_name: Entry Control
event_type: {event_type}
event_type_label: Ignored
data_type: 0
data_type_label: None
event_data: {event_data}
"""


@pytest.fixture(autouse=True)
def mock_setup_integration(config_entry: MockConfigEntry) -> None:
    """Setup the integration"""


async def test_default_state(hass: HomeAssistant) -> None:
    """Test event entity default state."""

    state = hass.states.get("event.device_name_button")
    assert state is not None
    assert state.state == "unknown"


@pytest.mark.parametrize(
    ("event_type", "event_type_name", "entity_event_type", "event_data"),
    [
        (0, "code_started", "pressed", None),
        (1, "code_timeout", "pressed", None),
        (2, "code_entered", "alarm_disarm", "1234"),
        (3, "disarm", "alarm_disarm", None),
        (5, "arm_away", "alarm_arm_away", None),
        (6, "arm_stay", "alarm_arm_home", None),
        (16, "fire", "pressed", None),
        (17, "police", "pressed", None),
        (19, "medical", "pressed", None),
        (25, "code_cancel", "pressed", None),
        (12345, None, None, None),  # Unknown
    ],
)
async def test_event_message(
    hass: HomeAssistant,
    zwave_device_id: str,
    event_type: int,
    event_type_name: str | None,
    entity_event_type: str,
    event_data: str | None,
) -> None:
    """Test event entity published."""

    hass.bus.async_fire(
        "zwave_js_notification",
        yaml.load(
            MESSAGE.format(
                device_id=zwave_device_id,
                event_type=event_type,
                event_data=f'"{event_data}"' if event_data else "null",
            ),
            Loader=yaml.Loader,
        ),
    )
    await hass.async_block_till_done()

    state = hass.states.get("event.device_name_button")
    assert state is not None
    assert state.attributes.get("event_type") == entity_event_type
    assert state.attributes.get("button") == event_type_name
    assert state.attributes.get("code") == event_data


async def test_invalid_device_id(hass: HomeAssistant) -> None:
    """Test event published for a different device id."""

    hass.bus.async_fire(
        "zwave_js_notification",
        yaml.load(
            MESSAGE.format(
                device_id="123456", event_type="code_canceled", event_data="null"
            ),
            Loader=yaml.Loader,
        ),
    )
    await hass.async_block_till_done()

    state = hass.states.get("event.device_name_button")
    assert state is not None
    assert state.state == "unknown"
