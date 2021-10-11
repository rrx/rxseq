import rtmidi
import typing
from rxseq import common
import time
import logging
from .midi import MidiDriver


log = logging.getLogger(__name__)


def match_name(name: str) -> typing.Optional[MidiDriver]:
    if name.startswith("Akai MPD18"):
        return MidiDriver("drumpad", False, True, None)


