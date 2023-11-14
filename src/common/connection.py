import serial.tools.list_ports as list_ports
import serial
import re
from dataclasses import dataclass


@dataclass
class Device:
    kind: str
    signature: str
    baud_rate: int


devices = [
    Device('QDAC-II', '0403:6014', 921600),
    Device('QSwitch', '04D8:00DD', 9600),
]


def find_serial_devices():
    result = []
    for device in devices:
        candidates = list(list_ports.grep(device.signature))
        if len(candidates) > 1:
            raise ValueError(f'More than one device with signature {device.signature} found')
        if len(candidates) == 1:
            result.append((device, candidates[0].device))
    if not result:
        raise ValueError('No devices found')
    return result


def get_id(connection):
    raw = bytes('*idn?\n', 'utf8')
    connection.write(raw)
    data = connection.read(40)
    answer = data.decode('utf-8')
    match = re.search('[^\n]+', answer)
    return match[0]


def get_ip_addr(connection):
    raw = bytes('syst:comm:lan:ipad?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    answer = data.decode('utf-8')
    match = re.search('[0-9.]+', answer)
    return match[0]


def get_mac_addr(connection):
    raw = bytes('syst:comm:lan:mac?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    answer = data.decode('utf-8')
    match = re.search('[0-9A-F:]+', answer)
    return match[0]


def get_gateway(connection):
    raw = bytes('syst:comm:lan:gat?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    answer = data.decode('utf-8')
    match = re.search('[0-9.]+', answer)
    return match[0]


def get_mask(connection):
    raw = bytes('syst:comm:lan:smas?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    answer = data.decode('utf-8')
    match = re.search('[0-9.]+', answer)
    return match[0]


def get_name(connection):
    raw = bytes('syst:comm:lan:host?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    answer = data.decode('utf-8')
    match = re.search('[^"]+', answer)
    return match[0]


def get_dhcp(connection):
    raw = bytes('syst:comm:lan:dhcp?\n', 'utf8')
    connection.write(raw)
    data = connection.read(3)
    return (float(data.decode('utf-8')) == 1)


def report_device_info():
    for device, serial_info in find_serial_devices():
        print(f'Found: {device.kind}')
        print(f'Port: {serial_info}')
        connection = serial.Serial(serial_info, device.baud_rate, timeout=0.2)
        id = get_id(connection)
        print(f'identification: {id}')
        mac_addr = get_mac_addr(connection)
        print(f'MAC address: {mac_addr}')
        gateway = get_gateway(connection)
        print(f'Gateway: {gateway}')
        mask = get_mask(connection)
        print(f'Network mask: {mask}')
        ip_addr = get_ip_addr(connection)
        print(f'IP address: {ip_addr}')
        name = get_name(connection)
        print(f'Host name: {name}')
        dhcp = 'yes' if get_dhcp(connection) else 'no'
        print(f'DHCP enabled: {dhcp}')
        print('')
