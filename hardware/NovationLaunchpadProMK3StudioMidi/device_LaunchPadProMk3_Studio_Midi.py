# name=NovationLaunchpadProMK3StudioMidi
# url=
# SPDX-License-Identifier: GPL-3.0-only


def OnMidiIn(event):
    event.handled = False


def OnMidiMsg(event):
    event.handled = False
