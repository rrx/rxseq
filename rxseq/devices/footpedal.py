import time
import struct
import logging
import ctypes
from rxseq import common

FOOTPEDAL_FORMAT = 'bb'

FOOTPEDAL_BUTTONS = {
    1 << 0: 'L',
    1 << 1: 'C',
    1 << 2: 'R'
}

def convert_button_code_to_buttons(value, button_assoc):
    buttons = {}
    for i in range(len(button_assoc)):
        result = (value >> i) & 1 == 1
        if result:
            buttons[button_assoc[1 << i]] = 1
    return buttons


def handle(_, device_state, event):
    last_buttons = device_state.last_buttons or set()

    now = time.time()
    (x, _) = struct.unpack(FOOTPEDAL_FORMAT, event)

    buttons = convert_button_code_to_buttons(x, FOOTPEDAL_BUTTONS)

    remove_buttons = last_buttons - buttons.keys()
    add_buttons = buttons.keys() - last_buttons

    device_state.last_buttons = buttons

    return {
        'action': 'event',
        'key': device_state.key,
        'ts': now,
        'buttons': buttons,
        '+': add_buttons,
        '-': remove_buttons,
        'controls': {}
    }

