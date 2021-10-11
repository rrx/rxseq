import logging
import time
from functools import partial

from rxseq import common, midi_controllers, usb_controllers
from rxseq.state import ControllerState
import rxseq.usb_devices
import rxseq.midi_devices
import rxseq.devices.mouse

log = logging.getLogger(__name__)


def merge_buttons(buttons_all, key, buttons):
    buttons_all[key] = buttons

    result = {}
    for v in buttons_all.values():
        result.update(v)

    return result


def merge_event(controller_state: ControllerState, event):
    # merge buttons from various sources
    event['buttons'] = merge_buttons(controller_state.buttons_all, event['key'], event['buttons'])
    return event


def controller_handler(controller_state: ControllerState, message_handler, event):
    # merge buttons from various sources
    event['buttons'] = merge_buttons(controller_state.buttons_all, event['key'], event['buttons'])
    message_handler(event)


def start_midi(controller_state: ControllerState, message_handler):
    # initialize and run midi in a thread
    def midi_callback(event, data, state=None):
        event = common.call_live(rxseq.midi_devices.callback, event, data, state=state)
        # event = rxseq.midi_devices.callback(event, data, state=state)
        if event:
            event = merge_event(state, event)
            message_handler(event)

    def midi_error_callback(error_type, error_msg, data, state=None):
        common.call_live(rxseq.midi_devices.error_callback, error_type, error_msg, data, state=state)

    def midi_thread():
        while True:
            midi_controllers.step(controller_state.midi)
            time.sleep(1)

    # init midi state
    controller_state.midi = midi_controllers.initialize(partial(midi_callback, state=controller_state), partial(midi_error_callback, state=controller_state))

    common.start_in_thread(midi_thread)


def start_usb(controller_state: ControllerState, message_handler):
    def cb(device_state, event):
        result = common.get_latest_version_of_function(rxseq.usb_devices.callback)(controller_state, device_state, event)
        log.info("%s", result)
        message_handler(merge_event(controller_state, result))

    controller_state.usb_state = usb_controllers.initialize(cb)
    common.start_live_thread(usb_controllers.step, state=controller_state.usb_state)


def start_mouse(controller_state: ControllerState, message_handler):
    def cb(event):
        log.info("mouse %s", event)
        message_handler(merge_event(controller_state, event))

    rxseq.devices.mouse.start(cb)

def start(message_handler):
    controller_state = ControllerState(buttons_all={})
    start_midi(controller_state, message_handler)
    start_usb(controller_state, message_handler)
    start_mouse(controller_state, message_handler)
    log.info("started")
    return controller_state
