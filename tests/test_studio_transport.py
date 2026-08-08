# SPDX-License-Identifier: GPL-3.0-only

import importlib.util
import sys
import types
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "hardware/NovationLaunchpadProMK3StudioDAW/device_LaunchPadProMk3_Studio_DAW.py"
)


class Event:
    def __init__(self, status=0xB0, data1=0, data2=0, sysex=b"", pme_flags=0):
        self.status = status
        self.midiId = status
        self.data1 = data1
        self.data2 = data2
        self.sysex = sysex
        self.pmeFlags = pme_flags
        self.handled = False


class FakeTransport:
    def __init__(self):
        self.playing = False
        self.recording = False
        self.start_calls = 0
        self.stop_calls = 0
        self.global_calls = []

    def isPlaying(self):
        return 1 if self.playing else 0

    def isRecording(self):
        return self.recording

    def start(self):
        self.playing = True
        self.start_calls += 1

    def stop(self):
        self.playing = False
        self.stop_calls += 1

    def globalTransport(self, command, value, pme_flags):
        self.global_calls.append((command, value, pme_flags))
        if command == 10 and value > 0:
            self.playing = not self.playing
        elif command == 11 and value > 0:
            self.playing = False
        elif command == 12 and value > 0:
            self.recording = not self.recording


def load_script():
    sysex_messages = []
    midi_messages = []
    device = types.SimpleNamespace(
        isAssigned=lambda: True,
        midiOutSysex=lambda message: sysex_messages.append(message),
        midiOutMsg=lambda *message: midi_messages.append(message),
    )
    midi = types.SimpleNamespace(
        PM_Playing=1,
        PME_System=0,
        FPT_Play=10,
        FPT_Stop=11,
        FPT_Record=12,
        MIDI_NOTEON=0x90,
        MIDI_NOTEOFF=0x80,
        MIDI_CONTROLCHANGE=0xB0,
        MIDI_BEGINSYSEX=0xF0,
    )
    transport = FakeTransport()
    mixer_state = {"selected": 1}
    armed_tracks = set()
    muted_tracks = set()
    solo_tracks = set()
    track_volumes = {track: 0.5 for track in range(1, 126)}
    mixer = types.SimpleNamespace(
        getTrackCount=lambda: mixer.track_count,
        getTrackColor=lambda track: 0x102030 + track,
        setTrackNumber=lambda track: (mixer.selected.append(track), mixer_state.__setitem__("selected", track)),
        trackNumber=lambda: mixer_state["selected"],
        isTrackArmed=lambda track: track in armed_tracks,
        armTrack=lambda track: armed_tracks.remove(track) if track in armed_tracks else armed_tracks.add(track),
        isTrackMuted=lambda track: track in muted_tracks,
        muteTrack=lambda track: muted_tracks.remove(track) if track in muted_tracks else muted_tracks.add(track),
        isTrackSolo=lambda track: track in solo_tracks,
        soloTrack=lambda track: solo_tracks.remove(track) if track in solo_tracks else solo_tracks.add(track),
        getTrackVolume=lambda track: track_volumes[track],
        setTrackVolume=lambda track, value: track_volumes.__setitem__(track, value),
        track_volumes=track_volumes,
        selected=[],
        track_count=125,
    )
    utils = types.SimpleNamespace(
        ColorToRGB=lambda color: ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF),
    )
    clock = types.SimpleNamespace(monotonic=lambda: 0.0)
    replacements = {
        "device": device,
        "midi": midi,
        "mixer": mixer,
        "transport": transport,
        "utils": utils,
        "time": clock,
    }
    previous = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        spec = importlib.util.spec_from_file_location("studio_midi_test", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module
    return module, transport, mixer, sysex_messages, midi_messages


class StudioTransportTests(unittest.TestCase):
    def test_session_button_always_enters_base_session_view(self):
        module, _, _, _, _ = load_script()
        event = Event(data1=module.SESSION_BUTTON, data2=127)

        module.Controller.on_midi_msg(event)
        self.assertTrue(module.Controller.session_active)

        module.Controller.set_mixer_control_mode('volume')
        module.Controller.on_midi_msg(event)
        self.assertTrue(module.Controller.session_active)
        self.assertFalse(module.Controller.volume_active)

    def test_session_layout_confirmation_preserves_current_mixer_view(self):
        module, _, _, sysex_messages, _ = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        enter = module.build_layout_sysex(module.LAYOUT_SESSION)

        module.Controller.on_midi_in(Event(status=module.midi.MIDI_BEGINSYSEX, sysex=enter))

        self.assertTrue(module.Controller.session_active)
        self.assertTrue(module.Controller.volume_active)
        self.assertIn(module.build_layout_sysex(module.LAYOUT_SESSION), sysex_messages)

    def test_setup_round_trip_restores_volume_view(self):
        module, _, _, sysex_messages, _ = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        sysex_messages.clear()

        module.Controller.on_midi_in(
            Event(
                status=module.midi.MIDI_BEGINSYSEX,
                sysex=module.build_layout_sysex(module.LAYOUT_SETTINGS),
            )
        )
        self.assertTrue(module.Controller.session_active)
        self.assertTrue(module.Controller.volume_active)

        module.Controller.on_midi_in(
            Event(
                status=module.midi.MIDI_BEGINSYSEX,
                sysex=module.build_layout_sysex(1),
            )
        )

        self.assertTrue(module.Controller.session_active)
        self.assertTrue(module.Controller.volume_active)
        self.assertIn(module.SYSEX_DAW_MODE_ON, sysex_messages)
        self.assertTrue(any(message[6] == 1 for message in sysex_messages))
        self.assertNotIn(module.SYSEX_FADER_LAYOUT, sysex_messages)

    def test_leaving_volume_selects_named_hardware_layout(self):
        module, _, _, sysex_messages, midi_messages = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')

        module.Controller.leave_session(module.LAYOUT_NOTE)

        self.assertFalse(module.Controller.session_active)
        self.assertEqual(sysex_messages[-1], module.build_layout_sysex(module.LAYOUT_NOTE))
        bottom_colors = {
            message[2]: message[3]
            for message in midi_messages
            if 1 <= message[2] <= 4
        }
        self.assertEqual(bottom_colors, {control: 0 for control in range(1, 5)})

    def test_hardware_layout_change_clears_mixer_mode_leds(self):
        module, _, _, _, midi_messages = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('solo')
        midi_messages.clear()
        note_layout = module.build_layout_sysex(module.LAYOUT_NOTE)

        module.Controller.on_midi_in(
            Event(status=module.midi.MIDI_BEGINSYSEX, sysex=note_layout)
        )

        colors = {message[2]: message[3] for message in midi_messages}
        self.assertEqual(
            {control: colors[control] for control in range(1, 5)},
            {control: 0 for control in range(1, 5)},
        )

    def test_switching_from_volume_to_solo_survives_session_layout_confirmation(self):
        module, _, _, _, _ = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')

        module.Controller.on_midi_msg(Event(data1=module.SOLO_BUTTON, data2=127))
        confirmation = module.build_layout_sysex(module.LAYOUT_SESSION)
        module.Controller.on_midi_in(
            Event(status=module.midi.MIDI_BEGINSYSEX, sysex=confirmation)
        )

        self.assertTrue(module.Controller.session_active)
        self.assertTrue(module.Controller.solo_active)
        self.assertFalse(module.Controller.volume_active)

    def test_play_toggles_transport_only_in_session(self):
        module, transport, _, _, _ = load_script()
        event = Event(data1=module.PLAY_BUTTON, data2=127)

        module.Controller.on_midi_msg(event)
        self.assertFalse(event.handled)
        self.assertEqual(transport.global_calls, [])

        module.Controller.enter_session()
        module.Controller.on_midi_msg(event)
        self.assertTrue(transport.playing)
        self.assertEqual(transport.global_calls[-1], (module.midi.FPT_Play, 2, 0))
        module.Controller.on_midi_msg(event)
        self.assertFalse(transport.playing)

    def test_stop_clip_always_stops_in_session(self):
        module, transport, _, _, _ = load_script()
        module.Controller.enter_session()
        transport.playing = True
        event = Event(data1=module.STOP_CLIP_BUTTON, data2=127)

        module.Controller.on_midi_msg(event)

        self.assertTrue(event.handled)
        self.assertFalse(transport.playing)
        self.assertEqual(transport.global_calls[-1], (module.midi.FPT_Stop, 2, 0))

    def test_transport_release_is_forwarded_as_button_release(self):
        module, transport, _, _, _ = load_script()
        module.Controller.enter_session()

        module.Controller.on_midi_msg(Event(data1=module.PLAY_BUTTON, data2=0, pme_flags=23))

        self.assertEqual(transport.global_calls[-1], (module.midi.FPT_Play, 0, 23))

    def test_mode_buttons_leave_to_named_hardware_layout(self):
        module, _, _, messages, _ = load_script()
        for button, layout in (
            (module.NOTE_BUTTON, module.LAYOUT_NOTE),
            (module.CHORD_BUTTON, module.LAYOUT_CHORD),
            (module.CUSTOM_BUTTON, module.LAYOUT_CUSTOM),
        ):
            module.Controller.enter_session()
            module.Controller.on_midi_msg(Event(data1=button, data2=127))
            self.assertFalse(module.Controller.session_active)
            self.assertEqual(messages[-1], module.build_layout_sysex(layout, 0))

    def test_function_leds_use_requested_palette_and_device_is_cleared(self):
        module, _, _, _, messages = load_script()

        self.assertEqual(module.PALETTE_FUNCTION, 2)
        self.assertEqual(module.PALETTE_ACTIVE, 90)
        self.assertEqual(module.PALETTE_PLAY_DARK, 22)
        self.assertEqual(module.PALETTE_PLAY_LIGHT, 21)
        self.assertEqual(module.PALETTE_STOP, 6)
        self.assertEqual(module.PALETTE_RECORD_DARK, 6)

        module.Controller.enter_session()

        colors = {message[2]: message[3] for message in messages}
        self.assertEqual(colors[module.SESSION_BUTTON], module.PALETTE_ACTIVE)
        self.assertEqual(colors[module.NOTE_BUTTON], module.PALETTE_FUNCTION)
        self.assertEqual(colors[module.CHORD_BUTTON], module.PALETTE_FUNCTION)
        self.assertEqual(colors[module.CUSTOM_BUTTON], module.PALETTE_FUNCTION)
        self.assertEqual(colors[module.PLAY_BUTTON], module.PALETTE_PLAY_DARK)
        self.assertEqual(colors[module.RECORD_BUTTON], module.PALETTE_RECORD_DARK)
        self.assertEqual(colors[module.STOP_CLIP_BUTTON], module.PALETTE_STOP)
        self.assertEqual(colors[7], module.PALETTE_OFF)
        self.assertEqual(colors[module.PALETTE_LOW_BUTTON], module.PALETTE_FUNCTION)
        self.assertEqual(colors[module.PALETTE_HIGH_BUTTON], module.PALETTE_FUNCTION)

    def test_record_button_toggles_fl_record_and_led(self):
        module, transport, _, _, messages = load_script()
        module.Controller.enter_session()

        event = Event(data1=module.RECORD_BUTTON, data2=127, pme_flags=17)
        module.Controller.on_midi_msg(event)

        self.assertTrue(event.handled)
        self.assertTrue(transport.recording)
        self.assertEqual(transport.global_calls[-1], (module.midi.FPT_Record, 2, 17))
        colors = {message[2]: message[3] for message in messages}
        self.assertEqual(colors[module.RECORD_BUTTON], module.PALETTE_RECORD_LIGHT)
        record_messages = [message for message in messages if message[2] == module.RECORD_BUTTON]
        self.assertEqual(record_messages[-2][1:], (module.LED_CHANNEL_STATIC, module.RECORD_BUTTON, 0))
        self.assertEqual(record_messages[-1][1], module.LED_CHANNEL_FLASH)

    def test_play_uses_flashing_channel_only_while_playing(self):
        module, transport, _, _, messages = load_script()
        module.Controller.enter_session()
        inactive = [message for message in messages if message[2] == module.PLAY_BUTTON][-1]

        transport.playing = True
        module.Controller.send_leds()
        active = [message for message in messages if message[2] == module.PLAY_BUTTON][-1]
        active_messages = [message for message in messages if message[2] == module.PLAY_BUTTON]

        self.assertEqual(inactive[1:], (module.LED_CHANNEL_STATIC, module.PLAY_BUTTON, module.PALETTE_PLAY_DARK))
        self.assertEqual(active_messages[-2][1:], (module.LED_CHANNEL_STATIC, module.PLAY_BUTTON, 0))
        self.assertEqual(active[1:], (module.LED_CHANNEL_FLASH, module.PLAY_BUTTON, module.PALETTE_PLAY_LIGHT))

    def test_low_palette_view_maps_zero_through_63_from_top_left(self):
        module, _, _, _, messages = load_script()
        module.Controller.enter_session()
        messages.clear()

        event = Event(data1=module.PALETTE_LOW_BUTTON, data2=127)
        module.Controller.on_midi_msg(event)

        note_messages = [message for message in messages if message[0] == module.midi.MIDI_NOTEON]
        self.assertTrue(event.handled)
        self.assertEqual(note_messages[0][2:], (81, 0))
        self.assertEqual(note_messages[7][2:], (88, 7))
        self.assertEqual(note_messages[-1][2:], (18, 63))

    def test_high_palette_view_maps_64_through_127_from_top_left(self):
        module, _, _, _, messages = load_script()
        module.Controller.enter_session()
        messages.clear()

        module.Controller.on_midi_msg(Event(data1=module.PALETTE_HIGH_BUTTON, data2=127))

        note_messages = [message for message in messages if message[0] == module.midi.MIDI_NOTEON]
        self.assertEqual(note_messages[0][2:], (81, 64))
        self.assertEqual(note_messages[-1][2:], (18, 127))
        button_colors = {
            message[2]: message[3]
            for message in messages
            if message[0] == module.midi.MIDI_CONTROLCHANGE
        }
        self.assertEqual(button_colors[module.PALETTE_HIGH_BUTTON], module.PALETTE_ACTIVE)
        self.assertEqual(button_colors[module.PALETTE_LOW_BUTTON], module.PALETTE_FUNCTION)

    def test_session_grid_uses_tracks_one_through_64_and_fl_colors(self):
        module, _, mixer, sysex_messages, _ = load_script()

        module.Controller.enter_session()

        grid_message = sysex_messages[-1]
        self.assertEqual(grid_message[:7], bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x03]))
        self.assertEqual(grid_message[7:12], bytes([3, 81, *module.launchpad_rgb(mixer.getTrackColor(1))]))
        self.assertEqual(grid_message[-6:-1], bytes([3, 18, *module.launchpad_rgb(mixer.getTrackColor(64))]))

    def test_grid_pad_selects_matching_mixer_track(self):
        module, _, mixer, _, midi_messages = load_script()
        module.Controller.enter_session()

        event = Event(status=module.midi.MIDI_NOTEON, data1=81, data2=127)
        module.Controller.on_midi_msg(event)
        module.Controller.on_midi_msg(Event(status=module.midi.MIDI_NOTEON, data1=18, data2=127))

        self.assertTrue(event.handled)
        self.assertEqual(mixer.selected, [1, 64])
        self.assertEqual(midi_messages[-1], (module.midi.MIDI_NOTEON, 0, 18, 17))

    def test_releasing_grid_pad_keeps_selected_color(self):
        module, _, _, sysex_messages, midi_messages = load_script()
        module.Controller.enter_session()
        sysex_messages.clear()
        midi_messages.clear()

        event = Event(status=module.midi.MIDI_NOTEOFF, data1=81, data2=0)
        module.Controller.on_midi_msg(event)

        self.assertTrue(event.handled)
        self.assertEqual(sysex_messages, [])
        self.assertEqual(midi_messages, [])

    def test_selecting_new_track_restores_previous_pad_and_keeps_new_pad_lime(self):
        module, _, mixer, sysex_messages, midi_messages = load_script()
        module.Controller.enter_session()
        sysex_messages.clear()
        midi_messages.clear()

        module.Controller.on_midi_msg(Event(status=module.midi.MIDI_NOTEON, data1=82, data2=127))

        expected_rgb = module.launchpad_rgb(mixer.getTrackColor(1))
        self.assertEqual(
            sysex_messages[-1],
            bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x03, 3, 81, *expected_rgb, 0xF7]),
        )
        self.assertEqual(midi_messages[-1], (module.midi.MIDI_NOTEON, 0, 82, 17))

    def test_record_arm_button_toggles_mode_and_led(self):
        module, _, _, _, messages = load_script()
        module.Controller.enter_session()
        times = iter((1.0, 1.1, 2.0, 2.1))
        module.time.monotonic = lambda: next(times)

        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=127))
        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=0))

        self.assertTrue(module.Controller.record_arm_active)
        arm_messages = [message for message in messages if message[2] == module.RECORD_ARM_BUTTON]
        self.assertEqual(arm_messages[-1][3], 13)

        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=127))
        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=0))
        self.assertFalse(module.Controller.record_arm_active)
        arm_messages = [message for message in messages if message[2] == module.RECORD_ARM_BUTTON]
        self.assertEqual(arm_messages[-1][3], module.PALETTE_FUNCTION)

    def test_holding_record_arm_temporarily_opens_mode(self):
        module, _, _, _, _ = load_script()
        module.Controller.enter_session()
        times = iter((1.0, 1.5))
        module.time.monotonic = lambda: next(times)

        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=127))
        self.assertTrue(module.Controller.record_arm_active)

        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=0))
        self.assertFalse(module.Controller.record_arm_active)

    def test_record_arm_mode_toggles_track_arm_without_selecting(self):
        module, _, mixer, _, messages = load_script()
        module.Controller.enter_session()
        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=127))
        mixer.selected.clear()

        module.Controller.on_midi_msg(Event(status=module.midi.MIDI_NOTEON, data1=82, data2=127))

        self.assertTrue(mixer.isTrackArmed(2))
        self.assertEqual(mixer.selected, [])
        self.assertEqual(messages[-1], (module.midi.MIDI_NOTEON, 0, 82, 6))

    def test_mute_mode_toggles_track_mute_with_blue_pad(self):
        module, _, mixer, _, messages = load_script()
        module.Controller.enter_session()
        module.Controller.on_midi_msg(Event(data1=module.MUTE_BUTTON, data2=127))
        mixer.selected.clear()

        module.Controller.on_midi_msg(Event(status=module.midi.MIDI_NOTEON, data1=82, data2=127))

        self.assertTrue(mixer.isTrackMuted(2))
        self.assertEqual(mixer.selected, [])
        self.assertEqual(messages[-1], (module.midi.MIDI_NOTEON, 0, 82, 45))

    def test_solo_mode_toggles_track_solo_with_yellow_pad(self):
        module, _, mixer, _, messages = load_script()
        module.Controller.enter_session()
        module.Controller.on_midi_msg(Event(data1=module.SOLO_BUTTON, data2=127))
        mixer.selected.clear()

        module.Controller.on_midi_msg(Event(status=module.midi.MIDI_NOTEON, data1=82, data2=127))

        self.assertTrue(mixer.isTrackSolo(2))
        self.assertEqual(mixer.selected, [])
        self.assertEqual(messages[-1], (module.midi.MIDI_NOTEON, 0, 82, 13))

    def test_mixer_control_modes_are_exclusive(self):
        module, _, _, _, _ = load_script()
        module.Controller.enter_session()

        module.Controller.on_midi_msg(Event(data1=module.RECORD_ARM_BUTTON, data2=127))
        module.Controller.on_midi_msg(Event(data1=module.MUTE_BUTTON, data2=127))

        self.assertFalse(module.Controller.record_arm_active)
        self.assertTrue(module.Controller.mute_active)
        self.assertFalse(module.Controller.solo_active)

    def test_volume_mode_uses_bank_containing_selected_track(self):
        module, _, mixer, sysex_messages, _ = load_script()
        module.Controller.enter_session()
        mixer.setTrackNumber(10)

        module.Controller.on_midi_msg(Event(data1=module.VOLUME_BUTTON, data2=127))

        self.assertTrue(module.Controller.volume_active)
        self.assertEqual(module.Controller.volume_bank_start, 9)
        self.assertIn(module.SYSEX_FADER_LAYOUT, sysex_messages)

    def test_fader_changes_track_volume_in_current_bank(self):
        module, _, mixer, _, _ = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        module.Controller.volume_bank_start = 9
        module.Controller.on_midi_msg(
            Event(status=module.midi.MIDI_CONTROLCHANGE,
                  data1=module.FADER_FIRST_CC + 2, data2=127)
        )

        self.assertEqual(mixer.track_volumes[11], 1.0)

    def test_volume_bank_buttons_move_eight_tracks(self):
        module, _, _, _, _ = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        module.Controller.on_midi_msg(
            Event(data1=module.BANK_RIGHT_BUTTON, data2=127)
        )

        self.assertEqual(module.Controller.volume_bank_start, 9)

    def test_volume_view_only_lights_existing_faders_and_banks(self):
        module, _, mixer, sysex_messages, midi_messages = load_script()
        mixer.track_count = 10
        mixer.setTrackNumber(10)
        module.Controller.enter_session()
        midi_messages.clear()
        sysex_messages.clear()

        module.Controller.set_mixer_control_mode('volume')

        fader_setup = next(message for message in sysex_messages if message[6] == 1)
        fader_colors = [fader_setup[12 + index * 4] for index in range(module.GRID_SIZE)]
        self.assertEqual(fader_colors, [3, 17, 0, 0, 0, 0, 0, 0])

        colors = {message[2]: message[3] for message in midi_messages}
        self.assertEqual(colors[module.BANK_LEFT_BUTTON], module.PALETTE_FUNCTION)
        self.assertEqual(colors[module.BANK_RIGHT_BUTTON], module.PALETTE_OFF)
        self.assertEqual(
            [colors[module.TRACK_SELECT_FIRST_CC + index] for index in range(module.GRID_SIZE)],
            [1, 17, 0, 0, 0, 0, 0, 0],
        )

    def test_volume_fader_colors_show_mixer_track_states(self):
        module, _, mixer, _, _ = load_script()
        mixer.setTrackNumber(1)
        mixer.armTrack(2)
        mixer.muteTrack(3)
        mixer.armTrack(4)
        mixer.muteTrack(4)

        colors = module.Controller.volume_fader_colors()

        self.assertEqual(colors, [17, 61, 1, 1, 3, 3, 3, 3])

    def test_volume_refresh_updates_colors_without_redefining_fader_bank(self):
        module, _, _, sysex_messages, midi_messages = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        sysex_messages.clear()
        midi_messages.clear()

        module.Controller.on_refresh(0)

        self.assertEqual(sysex_messages, [])
        color_messages = [
            message for message in midi_messages
            if message[1] == module.FADER_COLOR_MIDI_CHANNEL
        ]
        self.assertEqual(len(color_messages), module.GRID_SIZE)

    def test_track_select_chooses_visible_volume_bank(self):
        module, _, _, _, _ = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')

        module.Controller.on_midi_msg(
            Event(data1=module.TRACK_SELECT_FIRST_CC + 3, data2=127)
        )

        self.assertEqual(module.Controller.volume_bank_start, 25)

    def test_leaving_volume_clears_track_select_leds(self):
        module, _, _, _, midi_messages = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        midi_messages.clear()

        module.Controller.set_mixer_control_mode('solo')

        colors = {message[2]: message[3] for message in midi_messages}
        self.assertEqual(
            [colors[module.TRACK_SELECT_FIRST_CC + index] for index in range(module.GRID_SIZE)],
            [0] * module.GRID_SIZE,
        )

    def test_volume_bank_indicator_pages_after_track_64(self):
        module, _, _, _, midi_messages = load_script()
        module.Controller.enter_session()
        module.Controller.set_mixer_control_mode('volume')
        module.Controller.volume_bank_start = 65
        midi_messages.clear()

        module.Controller.send_volume_bank_leds()

        colors = {message[2]: message[3] for message in midi_messages}
        self.assertEqual(colors[module.TRACK_SELECT_FIRST_CC], 17)
        self.assertEqual(colors[module.TRACK_SELECT_FIRST_CC + 7], 1)

    def test_pressing_active_palette_button_returns_to_mixer_grid(self):
        module, _, _, sysex_messages, _ = load_script()
        module.Controller.enter_session()
        module.Controller.on_midi_msg(Event(data1=module.PALETTE_LOW_BUTTON, data2=127))
        sysex_messages.clear()

        module.Controller.on_midi_msg(Event(data1=module.PALETTE_LOW_BUTTON, data2=127))

        self.assertIsNone(module.Controller.palette_page)
        self.assertEqual(sysex_messages[-1][:7], bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x03]))


if __name__ == "__main__":
    unittest.main()
