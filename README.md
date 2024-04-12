# home-assistant-ring-keypad

A Home Assistant custom component for the ZWave Ring Keypad.

This implements a helper that makes the Ring Keypad Z-Wave device appear
with a couple more user friendly components that a raw Z-Wave device.

## Event Entity

Ring Keypad key-presses are [published as events](https://github.com/ImSorryButWho/HomeAssistantNotes/blob/main/RingKeypadV2.md) on the event. This component adds a [Event entity](https://www.home-assistant.io/integrations/event/)
that can be used to simplify automations rather than relying on
lower level event codes.



This event was generated from entering the code "1234", and pressing the Enter button.  The `event_data` field tells you what code was entered, and the `event_type` tells you which button was pressed.  The following table explains the meanings of the different `event_type` values the keypad can produce:

| `event_type` | Meaning |
| ------------ | ------- |
| `code_started` | User started entering a code |
| `code_timeout` | User entered a code, but didn't press enter (or another button) before the timeout. |
| `code_cancel` | Cancel |
| `code_entered` | User entered a code, and the event also contains a field `code` with the code |
| `disarm` | Disarm |
| `arm_away` | Arm Away |
| `arm_stay` | Arm Stay |
| `fire` | Fire (not sent unless button is held down until all 3 lights go out) |
| `police` | Police (not sent unless button is held down until all 3 lights go out) |
| `medical` | Medical (not sent unless button is held down until all 3 lights go out) |
