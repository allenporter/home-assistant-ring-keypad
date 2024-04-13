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
| `alarm_arm_home` | `button: arm_stay`                                            | Arm Stay                                                                            |
| `pressed`        | `button: code_started`                                        | User started entering a code                                                        |
| `pressed`        | `button: code_timeout`                                        | User entered a code, but didn't press enter (or another button) before the timeout. |
| `pressed`        | `button: code_cancel`                                         | Cancel                                                                              |
| `pressed`        | `button: fire`                                                | Fire (not sent unless button is held down until all 3 lights go out)                |
| `pressed`        | `button: police`                                              | Police (not sent unless button is held down until all 3 lights go out)              |
| `pressed`        | `button: medical`                                             | Medical (not sent unless button is held down until all 3 lights go out)             |

## Services

### Update Alarm State

Sets the state of the alarm control panel.

```
- service: ring_keypad.update_alarm_state
  target:
    device_id: < device id >
  data:
    alarm_state: armed_away
```

| `alarm_state` | Description |
| ---------- | ----------- |
| `disarmed` | Disarmed.  Keypad says "Disarmed," disarmed light lights up on motion. |
| `armed_home` | Armed Home.  Keypad says "Home and armed," armed stay light lights up on motion. |
| `armed_away` | Armed Away.  Keypad says "Away and armed," armed away light lights up on motion. |
| `arming` |  Exit delay, about to arm. Keypad says "Exit delay started." Plays sound, speeding up near end of specified duration. Bar shows countup. The delay is currently hard coded to 45 seconds. |
| `pending` | Pending, about to trigger. Keypad says "Entry delay started." Plays sound, speeding up near end of specified duration. The delay is currently hard coded to 30 seconds. |
| `triggered` | Trigger the alarm. This is equivalent to calling the Alarm service with `burglar`. |


### Alarm

The Alarm service will sound an alarm from the Ring Keypad.

```
- service: ring_keypad.alarm
  target:
    device_id: < device id >
  data:
    alarm: burglar
```

| `alarm` | Description |
| ----- | ----------- |
| `generic` | Generic alarm.  Plays alarm, flashes light until another mode is selected. |
| `burglar` | Burglar alarm.  Identical to generic.  |
| `smoke` | Smoke alarm.  Plays smoke alarm, flashes light until another mode is selected.|
| `co2` | Carbon monoxide alarm.  Plays intermittent beeping alarm, flashes light until another mode is selected.  |
| `medical` |  Medical alarm.  Medical button lights, bar flashes.  No alarm sound plays. |


### Chime

The Chime service will send a message to the Ring Keypad to play the
specified chime sound.

```
- service: ring_keypad.chime
  target:
    device_id: XXXXX
  data:
    chime: double_beep
```

| `chime` | Description |
| ----- | ----------- |
| `double_beep` | Electronic double beep  |
| `guitar_riff` | Guitar riff  |
| `wind_chime` | Wind chimes |
| `bing_bong` | Echoey Bing Bong |
| `doorbell` | Ring doorbell chime  |
