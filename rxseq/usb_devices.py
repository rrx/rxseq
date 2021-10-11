import time
import struct
import logging
from rxseq import common
from rxseq import devices
import ctypes


log = logging.getLogger(__name__)


def callback(state, device_state, event):
    if device_state.key == 'shuttlepro':
        return devices.shuttlepro.handle(state.usb_state, device_state, event)
    elif device_state.key == 'footpedal':
        return devices.footpedal.handle(state.usb_state, device_state, event)
