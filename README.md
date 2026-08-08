# Launchpad Pro MK3 Studio controls for FL Studio

An independent FL Studio MIDI-script integration for the Novation Launchpad Pro MK3, focused on recording and mixing in a studio rather than live performance.

This project is not affiliated with or endorsed by Image-Line, Novation, or Focusrite. Product names are used only to describe compatibility.

## Design

The Launchpad's USB interfaces have separate responsibilities:

- `LPProMK3 DAW` owns Session Mode, transport, mixer controls, LEDs, and native DAW faders.
- `LPProMK3 MIDI` passes musical MIDI from Note, Chord, Custom, and the hardware sequencer through to FL Studio.

The scripts are independent. They do not use `receiveFrom`, cross-script dispatch, background threads, or external runtime dependencies.

## Features

Session always opens the 8×8 mixer overview:

- pads represent FL Studio Mixer tracks 1–64 using their track colours;
- pressing a pad selects its Mixer track;
- Record Arm, Mute, and Solo provide latched or momentary status views;
- Volume opens eight native vertical DAW faders;
- left and right move the Volume bank by eight Mixer tracks;
- Play, Record, and Stop Clip control FL Studio transport;
- Note, Chord, and Custom return to the matching hardware-native layout.

The hardware's Note, Chord, Custom, Sequencer, Projects, and Setup features remain firmware-native.

## Installation

Copy these folders into FL Studio's user hardware-script directory:

```text
hardware/NovationLaunchpadProMK3StudioMidi
hardware/NovationLaunchpadProMK3StudioDAW
```

Assign the controller types in FL Studio MIDI Settings:

| Launchpad interface | Controller type |
| --- | --- |
| `LPProMK3 MIDI` | `NovationLaunchpadProMK3StudioMidi` |
| `LPProMK3 DAW` | `NovationLaunchpadProMK3StudioDAW` |

Enable the matching input and output for each interface. Do not interchange the MIDI and DAW controller types.

After changing script metadata or controller assignments, restart FL Studio. For ordinary DAW-script code changes, use **View → Script output → Reload**.

## Controls in Session Mode

| Control | Function |
| --- | --- |
| Session | Return to the mixer overview |
| Play | FL Studio Play/Pause |
| Record | FL Studio global Record |
| Stop Clip | FL Studio global Stop |
| Record Arm | Toggle or temporarily show Mixer recording-arm states |
| Mute | Toggle or temporarily show Mixer mute states |
| Solo | Toggle or temporarily show Mixer solo states |
| Volume | Toggle or temporarily show eight native DAW volume faders |
| Left / Right | Previous / next eight-track Volume bank |
| Note / Chord / Custom | Leave Session for the named hardware layout |

A short press locks a mixer view. Holding Record Arm, Mute, Solo, or Volume for at least 0.35 seconds makes the view temporary until release.

## Development

Run the isolated Python tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The tests use local stubs for FL Studio's Python modules and do not require FL Studio.

## Protocol references

The implementation uses public device and scripting interfaces:

- [Novation Launchpad Pro MK3 downloads and Programmer's Reference Guide](https://downloads.novationmusic.com/novation/launchpad-mk3/launchpad-pro-mk3-0)
- [FL Studio MIDI scripting API](https://www.image-line.com/fl-studio-learning-content/fl-studio-online-manual/html/midi_scripting.htm)

No vendor documentation, firmware, artwork, or third-party source code is included in this repository.

## License

This project is licensed under the [GNU General Public License, version 3](LICENSE) (`GPL-3.0-only`).
