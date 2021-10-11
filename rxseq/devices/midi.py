import time
from rtmidi.midiconstants import (CHANNEL_PRESSURE,
                                  CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF)
import logging
log = logging.getLogger(__name__)


class MidiDriver:
    def __init__(self, name, bind_to_input, bind_to_output, handler):
        self.name = name
        self.bind_to_input = bind_to_input
        self.bind_to_output = bind_to_output
        self.handler = handler
        self.index = {}
        self.notes = {}

    def add_control_notes(self, control_notes):
        self.index = dict([(v, k) for k, v in control_notes.items()])

    def handle(self, msg, data):
        if self.handler:
            self.handler(self, msg, data)
        return self.default_handler(msg, data)

    def dump_event(self, key, status, ts, channel, note, velocity):
        velocity /= 127.0
        log.info("%s %s channel: %s note: %s velocity: %s",
                 key, status, "0x%02x" % channel, "0x%02x" % (note or 0), "%.04f" % (velocity or 0))

    def default_handler(self, msg, data):
        status = msg[0] & 0xF0
        channel = msg[0] & 0x0F
        ts = time.monotonic()

        if status in [CHANNEL_PRESSURE]:
            (_, velocity) = msg
            name = "P_%02X" % (channel)

            self.dump_event(self.name, "pressure", ts, channel, None, velocity)

            return {
                'action': 'event',
                'midi': msg,
                'channel': channel,
                'status': status,
                'velocity': velocity,
                'key': self.name,
                'ts': ts,
                'buttons': set(),
                'controls': {
                    name: velocity,
                }
            }

        elif status in [CONTROLLER_CHANGE]:
            status, note, velocity = msg
            name = "C_%02X_%02X" % (channel, note)

            self.dump_event(self.name, "control", ts, channel, note, velocity)
            return {
                'action': 'event',
                'midi': msg,
                'channel': channel,
                'status': status,
                'velocity': velocity,
                'note': note,
                'key': self.name,
                'ts': ts,
                'buttons': set(),
                'controls': {
                    name: velocity,
                }
            }

        elif status in [NOTE_ON]:
            _, note, velocity = msg
            names = [
                "MIDI_%02X_%02X" % (channel, note)
            ]

            if channel == 0:
                v = self.index.get(note)
                if v:
                    names.append(v)

            for name in names:
                self.notes[name] = velocity

            self.dump_event(self.name, "note_on", ts, channel, note, velocity)

            return {
                'action': 'event',
                'midi': msg,
                'channel': channel,
                'status': status,
                'velocity': velocity,
                'note': note,
                'key': self.name,
                'ts': ts,
                'buttons': self.notes,
                '+': names,
                '-': [],
                'controls': {}
            }

        elif status in [NOTE_OFF]:
            _, note, velocity = msg
            names = ["MIDI_%02X_%02X" % (channel, note)]
            if channel == 0:
                v = self.index.get(note)
                if v:
                    names.append(v)
            for name in names:
                self.notes.pop(name, None)
            self.dump_event(self.name, "note_off", ts, channel, note, velocity)


            return {
                'action': 'event',
                'midi': msg,
                'channel': channel,
                'status': status,
                'velocity': velocity,
                'note': note,
                'key': self.name,
                'ts': ts,
                'buttons': self.notes,
                '+': [],
                '-': names,
                'controls': {}
            }

        else:
            print("Unhandled event", event, data)



