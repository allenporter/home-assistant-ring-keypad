"""Data model related to the Ring Keypad.

The details for the events and commands are described here:
https://github.com/ImSorryButWho/HomeAssistantNotes/blob/main/RingKeypadV2.md
"""

#

import enum
from dataclasses import dataclass
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)


EVENT_COMMAND_CLASS = "111"
COMMAND_CLASS = "135"
ENDPOINT = 0


class KeypadEvent(enum.IntEnum):
    """Events from the user interacting with the keypad."""

    # Keypad code detailed events
    CODE_STARTED = 0
    CODE_TIMEOUT = 1
    CODE_CANCEL = 25

    CODE_ENTERED = 2  # Event also contains `trigger.event.data.event_data``

    # Mode buttons
    DISARM = 3
    ARM_AWAY = 5
    ARM_HOME = 6

    FIRE = 16
    POLICE = 17
    MEDICAL = 19


# @dataclass
# class Command:
#     property: int
#     property_key: int
#     value: int


class Messages(enum.IntEnum):
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


class Delays(enum.IntEnum):
    # Property key 7
    ENTRY_DELAY = 17
    EXIT_DELAY = 18


class Sound(enum.IntEnum):
    # Property key 9
    ELECTRONIC_DOUBLE_BEEP = 96
    GUITAR_RIFF = 97
    WIND_CHIME = 98
    BING_BONG = 99
    DOORBELL = 100


ALARM_STATE = {
    STATE_ALARM_ARMED_AWAY: Messages.ARMED_AWAY,
    STATE_ALARM_ARMED_HOME: Messages.ARMED_HOME,
    STATE_ALARM_ARMING: Delays.EXIT_DELAY,
    STATE_ALARM_DISARMED: Messages.DISARMED,
    STATE_ALARM_PENDING: Delays.ENTRY_DELAY,
    STATE_ALARM_TRIGGERED: Messages.BURGLAR_ALARM,
}


# def notification_command(status: Notification) -> Command:
#     """Notification."""
#     return {
#         "command_class": COMMAND_CLASS,
#         "endpoint": ENDPOINT,
#         "property": int(status),
#         "property_key": 1,
#         "value": 100,
#     }
