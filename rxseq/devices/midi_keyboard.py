import rtmidi
import typing
from rxseq import common
import time
import logging
from .midi import MidiDriver

from rtmidi.midiconstants import (CHANNEL_PRESSURE,
                                  CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF)


log = logging.getLogger(__name__)

CONTROL_NOTES = dict(
    record=93,
    play_pause=91,
    shift=98,
    clip_stop=82,
    solo=83,
    rec_arm=84,
    mute=85,
    select=86,
    stop_all_clips=81,
    up=64,
    down=65,
    left=66,
    right=67,
    volume=68,
    pan=69,
    send=70,
    device=71)


CONTROL_NOTE_INDEX = dict([(v, k) for k, v in CONTROL_NOTES.items()])



def match_name(name: str) -> typing.Optional[MidiDriver]:
    if name.startswith("APC Key 25"):
        driver = MidiDriver("keyboard", True, True, handler)
        driver.add_control_notes(CONTROL_NOTES)
        return driver


def handler(driver, msg, data):
    status = msg[0] & 0xF0
    channel = msg[0] & 0x0F

    # handle LEDS on key press
    if status == NOTE_ON and channel == 0:
        _, note, velocity = msg
        if note <= 0x28 or 0x40 <= note <= 0x47 or 0x52 <= note <= 0x56:
            data.midi_out.send_message([NOTE_ON, note, 1])
    if status == NOTE_OFF and channel == 0:
        _, note, velocity = msg
        if note <= 0x28 or 0x40 <= note <= 0x47 or 0x52 <= note <= 0x56:
            data.midi_out.send_message([NOTE_ON, note, 0])

