import typing
from .midi import MidiDriver
from . import midi_keyboard, midi_drumpad, shuttlepro, footpedal

def get_midi_driver_from_name(midi_name: str) -> typing.Optional[MidiDriver]:
    device = midi_keyboard.match_name(midi_name)
    if not device:
        midi_drumpad.match_name(midi_name)
    return device
