import rtmidi
import typing
from rxseq import common, devices
import time
import logging
log = logging.getLogger(__name__)


__all__ = ['step', 'update_callbacks', 'initialize']


class MidiState(common.State):
    pass


def add_port(state: MidiState, i, driver: devices.MidiDriver, name):
    rtapi = rtmidi.API_LINUX_ALSA

    midi_state = common.State(
        driver=driver, state=state, name=name
    )

    if driver.bind_to_input:
        midi_state.midi_out = rtmidi.MidiOut(rtapi=state.rtapi, name="midi:%s:%d" % (driver, i))
        midi_state.midi_out.open_port(i)
        state.outports[name] = midi_state.midi_out

    if driver.bind_to_output:
        midi_state.midi_in = rtmidi.MidiIn(rtapi=state.rtapi, name="midi:%s:%d" % (driver, i))
        midi_state.midi_in.open_port(i)
        midi_state.midi_in.set_callback(state.callback, data=midi_state)
        midi_state.midi_in.set_error_callback(state.error_callback, data=midi_state)

    state.ports[name] = midi_state.midi_in

    log.info("ADD %s %s", name, i)


def remove_port(state: MidiState, name):
    midi_port = state.ports.get(name)
    # remove port
    midi_port.cancel_callback()
    midi_port.cancel_error_callback()
    midi_port.close_port()
    log.info("REMOVE %s", name)
    state.ports.pop(name)


def update_ports(state: MidiState, available_ports):
    current_ports = {}
    for i, name in enumerate(available_ports):
        current_ports[name] = i

    ports_to_remove = set()
    for name, midi_port in state.ports.items():
        if name not in current_ports:
            ports_to_remove.add(name)

    for name in ports_to_remove:
        remove_port(state, name)

    for name, i in current_ports.items():
        if name not in state.ports:
            driver = devices.get_midi_driver_from_name(name)
            if driver is None:
                continue
            add_port(state, i, driver, name)


def initialize_state() -> MidiState:
    rtapi = rtmidi.API_LINUX_ALSA
    return MidiState(
        midi=rtmidi.MidiIn(rtapi=rtapi),
        rtapi=rtapi,
        ports={},
        outports={},
        buttons={}
    )


def midi_controllers(callback, error_callback):
    state = initialize(callback, error_callback)
    while True:
        step(state)


def update_callbacks(state: MidiState, callback, error_callback):
    state.callback = callback
    state.error_callback = error_callback


def initialize(callback, error_callback):
    state = initialize_state()
    state.callback = callback
    state.error_callback = error_callback
    return state


def step(state: MidiState):
    available_ports = state.midi.get_ports()
    update_ports(state, available_ports)
    time.sleep(1)


if __name__ == '__main__':
    def _callback(event, data):
        print(data.name, event)
        state = data.state
        msg, _ = event
        result = data.driver.handle(msg, data)
        print(result)


    def _error_callback(error_type, error_msg, data):
        print('ERROR', error_type, error_msg, data)


    midi_controllers(_callback, _error_callback)
