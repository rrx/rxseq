import logging

import pyudev
import usb.core
import usb.util

from rxseq import common
from rxseq.common import start_in_thread

log = logging.getLogger('usb_controllers')


class USBState(common.State):
    pass


class DeviceState(common.State):
    pass


SUPPORTED_DEVICES = {
    '0b33:0030': 'shuttlepro',
    '05f3:00ff': 'footpedal'
    # '09e8:0027': ('AKAIProfessional', default_mainthread),
    # '09e8:0074': ('AKAIProfessional', default_mainthread)
}


def hex(s):
    if s is None:
        return 0

    return int(s, 16)


def extract_device_id(device):
    return "%04x:%04x" % (hex(device.get('ID_VENDOR_ID')), hex(device.get('ID_MODEL_ID'))), device.get('DEVPATH')


def device_open(device):
    id_vendor = hex(device.get('ID_VENDOR_ID'))
    id_model = hex(device.get('ID_MODEL_ID'))

    usb_device = usb.core.find(idVendor=id_vendor, idProduct=id_model)

    for i in usb_device[0].interfaces():
        for e in i.endpoints():
            if e.bEndpointAddress in [0x81, 0x82]:
                try:
                    if usb_device.is_kernel_driver_active(0) is True:
                        usb_device.detach_kernel_driver(0)
                except usb.core.USBError as e:
                    log.error("[%s] Kernel driver won't give up control over device: %s", device, str(e))
                    return None, None

                try:
                    usb_device.set_configuration(usb_device[0].bConfigurationValue)
                    usb_device.reset()
                except usb.core.USBError as e:
                    log.error("[%s] Cannot set configuration the device: %s", device, str(e))
                    return None, None

                return usb_device, e

    return None, None


def device_thread(state: USBState, device_state: DeviceState):
    while True:
        try:
            endpoint = device_state.endpoint
            data = device_state.usb_device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=1000)
            state.callback(device_state, data)
        except usb.core.USBError as e:
            pass
        except KeyboardInterrupt:
            break
        except:
            import traceback
            traceback.print_exc()

        if state.stop:
            return


def device_add(state: USBState, device):
    device_id, path = extract_device_id(device)
    device_key = SUPPORTED_DEVICES.get(device_id)

    # only open if we know about the device
    if device_key is None:
        return

    usb_device, endpoint = device_open(device)

    if usb_device is None:
        log.error("Unable to open device")
    else:
        device_state = DeviceState(device=device, key=device_key, usb_device=usb_device, endpoint=endpoint)
        state.devices[path] = device_state
        start_in_thread(device_thread, state, device_state)

        id_vendor = hex(device.get('ID_VENDOR_ID'))
        id_model = hex(device.get('ID_MODEL_ID'))
        log.info("[%d devices] Connected %s (%04x:%04x)", len(state.devices), device_key, id_vendor, id_model)


def device_remove(state: USBState, device):
    devices = state.get_or_create('devices', {})

    _, path = extract_device_id(device)

    if path not in devices:
        return

    device = devices.pop(path, None)

    log.info("[%d devices] Disconnected %s (%04x:%04x)",
             len(devices), device.handler, device.id_vendor, device.id_model)


def initialize(callback):
    state = USBState(devices={})
    state.callback = callback

    context = pyudev.Context()
    state.monitor = pyudev.Monitor.from_netlink(context)
    state.monitor.filter_by(subsystem='usb')

    # add existing devices
    for device in context.list_devices(subsystem='usb'):
        log.debug("ADD: %s", device)
        device_add(state, device)

    return state


def step(state: USBState):
    event = next(iter(state.monitor.poll, None))
    if event.action == 'add':
        log.debug("ADD: %s", event)
        device_add(state, event)

    elif event.action == 'remove':
        log.debug("REMOVE: %s", event)
        device_remove(state, event)


def usb_controllers(callback):
    state = initialize(callback)
    try:
        while True:
            step(state)
    except KeyboardInterrupt:
        state.stop = True

    log.info('exit')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(thread)s %(name)s %(message)s')

    def cb(ev):
        log.info('event: %s', ev)
        pass

    usb_controllers(cb)
