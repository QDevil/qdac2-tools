import serial.tools.list_ports as list_ports
import serial

device_signature = '0403:6014'
baud_rate = 921600


def find_serial_device():
    candidates = list(list_ports.grep(device_signature))
    if not candidates:
        raise ValueError(f'No device with signature {device_signature} found')
    if len(candidates) > 1:
        raise ValueError(f'More than one device with signature {device_signature} found')
    return candidates[0].device


def report_device_info():
    serial_device = find_serial_device()
    print(f'Found QDAC-II on {serial_device}')
    connection = serial.Serial(serial_device, baud_rate, timeout=1)
    raw = bytes('*idn?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    id = data.decode('utf-8')
    print(f'identification: {id}')
