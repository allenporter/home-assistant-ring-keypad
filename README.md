# home-assistant-ring-keypad

A Home Assistant custom component for the ZWave Ring Keypad.

This implements a helper that makes the Ring Keypad Z-Wave device appear
with a couple more user friendly components that a raw Z-Wave device.

## Event Entity

Ring Keypad key-presses are [published as events](https://github.com/ImSorryButWho/HomeAssistantNotes/blob/main/RingKeypadV2.md) on the event. This component adds a [Event entity](https://www.home-assistant.io/integrations/event/)
that can be used to simplify automations rather than relying on
lower level event codes.

The idea here is to translate the more complex events into simpler events
that can be bound to alarm control panel services.

Below are the attributes for the event entity and how they relate to the buttons
on the keypad.

| `event_type`     | Additional attributes                                         | Meaning                                                                             |
| ---------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `alarm_disarm`   | `button: disarm` or `button: code_entered` and `code: <code>` | Diarm button or user entered a code to disarm                                       |
| `alarm_arm_away` | `button: arm_away`                                            | Arm Away                                                                            |
| `alarm_arm_stay` | `button: arm_stay`                                            | Arm Stay                                                                            |
| `pressed`        | `button: code_started`                                        | User started entering a code                                                        |
| `pressed`        | `button: code_timeout`                                        | User entered a code, but didn't press enter (or another button) before the timeout. |
| `pressed`        | `button: code_cancel`                                         | Cancel                                                                              |
| `pressed`        | `button: fire`                                                | Fire (not sent unless button is held down until all 3 lights go out)                |
| `pressed`        | `button: police`                                              | Police (not sent unless button is held down until all 3 lights go out)              |
| `pressed`        | `button: medical`                                             | Medical (not sent unless button is held down until all 3 lights go out)             |
