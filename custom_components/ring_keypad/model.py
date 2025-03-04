"""Data model related to the Ring Keypad.

The details for the events and commands are described here:
https://github.com/ImSorryButWho/HomeAssistantNotes/blob/main/RingKeypadV2.md
"""

import enum

from homeassistant.components.alarm_control_panel import AlarmControlPanelState

from .const import DEFAULT_DELAY


EVENT_COMMAND_CLASS = "111"
COMMAND_CLASS = "135"
ENDPOINT = 0
MODE_PROPERTY_KEY = 1
DELAY_PROPERTY_KEY = 7
NOTIFICATION_SOUND_PROPERTY_KEY = 9
MAX_VALUE = 100


# Mapping of keypad event name and number to event entity event type
KEYAD_EVENTS = [
    ("code_started", 0, "pressed"),
    ("code_timeout", 1, "pressed"),
    ("code_cancel", 25, "pressed"),
    ("code_entered", 2, "alarm_disarm"),
    ("disarm", 3, "alarm_disarm"),
    ("arm_away", 5, "alarm_arm_away"),
    ("arm_stay", 6, "alarm_arm_home"),
    ("fire", 16, "pressed"),
    ("police", 17, "pressed"),
    ("medical", 19, "pressed"),
]


class Message(enum.IntEnum):
    # Property key 1
    INVALID_CODE = 9
    NEED_BYPASS = 16
    # Modes
    DISARMED = 2
    ARMED_AWAY = 11
    ARMED_HOME = 10
    # Alarms
    GENERIC_ALARM = 12
    BURGLAR_ALARM = 13  # Same as 13
    SMOKE_ALARM = 14
    CO2_ALARM = 15
    MEDICAL_ALARM = 19


class Delay(enum.IntEnum):
    # Property key 7
    ENTRY_DELAY = 17
    EXIT_DELAY = 18


class NotificationSound(enum.IntEnum):
    """Notification sounds."""

    DOUBLE_BEEP = 96
    GUITAR_RIFF = 97
    WIND_CHIME = 98
    BING_BONG = 99
    DOORBELL = 100


# Mapping of Home Assistant entity state to keypad messages
ALARM_STATE = {
    AlarmControlPanelState.ARMED_AWAY: Message.ARMED_AWAY,
    AlarmControlPanelState.ARMED_HOME: Message.ARMED_HOME,
    AlarmControlPanelState.ARMING: Delay.EXIT_DELAY,
    AlarmControlPanelState.DISARMED: Message.DISARMED,
    AlarmControlPanelState.PENDING: Delay.ENTRY_DELAY,
    AlarmControlPanelState.TRIGGERED: Message.BURGLAR_ALARM,
}

CHIME = {
    "invalid_code": Message.INVALID_CODE,
    "need_bypass": Message.NEED_BYPASS,
    "double_beep": NotificationSound.DOUBLE_BEEP,
    "guitar_riff": NotificationSound.GUITAR_RIFF,
    "wind_chime": NotificationSound.WIND_CHIME,
    "bing_bong": NotificationSound.BING_BONG,
    "doorbell": NotificationSound.DOORBELL,
}

ALARM = {
    "generic": Message.GENERIC_ALARM,
    "burglar": Message.BURGLAR_ALARM,
    "smoke": Message.SMOKE_ALARM,
    "co2": Message.CO2_ALARM,
    "medical": Message.MEDICAL_ALARM,
}


def alarm_state_command(
    state: AlarmControlPanelState, delay: int | None
) -> dict[str, str | int]:
    """Return a zwave command for updating the alarm state."""
    if not (message := ALARM_STATE.get(state)):
        raise ValueError(f"Invalid alarm state command: {state}")
    property_key = MODE_PROPERTY_KEY
    value = MAX_VALUE
    if isinstance(message, Delay):
        property_key = 7
        if delay is None:
            value = DEFAULT_DELAY
        else:
            value = delay
    return {
        "command_class": COMMAND_CLASS,
        "endpoint": ENDPOINT,
        "property": int(message),
        "property_key": property_key,
        "value": value,
    }


def alarm_command(alarm: str) -> dict[str, str | int]:
    """Return a zwave command for sounding an alarm command."""
    if not (property := ALARM.get(alarm)):
        raise ValueError(f"Invalid chime command: {alarm}")
    return {
        "command_class": COMMAND_CLASS,
        "endpoint": ENDPOINT,
        "property": int(property),
        "property_key": MODE_PROPERTY_KEY,
        "value": MAX_VALUE,
    }


def chime_command(chime: str) -> dict[str, str | int]:
    """Return a zwave command for sending a chime."""
    if not (message := CHIME.get(chime)):
        raise ValueError(f"Invalid chime command: {chime}")
    if isinstance(message, NotificationSound):
        property_key = NOTIFICATION_SOUND_PROPERTY_KEY
    else:
        property_key = MODE_PROPERTY_KEY
    return {
        "command_class": COMMAND_CLASS,
        "endpoint": ENDPOINT,
        "property": int(message),
        "property_key": property_key,
        "value": MAX_VALUE,
    }
