import time
import struct
import logging
import ctypes
from rxseq import common

log = logging.getLogger(__name__)

DEVICES = {
    '0b33:0030': 'shuttlepro'
}

SHUTTLEPRO_FORMAT = 'bBbBB'

SHUTTLEPRO_BUTTONS = {
        1 << 0: 'F1',
        1 << 1: 'F2',
        1 << 2: 'F3',
        1 << 3: 'F4',
        1 << 4: 'F5',
        1 << 5: 'F6',
        1 << 6: 'F7',
        1 << 7: 'F8',
        1 << 8: 'F9',
        1 << 9: 'B1',
        1 << 10: 'B2',
        1 << 11: 'B3',
        1 << 12: 'B4',
        1 << 13: 'M1',
        1 << 14: 'M2'
    }

def convert_button_code_to_buttons(value, button_assoc):
    buttons = {}
    for i in range(len(button_assoc)):
        result = (value >> i) & 1 == 1
        if result:
            buttons[button_assoc[1 << i]] = 1
    return buttons


def handle(_, device_state, event):
    now = time.time()
    last_time = common.initialize_default(device_state, 'last_time', now)
    common.initialize_default(device_state, 'last_buttons', set())

    (a, b, _, d, e) = struct.unpack(SHUTTLEPRO_FORMAT, event)
    x = e * 256 + d

    pos = device_state.pos

    jog = 0
    if pos is None:
        pos = b
    elif b != pos:
        jog = ctypes.c_byte(b - pos).value
        pos = b

    if jog != 0:
        if now - last_time < 0.2:
            jog *= 2
        device_state.last_time = now

    device_state.pos = pos

    buttons = convert_button_code_to_buttons(x, SHUTTLEPRO_BUTTONS)

    remove_buttons = device_state.last_buttons - buttons.keys()
    add_buttons = buttons.keys() - device_state.last_buttons

    device_state.last_buttons = buttons

    return {
        'action': 'event',
        'key': device_state.key,
        'ts': now,
        'buttons': buttons,
        '+': add_buttons,
        '-': remove_buttons,
        'controls': {
            'pos1': a,
            'pos2': jog,
            'pos3': pos
        }
    }


