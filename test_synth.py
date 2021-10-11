import fluidsynth
import time
from rxseq import controllers
import logging

from rtmidi.midiconstants import (CHANNEL_PRESSURE,
                                  CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF)

log = logging.getLogger(__name__)


class App:
    def __init__(self):
        self.fs = fluidsynth.Synth()
        self.fs.start(driver='pulseaudio')
        sf = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
        self.sfid = self.fs.sfload(sf)
        # create channels on synth
        self.fs.program_select(0, self.sfid, 0, 114)
        self.fs.program_select(1, self.sfid, 0, 0)
        self.fs.program_select(2, self.sfid, 0, 109)

    def event(self, e):
        status = e.get('status')
        channel = e.get('channel')
        note = e.get('note')
        velocity = e.get('velocity')
        if status == NOTE_ON:
            self.fs.noteon(channel, note, velocity)
        elif status == NOTE_OFF:
            self.fs.noteoff(channel, note)
        log.info(e['buttons'])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(relativeCreated)6d %(thread)s %(name)s %(message)s')
    app = App()
    controllers.start(app.event)

