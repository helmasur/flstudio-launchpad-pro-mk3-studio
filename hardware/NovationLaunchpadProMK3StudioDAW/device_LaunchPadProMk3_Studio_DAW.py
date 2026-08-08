# name=NovationLaunchpadProMK3StudioDAW
# url=
# SPDX-License-Identifier: GPL-3.0-only

import device
import midi
import mixer
import time
import transport
import utils


SESSION_BUTTON = 93
NOTE_BUTTON = 94
CHORD_BUTTON = 95
CUSTOM_BUTTON = 96
PLAY_BUTTON = 20
RECORD_BUTTON = 10
RECORD_ARM_BUTTON = 1
MUTE_BUTTON = 2
SOLO_BUTTON = 3
VOLUME_BUTTON = 4
STOP_CLIP_BUTTON = 8
BANK_LEFT_BUTTON = 91
BANK_RIGHT_BUTTON = 92
FADER_FIRST_CC = 21
PALETTE_LOW_BUTTON = 29
PALETTE_HIGH_BUTTON = 19

LAYOUT_SESSION = 0
LAYOUT_CHORD = 2
LAYOUT_CUSTOM = 3
LAYOUT_NOTE = 4

SYSEX_DAW_MODE_ON = bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x10, 0x01, 0xF7])
SYSEX_DAW_MODE_OFF = bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x10, 0x00, 0xF7])
SYSEX_FADER_LAYOUT = bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E,
                            0x00, 0x01, 0x00, 0x00, 0xF7])
FADER_MIDI_CHANNEL = 4

PALETTE_OFF = 0
PALETTE_FUNCTION = 2
PALETTE_ACTIVE = 90
PALETTE_STOP = 6
PALETTE_PLAY_LIGHT = 21
PALETTE_PLAY_DARK = 22
PALETTE_RECORD_LIGHT = 5
PALETTE_RECORD_DARK = 6
PALETTE_PAD_PRESSED = 3
PALETTE_RECORD_ARM_ACTIVE = 13
PALETTE_TRACK_ARMED = 6
PALETTE_TRACK_MUTED = 45
PALETTE_TRACK_SOLO = 13
PALETTE_FADER = 45
LED_CHANNEL_STATIC = 0
LED_CHANNEL_FLASH = 1
MOMENTARY_HOLD_SECONDS = 0.35

GRID_SIZE = 8
FIRST_MIXER_TRACK = 1


def grid_note(row_from_top, column):
    return (GRID_SIZE - row_from_top) * 10 + column + 1


def grid_track(note):
    row_from_bottom, column = divmod(note, 10)
    if not 1 <= row_from_bottom <= GRID_SIZE or not 1 <= column <= GRID_SIZE:
        return None
    row_from_top = GRID_SIZE - row_from_bottom
    return FIRST_MIXER_TRACK + row_from_top * GRID_SIZE + column - 1


def launchpad_rgb(color):
    red, green, blue = utils.ColorToRGB(color)

    def scale(component):
        normalized = component / 255
        return min(round(normalized * normalized * normalized * 255 * 0.9), 63)

    return scale(red), scale(green), scale(blue)


def build_layout_sysex(layout, page=0):
    return bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x00, layout, page, 0x00, 0xF7])


def build_volume_faders(color):
    message = bytearray([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x01, 0, 0])
    for index in range(GRID_SIZE):
        message.extend([index, 0, FADER_FIRST_CC + index, color])
    message.append(0xF7)
    return bytes(message)


class StudioController:
    def __init__(self):
        self.session_active = False
        self.last_layout = LAYOUT_NOTE
        self.last_layout_page = 0
        self.palette_page = None
        self.record_arm_active = False
        self.mute_active = False
        self.solo_active = False
        self.volume_active = False
        self.volume_bank_start = FIRST_MIXER_TRACK
        self.mode_press_time = None
        self.mode_was_active = False

    def send_leds(self):
        if not self.session_active or not device.isAssigned():
            return

        play_color = PALETTE_PLAY_LIGHT if transport.isPlaying() == midi.PM_Playing else PALETTE_PLAY_DARK
        record_color = PALETTE_RECORD_LIGHT if transport.isRecording() else PALETTE_RECORD_DARK
        colors = {
            SESSION_BUTTON: (PALETTE_ACTIVE, LED_CHANNEL_STATIC),
            NOTE_BUTTON: (PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            CHORD_BUTTON: (PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            CUSTOM_BUTTON: (PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            PLAY_BUTTON: (play_color, LED_CHANNEL_FLASH if transport.isPlaying() == midi.PM_Playing else LED_CHANNEL_STATIC),
            RECORD_BUTTON: (record_color, LED_CHANNEL_FLASH if transport.isRecording() else LED_CHANNEL_STATIC),
            RECORD_ARM_BUTTON: (PALETTE_RECORD_ARM_ACTIVE if self.record_arm_active else PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            MUTE_BUTTON: (PALETTE_RECORD_ARM_ACTIVE if self.mute_active else PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            SOLO_BUTTON: (PALETTE_RECORD_ARM_ACTIVE if self.solo_active else PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            VOLUME_BUTTON: (PALETTE_RECORD_ARM_ACTIVE if self.volume_active else PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            STOP_CLIP_BUTTON: (PALETTE_STOP, LED_CHANNEL_STATIC),
            7: (PALETTE_OFF, LED_CHANNEL_STATIC),  # Device has no function in the transport MVP.
            PALETTE_LOW_BUTTON: (PALETTE_ACTIVE if self.palette_page == 0 else PALETTE_FUNCTION, LED_CHANNEL_STATIC),
            PALETTE_HIGH_BUTTON: (PALETTE_ACTIVE if self.palette_page == 1 else PALETTE_FUNCTION, LED_CHANNEL_STATIC),
        }
        for led_index, (palette_color, midi_channel) in colors.items():
            if midi_channel == LED_CHANNEL_FLASH:
                device.midiOutMsg(midi.MIDI_CONTROLCHANGE, LED_CHANNEL_STATIC,
                                  led_index, PALETTE_OFF)
            device.midiOutMsg(midi.MIDI_CONTROLCHANGE, midi_channel, led_index, palette_color)

    def send_palette_grid(self, page):
        first_color = page * 64
        for row_from_top in range(8):
            for column in range(8):
                note = grid_note(row_from_top, column)
                color = first_color + row_from_top * 8 + column
                device.midiOutMsg(midi.MIDI_NOTEON, 0, note, color)

    def clear_grid(self):
        for row_from_top in range(8):
            for column in range(8):
                note = grid_note(row_from_top, column)
                device.midiOutMsg(midi.MIDI_NOTEON, 0, note, PALETTE_OFF)

    def clear_mixer_mode_leds(self):
        for control in (RECORD_ARM_BUTTON, MUTE_BUTTON, SOLO_BUTTON, VOLUME_BUTTON):
            device.midiOutMsg(midi.MIDI_CONTROLCHANGE, LED_CHANNEL_STATIC,
                              control, PALETTE_OFF)

    def send_mixer_grid(self):
        if not self.session_active or self.palette_page is not None or not device.isAssigned():
            return

        track_count = mixer.getTrackCount()
        message = bytearray([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x03])
        for row_from_top in range(GRID_SIZE):
            for column in range(GRID_SIZE):
                track = FIRST_MIXER_TRACK + row_from_top * GRID_SIZE + column
                color = mixer.getTrackColor(track) if track <= track_count else 0
                message.extend([3, grid_note(row_from_top, column), *launchpad_rgb(color)])
        message.append(0xF7)
        device.midiOutSysex(bytes(message))

        if self.record_arm_active:
            for track in range(FIRST_MIXER_TRACK, min(track_count, 64) + 1):
                if mixer.isTrackArmed(track):
                    device.midiOutMsg(midi.MIDI_NOTEON, 0,
                                      self.note_for_track(track), PALETTE_TRACK_ARMED)
        elif self.mute_active:
            for track in range(FIRST_MIXER_TRACK, min(track_count, 64) + 1):
                if mixer.isTrackMuted(track):
                    device.midiOutMsg(midi.MIDI_NOTEON, 0,
                                      self.note_for_track(track), PALETTE_TRACK_MUTED)
        elif self.solo_active:
            for track in range(FIRST_MIXER_TRACK, min(track_count, 64) + 1):
                if mixer.isTrackSolo(track):
                    device.midiOutMsg(midi.MIDI_NOTEON, 0,
                                      self.note_for_track(track), PALETTE_TRACK_SOLO)
        else:
            selected_track = mixer.trackNumber()
            selected_note = self.note_for_track(selected_track)
            if selected_note is not None:
                device.midiOutMsg(midi.MIDI_NOTEON, 0, selected_note, PALETTE_PAD_PRESSED)

    @staticmethod
    def note_for_track(track):
        offset = track - FIRST_MIXER_TRACK
        if not 0 <= offset < GRID_SIZE * GRID_SIZE:
            return None
        row_from_top, column = divmod(offset, GRID_SIZE)
        return grid_note(row_from_top, column)

    def restore_mixer_pad(self, note, track):
        color = mixer.getTrackColor(track)
        red, green, blue = launchpad_rgb(color)
        message = bytes([0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x03,
                         3, note, red, green, blue, 0xF7])
        device.midiOutSysex(message)

    def show_palette_page(self, page):
        if self.palette_page == page:
            self.palette_page = None
            self.send_mixer_grid()
        else:
            self.palette_page = page
            self.send_palette_grid(page)
        self.send_leds()

    def set_mixer_control_mode(self, mode):
        was_volume_active = self.volume_active
        self.record_arm_active = mode == 'record_arm'
        self.mute_active = mode == 'mute'
        self.solo_active = mode == 'solo'
        self.volume_active = mode == 'volume'
        self.palette_page = None
        if self.volume_active:
            selected_track = mixer.trackNumber()
            if not was_volume_active and selected_track >= FIRST_MIXER_TRACK:
                self.volume_bank_start = ((selected_track - 1) // GRID_SIZE) * GRID_SIZE + 1
            self.send_volume_view()
        else:
            if was_volume_active and device.isAssigned():
                device.midiOutSysex(build_layout_sysex(LAYOUT_SESSION))
            self.send_mixer_grid()
        self.send_leds()

    def handle_mixer_mode_button(self, data2, mode):
        active_attribute = mode + '_active'
        if data2 > 0:
            self.mode_press_time = time.monotonic()
            self.mode_was_active = getattr(self, active_attribute)
            if not self.mode_was_active:
                self.set_mixer_control_mode(mode)
            return

        if self.mode_press_time is None:
            return
        held_seconds = time.monotonic() - self.mode_press_time
        if held_seconds >= MOMENTARY_HOLD_SECONDS:
            target_state = self.mode_was_active
        else:
            target_state = not self.mode_was_active
        self.mode_press_time = None
        current_state = getattr(self, active_attribute)
        if current_state != target_state:
            self.set_mixer_control_mode(mode if target_state else None)

    def send_volume_view(self):
        if not self.session_active or not self.volume_active or not device.isAssigned():
            return
        device.midiOutSysex(SYSEX_DAW_MODE_ON)
        device.midiOutSysex(build_volume_faders(PALETTE_FADER))
        device.midiOutSysex(SYSEX_FADER_LAYOUT)
        self.send_volume_values()

    def send_volume_values(self):
        track_count = mixer.getTrackCount()
        for index in range(GRID_SIZE):
            track = self.volume_bank_start + index
            value = round(mixer.getTrackVolume(track) * 127) if track <= track_count else 0
            device.midiOutMsg(midi.MIDI_CONTROLCHANGE, FADER_MIDI_CHANNEL,
                              FADER_FIRST_CC + index, value)

    def change_volume_bank(self, direction):
        max_start = max(1, ((mixer.getTrackCount() - 1) // GRID_SIZE) * GRID_SIZE + 1)
        self.volume_bank_start = min(max(self.volume_bank_start + direction * GRID_SIZE, 1), max_start)
        self.send_volume_values()

    def handle_fader_value(self, fader_index, value):
        if not self.volume_active or not 0 <= fader_index < GRID_SIZE:
            return
        track = self.volume_bank_start + fader_index
        if track <= mixer.getTrackCount():
            mixer.setTrackVolume(track, value / 127)

    def enter_session(self, force=False, select_layout=True):
        if self.session_active and not force:
            return
        self.session_active = True
        self.palette_page = None
        self.record_arm_active = False
        self.mute_active = False
        self.solo_active = False
        self.volume_active = False
        self.mode_press_time = None
        if device.isAssigned():
            device.midiOutSysex(SYSEX_DAW_MODE_ON)
            if select_layout:
                device.midiOutSysex(build_layout_sysex(LAYOUT_SESSION))
            self.send_mixer_grid()
            self.send_leds()

    def leave_session(self, layout=None, page=0):
        if layout is not None:
            self.last_layout = layout
            self.last_layout_page = page
        if not self.session_active:
            return
        if device.isAssigned():
            self.clear_mixer_mode_leds()
        self.session_active = False
        self.palette_page = None
        self.record_arm_active = False
        self.mute_active = False
        self.solo_active = False
        self.volume_active = False
        self.mode_press_time = None
        if device.isAssigned():
            device.midiOutSysex(SYSEX_DAW_MODE_ON)
            device.midiOutSysex(build_layout_sysex(self.last_layout, self.last_layout_page))

    def send_transport_value(self, command, data2, pme_flags=None):
        value = 2 if data2 > 0 else 0
        if pme_flags is None:
            pme_flags = getattr(midi, 'PME_System', 0)
        transport.globalTransport(command, value, pme_flags)
        if data2 > 0:
            self.send_leds()

    def send_transport_command(self, command, event):
        self.send_transport_value(
            command,
            event.data2,
            getattr(event, 'pmeFlags', getattr(midi, 'PME_System', 0)),
        )

    def on_midi_in(self, event):
        if (
            event.status == midi.MIDI_BEGINSYSEX
            and len(event.sysex) == 11
            and list(event.sysex[:7]) == [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0E, 0x00]
        ):
            layout = event.sysex[7]
            if layout == LAYOUT_SESSION:
                if not self.session_active:
                    self.enter_session(force=True, select_layout=False)
                else:
                    self.send_mixer_grid()
                    self.send_leds()
            elif layout != 1:  # Fader layout is part of Session's mixer controls.
                self.session_active = False
                self.record_arm_active = False
                self.mute_active = False
                self.solo_active = False
                self.volume_active = False
                if device.isAssigned():
                    self.clear_mixer_mode_leds()
            event.handled = True
            return
        event.handled = False

    def on_midi_msg(self, event):
        if event.data1 == SESSION_BUTTON:
            event.handled = True
            if event.data2 > 0:
                self.enter_session(force=True)
            return

        if not self.session_active:
            event.handled = False
            return

        if self.volume_active and FADER_FIRST_CC <= event.data1 < FADER_FIRST_CC + GRID_SIZE:
            event.handled = True
            self.handle_fader_value(event.data1 - FADER_FIRST_CC, event.data2)
            return
        if self.volume_active and event.data1 in (BANK_LEFT_BUTTON, BANK_RIGHT_BUTTON):
            event.handled = True
            if event.data2 > 0:
                self.change_volume_bank(-1 if event.data1 == BANK_LEFT_BUTTON else 1)
            return

        if event.data1 == PLAY_BUTTON:
            event.handled = True
            self.send_transport_command(midi.FPT_Play, event)
            return
        if event.data1 == RECORD_BUTTON:
            event.handled = True
            self.send_transport_command(midi.FPT_Record, event)
            return
        if event.data1 == STOP_CLIP_BUTTON:
            event.handled = True
            self.send_transport_command(midi.FPT_Stop, event)
            return
        if event.data1 == RECORD_ARM_BUTTON:
            event.handled = True
            self.handle_mixer_mode_button(event.data2, 'record_arm')
            return
        if event.data1 == MUTE_BUTTON:
            event.handled = True
            self.handle_mixer_mode_button(event.data2, 'mute')
            return
        if event.data1 == SOLO_BUTTON:
            event.handled = True
            self.handle_mixer_mode_button(event.data2, 'solo')
            return
        if event.data1 == VOLUME_BUTTON:
            event.handled = True
            self.handle_mixer_mode_button(event.data2, 'volume')
            return
        if event.data1 in (PALETTE_LOW_BUTTON, PALETTE_HIGH_BUTTON):
            event.handled = True
            if event.data2 > 0:
                self.show_palette_page(0 if event.data1 == PALETTE_LOW_BUTTON else 1)
            return

        if event.midiId in (midi.MIDI_NOTEON, midi.MIDI_NOTEOFF):
            track = grid_track(event.data1)
            if track is not None:
                event.handled = True
                if track > mixer.getTrackCount():
                    return
                if event.midiId == midi.MIDI_NOTEON and event.data2 > 0:
                    if self.record_arm_active:
                        mixer.armTrack(track)
                        if mixer.isTrackArmed(track):
                            device.midiOutMsg(midi.MIDI_NOTEON, 0,
                                              event.data1, PALETTE_TRACK_ARMED)
                        else:
                            self.restore_mixer_pad(event.data1, track)
                        return
                    if self.mute_active:
                        mixer.muteTrack(track)
                        if mixer.isTrackMuted(track):
                            device.midiOutMsg(midi.MIDI_NOTEON, 0,
                                              event.data1, PALETTE_TRACK_MUTED)
                        else:
                            self.restore_mixer_pad(event.data1, track)
                        return
                    if self.solo_active:
                        mixer.soloTrack(track)
                        if mixer.isTrackSolo(track):
                            device.midiOutMsg(midi.MIDI_NOTEON, 0,
                                              event.data1, PALETTE_TRACK_SOLO)
                        else:
                            self.restore_mixer_pad(event.data1, track)
                        return
                    previous_track = mixer.trackNumber()
                    previous_note = self.note_for_track(previous_track)
                    if previous_note is not None and previous_track != track:
                        self.restore_mixer_pad(previous_note, previous_track)
                    mixer.setTrackNumber(track)
                    device.midiOutMsg(midi.MIDI_NOTEON, 0, event.data1, PALETTE_PAD_PRESSED)
                return

        exit_layouts = {
            NOTE_BUTTON: LAYOUT_NOTE,
            CHORD_BUTTON: LAYOUT_CHORD,
            CUSTOM_BUTTON: LAYOUT_CUSTOM,
        }
        if event.data1 in exit_layouts:
            event.handled = True
            if event.data2 > 0:
                self.leave_session(exit_layouts[event.data1])
            return

        event.handled = False

    def on_init(self):
        self.session_active = False
        if device.isAssigned():
            self.clear_mixer_mode_leds()
            device.midiOutSysex(SYSEX_DAW_MODE_ON)

    def on_deinit(self):
        self.session_active = False
        if device.isAssigned():
            self.clear_mixer_mode_leds()
            device.midiOutSysex(SYSEX_DAW_MODE_OFF)

    def on_refresh(self, flags):
        if self.volume_active:
            self.send_volume_values()
        else:
            self.send_mixer_grid()
        self.send_leds()


Controller = StudioController()


def OnInit():
    Controller.on_init()


def OnDeInit():
    Controller.on_deinit()


def OnMidiIn(event):
    Controller.on_midi_in(event)


def OnMidiMsg(event):
    Controller.on_midi_msg(event)


def OnUpdateBeatIndicator(value):
    Controller.send_leds()


def OnRefresh(flags):
    Controller.on_refresh(flags)
