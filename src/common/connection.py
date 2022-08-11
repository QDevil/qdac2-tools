import serial.tools.list_ports as list_ports
import serial
import re

device_signature = '0403:6014'
baud_rate = 921600


def find_serial_device():
    candidates = list(list_ports.grep(device_signature))
    if not candidates:
        raise ValueError(f'No device with signature {device_signature} found')
    if len(candidates) > 1:
        raise ValueError(f'More than one device with signature {device_signature} found')
    return candidates[0].device


def get_id(connection):
    raw = bytes('*idn?\n', 'utf8')
    connection.write(raw)
    data = connection.read(30)
    return data.decode('utf-8')


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
    match = re.search('[0-9A-F]+', answer)
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
    match = re.search('[0-9a-f._-]+', answer)
    return match[0]


def get_dhcp(connection):
    raw = bytes('syst:comm:lan:dhcp?\n', 'utf8')
    connection.write(raw)
    data = connection.read(3)
    return (float(data.decode('utf-8')) == 1)


def report_device_info():
    serial_device = find_serial_device()
    print(f'Found QDAC-II')
    print(f'Port: {serial_device}')
    connection = serial.Serial(serial_device, baud_rate, timeout=0.2)
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
