import logging
import time

from rtmidi.midiconstants import (CHANNEL_PRESSURE,
                                  CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF)

from rxseq import common

log = logging.getLogger(__name__)


def keyboard_test(port):
    # arrow
    for i in range(0x40, 0x48):
        port.send_message([0x90, i, 0])
        port.send_message([0x90, i, 1])

    # stop all (0x51)
    port.send_message([0x90, 0x51, 0])
    port.send_message([0x90, 0x51, 1])

    # clip/stop (0x52), solo (0x53), rec/arm (0x54), mute (0x55), select (0x56)
    for i in range(0x52, 0x57):
        port.send_message([0x90, i, 0])
        port.send_message([0x90, i, 2])

    for i in range(0x00, 0x28):
        port.send_message([0x90, i, 0])
        port.send_message([0x90, i, 1])

    # play/pause
    port.send_message([0x90, 0x5b, 0])
    port.send_message([0x90, 0x5b, 1])
    # record
    port.send_message([0x90, 0x5d, 0])
    port.send_message([0x90, 0x5d, 1])
    # shift
    port.send_message([0x90, 0x62, 0])
    port.send_message([0x90, 0x62, 1])
    # sustain
    port.send_message([0x91, 0x40, 0])
    port.send_message([0x91, 0x40, 1])


def callback(event, data, state=None):
    result = get_event_from_callback(event, data)
    if result:
        log.info('midi %s', result)
        return result


def get_event_from_callback(event, data):
    key = data.driver
    state = data.state
    notes = common.initialize_default(state, 'notes', {})
    msg, _ = event
    ts = time.monotonic()
    return data.driver.handle(msg, data)


def midi_error_callback(error_type, error_msg, data, state=None):
    log.error('ERROR: %s', (error_type, error_msg, data, state))

