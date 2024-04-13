# home-assistant-ring-keypad

A Home Assistant custom component for the ZWave Ring Keypad.

This implements a helper that makes the Ring Keypad Z-Wave device appear
with a couple more user friendly components that a raw Z-Wave device. The Ring
Keypad device does not expose the current state over Z-Wave and therefore it
must always be used as a follower, where the state is another system.

## Event Entity

Ring Keypad key-presses are typically published as Z-Wave [events](https://github.com/ImSorryButWho/HomeAssistantNotes/blob/main/RingKeypadV2.md). This component adds a [Event entity](https://www.home-assistant.io/integrations/event/)
to make these more user friendly in the UI and automations. The idea here is to
translate the more complex events into simpler events that can be bound to
an [Alarm Control Panel](https://www.home-assistant.io/integrations/alarm_control_panel/)
entity services.

The Event entity has an event type either associated with a specific Home Assistant
alarm state, or a generic button press. There is additional detail about which
button was pressed in the `button` attributes or details about the alarm code
entered when disarming in the `code` attributes.

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

This component also exposes additional services that can be used to update the
current state of the Ring Keypad. The Keypad does not expose its current state
to Home Assistant, however, so it

### Update Alarm State

Sets the state of the Ring Keypad from the current state of an [Alarm Control Panel](https://www.home-assistant.io/integrations/alarm_control_panel/).

The service allows specifying a delay for the `arming` and `pending` states
which are used for the countdown announcements. Any delay is just for the
anonuncement, and must be kept in sync with the actual alarm control panel
behavior. Keypad itself will not transition to an amrmed or triggered state
itself.

```
- service: ring_keypad.update_alarm_state
  target:
    device_id: < device id >
  data:
    alarm_state: armed_away
    delay: 60  # For `arming` and `pending`
```

| `alarm_state` | Description                                                                                                                                                                  |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `disarmed`    | Disarmed. Keypad says "Disarmed," disarmed light lights up on motion.                                                                                                        |
| `armed_home`  | Armed Home. Keypad says "Home and armed," armed stay light lights up on motion.                                                                                              |
| `armed_away`  | Armed Away. Keypad says "Away and armed," armed away light lights up on motion.                                                                                              |
| `arming`      | Exit delay, about to arm. Keypad says "Exit delay started." Plays sound, speeding up near end of specified duration. Bar shows countup. The `delay` sets the delay duration. |
| `pending`     | Pending, about to trigger. Keypad says "Entry delay started." Plays sound, speeding up near end of specified duration. The `delay` sets the delay duration.                  |
| `triggered`   | Trigger the alarm. This is equivalent to calling the Alarm service with `burglar`.                                                                                           |

### Alarm

The Alarm service will sound an alarm from the Ring Keypad.

```
- service: ring_keypad.alarm
  target:
    device_id: < device id >
  data:
    alarm: burglar
```

| `alarm`   | Description                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------ |
| `generic` | Generic alarm. Plays alarm, flashes light until another mode is selected.                              |
| `burglar` | Burglar alarm. Identical to generic.                                                                   |
| `smoke`   | Smoke alarm. Plays smoke alarm, flashes light until another mode is selected.                          |
| `co2`     | Carbon monoxide alarm. Plays intermittent beeping alarm, flashes light until another mode is selected. |
| `medical` | Medical alarm. Medical button lights, bar flashes. No alarm sound plays.                               |

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

| `chime`       | Description            |
| ------------- | ---------------------- |
| `double_beep` | Electronic double beep |
| `guitar_riff` | Guitar riff            |
| `wind_chime`  | Wind chimes            |
| `bing_bong`   | Echoey Bing Bong       |
| `doorbell`    | Ring doorbell chime    |
