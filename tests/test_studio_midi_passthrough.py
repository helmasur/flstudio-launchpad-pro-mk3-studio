# SPDX-License-Identifier: GPL-3.0-only

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "hardware/NovationLaunchpadProMK3StudioMidi/device_LaunchPadProMk3_Studio_Midi.py"
)


class Event:
    def __init__(self):
        self.handled = True


class StudioMidiPassthroughTests(unittest.TestCase):
    def test_musical_midi_is_left_unhandled(self):
        spec = importlib.util.spec_from_file_location("studio_midi_passthrough", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        event = Event()

        module.OnMidiIn(event)
        self.assertFalse(event.handled)

        event.handled = True
        module.OnMidiMsg(event)
        self.assertFalse(event.handled)


if __name__ == "__main__":
    unittest.main()
