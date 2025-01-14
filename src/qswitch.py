import pyvisa as visa
from typing import Sequence, List, Tuple
from dataclasses import dataclass
import socket
from datetime import datetime
from time import sleep as sleep_s
import re

def is_ok(message: str) -> bool:
    return message == '0,"No error"'

@dataclass
class UdpConfig:
    ip: str
    port: int = 5025
    timeout_ms: float = 2000
    delay_s: float = 0.01
    verbose: bool = False

UDP_QUERY_MAX_ATTEMPTS = 5
UDP_WRITE_MAX_ATTEMPTS = 3

class QSwitch:
    """
    Simple wrapper for communicating with a QSwitch.

    Use like this on USB:

    import qswitch
    import common.connection as conn
    device = conn.find_qswitch_on_usb()
    switch = qswitch.QSwitch(device)
    print(switch.status())

    Use like this for ethernet (Firmware verison >= 1.9):
    
    import qswitch
    device = qswitch.UdpConfig(ip="192.168.8.100")
    switch = qswitch.QSwitch(device)
    print(switch.status())
    """

    def __init__(self, resource: visa.Resource | UdpConfig):
        self.verbose = False 
        self.log = print
        
        if isinstance(resource, UdpConfig):
            # UDP Mode
            self._udp_mode = True
            self._udp_config = resource
            self.verbose = self._udp_config.verbose
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.settimeout(resource.timeout_ms / 1000)  # Convert ms to seconds
            if self.verbose: 
                self.log(f"{datetime.now()} Connected UDP: {resource.ip}:{resource.port}, timeout:{resource.timeout_ms}ms")
        else:
            # VISA Mode
            self._udp_mode = False
            self._switch = resource
            self._switch.write_termination = '\n'
            self._switch.read_termination = '\n'
            self._switch.timeout = 5000
            self._switch.query_delay = 0.01
            self._switch.baud_rate = 9600
            if self.verbose:
                self.log(f"{datetime.now()} Connected VISA: timeout:{self._switch.timeout }ms, query_delay:{self._switch.query_delay}s")

        self._record_commands = False

    def status(self) -> str:
        """
        Return the error status of the instrument.
        """
        return self.query('all?')

    def sequence(self, cmds: Sequence[str]):
        """
        Send a sequence of SCPI commands to the QSwitch
        """
        for cmd in cmds:
            self._write(cmd)
            errors = self.query('all?')
            if is_ok(errors):
                return
            raise ValueError(f'Error: {errors} while executing {cmds}')
   
    def command(self, cmd: str):
        """
        Send a SCPI command to the QSwitch, and check when ready for a new command by sending a query
        UDP connection: For relay open/close and *rst commands, only, it is checked the command was well received
        """
        if self._udp_mode:
            cmd_lower = cmd.lower()
            is_open_close_cmd = cmd_lower.find("clos ",0,12) != -1 or (cmd_lower.find("close ",0,12) != -1) or (cmd_lower.find("open ",0,12)  != -1) 
            is_rst_cmd = (cmd_lower == "*rst")
            counter = 0
            while True: 
                try:
                    self._sock.sendto(f"{cmd}\n".encode(), (self._udp_config.ip, self._udp_config.port))
                except Exception as e:
                    raise ValueError(f'QSwitch {self._udp_config.ip} (UDP): Write Error [{cmd}]: {repr(e)}')
                # Check that relay command was well received
                if (is_open_close_cmd or is_rst_cmd): 
                    if (counter > 0) and self.verbose: self.log(f'{datetime.now()} UDP write repeat {counter} [{cmd}]')
                    if is_open_close_cmd:
                        self.query('*opc?')  
                        splitcmd = cmd.split(" ")
                        reply = self.query(splitcmd[0]+"? "+splitcmd[1] if len(splitcmd)==2 else "")
                        if (len(reply) > 0) and (reply.find("0") == -1):  
                            return
                    elif is_rst_cmd:
                        self.query('*opc?')    
                        reply = self.query("clos:stat?")
                        if (reply == "(@1!0:24!0)"):
                            return
                    counter += 1
                    if self.verbose: 
                        self.log(f"{datetime.now()} UDP: {counter} failed check of [{cmd_lower}], result: {reply}")
                    if (counter >= UDP_WRITE_MAX_ATTEMPTS):
                        raise ValueError(f'QSwitch {self._udp_config.ip} (UDP): Command check failure [{cmd_lower}] after {UDP_WRITE_MAX_ATTEMPTS} attempts')
                else:
                    self.query('*opc?')
                    return
        else: # VISA
            try:
                self._switch.write(cmd)
                self.query('*opc?')
            except Exception as e:
                if self.verbose: self.log(f'{datetime.now()} VISA error: {repr(e)}')
                raise ValueError(f"QSwitch VISA error: {repr(e)}")
            return


    def query(self, cmd: str) -> str:
        """
        Send a SCPI query to the QSwitch
        UDP: Repeat query until a reply is received
        """
        if self._record_commands:
            self._scpi_sent.append(cmd)

        if self._udp_mode: # UDP (ethernet)
            counter = 0
            time_before_next = 0.1
            while True:
                try:
                    self.clear()
                    self._sock.sendto(f"{cmd}\n".encode(), (self._udp_config.ip, self._udp_config.port))
                    sleep_s(self._udp_config.delay_s)
                    # Wait for response
                    time_before = datetime.now()
                    data, _ = self._sock.recvfrom(1024)
                    answer = data.decode().strip()
                    if (counter > 0) and self.verbose: self.log(f'{datetime.now()} UDP query repeat {counter} [{cmd}]')
                    return answer
                except Exception as error:
                    counter += 1
                    if self.verbose:
                        self.log(f'{time_before} - {datetime.now().time()} UDP query error {counter} [{cmd}]: {repr(error)}')
                    if (counter >= UDP_QUERY_MAX_ATTEMPTS):
                        raise ValueError(f'QSwitch {self._udp_config.ip} (UDP): Query timeout [{cmd}] after {UDP_QUERY_MAX_ATTEMPTS} attempts')
                    sleep_s(time_before_next)
                    time_before_next += 0.5   # Next time we wait even longer so that we do not quickly run out of retries
        else: # VISA 
            try:
                answer = self._switch.query(cmd)
            except visa.errors.VisaIOError as error:
                if self.verbose:
                    self.log(f'{datetime.now()} QSwitch failed VISA query [{cmd}] (1st try): {repr(error)}')
                raise ValueError(f'QSwitch failed VISA query [{cmd}] (1st try): {repr(error)}')
            return answer

    def clear(self) -> None:
        """
        Function to reset the connection state for TCPIP (FW <= 1.3) 
        or flush the input buffer for a UDP connection (FW >= 1.9).
        In USB-serial mode, do nothing. 
        """
        if self._udp_mode:
            self._sock.settimeout( 0.0001 )
            while True:
                try:
                    data,_ = self._sock.recvfrom(1024)
                except:
                    break
            self._sock.settimeout( self._udp_config.timeout_ms / 1000)
        else: 
            if (self._switch.resource_class == "SOCKET"):
                self._switch.clear()
            

    def close(self):
        if self._udp_mode:
            self._sock.close()
        else:
            self._switch.close()


    def _write(self, cmd: str) -> None:
        if self._record_commands:
            self._scpi_sent.append(cmd)

        if self._udp_mode:
            try:
                self._sock.sendto(f"{cmd}\n".encode(), (self._udp_config.ip, self._udp_config.port))
            except Exception as e:
                self.log(f'{datetime.now()} UDP write Error: {repr(e)}')  # raise?
                raise ValueError(f'QSwitch {self._udp_config.ip} (UDP): Write Error [{cmd}]: {repr(e)}')
        else:
            self._switch.write(cmd)

    def _read(self):
        counter = 0
        time_before_next = 0.1
        while True:
            try:
                # Wait for response
                data, _ = self._sock.recvfrom(1024)
                answer = data.decode().strip()
                if (counter > 1) and self._verbose: 
                    self.log(f'{datetime.now()} UDP read repeat {counter}')
                return answer
            except Exception as error:
                counter += 1
                if self.verbose:
                    self.log(f'{datetime.now()} UDP read error {counter} : {repr(error)}')
                if (counter >= UDP_QUERY_MAX_ATTEMPTS):
                    raise ValueError(f'QSwitch {self._udp_config.ip} (UDP): Read timeout after {UDP_QUERY_MAX_ATTEMPTS} attempts')
                sleep_s(time_before_next)
                time_before_next += 0.5

    # ----------------------------------------------------------------------
    # Debugging and testing

    def start_recording_scpi(self) -> None:
        """
        Record all SCPI commands sent to the instrument

        Any previous recordings are removed.  To inspect the SCPI commands sent
        to the instrument, call get_recorded_scpi_commands().
        """
        self._scpi_sent: List[str] = []
        self._record_commands = True

    def get_recorded_scpi_commands(self) -> Sequence[str]:
        """
        Returns the SCPI commands sent to the instrument
        """
        commands = self._scpi_sent
        self._scpi_sent = []
        return commands

    # ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Helpers
State = Sequence[Tuple[int, int]]


def _line_tap_split(input: str) -> Tuple[int, int]:
    pair = input.split('!')
    if len(pair) != 2:
        raise ValueError(f'Expected channel pair, got {input}')
    if not pair[0].isdecimal():
        raise ValueError(f'Expected channel, got {pair[0]}')
    if not pair[1].isdecimal():
        raise ValueError(f'Expected channel, got {pair[1]}')
    return int(pair[0]), int(pair[1])


def channel_list_to_state( channel_list: str) -> State:
    outer = re.match(r'\(@([0-9,:! ]*)\)', channel_list)
    if not outer:
        raise ValueError(f'Expected channel list, got {channel_list}')
    result: List[Tuple[int, int]] = []
    sequences = outer[1].split(',')
    if sequences == ['']:
        return result
    for sequence in sequences:
        limits = sequence.split(':')
        if limits == ['']:
            raise ValueError(f'Expected channel sequence, got {limits}')
        line_start, tap_start = _line_tap_split(limits[0])
        line_stop, tap_stop = line_start, tap_start
        if len(limits) == 2:
            line_stop, tap_stop = _line_tap_split(limits[1])
        if len(limits) > 2:
            raise ValueError(f'Expected channel sequence, got {limits}')
        if tap_start != tap_stop:
            raise ValueError(
                f'Expected same breakout in sequence, got {limits}')
        for line in range(line_start, line_stop+1):
            result.append((line, tap_start))
    return result
