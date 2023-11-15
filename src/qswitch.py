import pyvisa as visa
from typing import Sequence, List


def is_ok(message: str) -> bool:
    return message == '0,"No error"'


class QSwitch:
    """
    Simple wrapper for communicating with a QSwitch.

    Use like this on USB:

    import qswitch
    import common.connection as conn
    device = conn.find_qswitch_on_usb()
    switch = qswitch.QSwitch(device)
    print(switch.status())
    """

    def __init__(self, visa_resource: visa.Resource):
        self._switch = visa_resource
        self._switch.write_termination = '\n'
        self._switch.read_termination = '\n'
        self._switch.baud_rate = 9600
        self._switch.timeout = 1000  # ms
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
        Send a SCPI command to the QSwitch
        """
        self._write(cmd)
        errors = self.query('all?')
        if is_ok(errors):
            return
        raise ValueError(f'Error: {errors} after executing {cmd}')

    def query(self, cmd: str) -> str:
        """
        Send a SCPI query to the QSwitch
        """
        if self._record_commands:
            self._scpi_sent.append(cmd)
        try:
            answer = self._switch.query(cmd)
        except visa.errors.VisaIOError as error:
            msg = f'QSwitch failed query (1st try): {repr(error)}'
            print(msg)
            answer = self._switch.query(cmd)
        return answer

    def clear(self) -> None:
        """
        Function to reset the VISA message queue of the instrument.
        """
        self._switch.clear()

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

    def _write(self, cmd: str) -> None:
        if self._record_commands:
            self._scpi_sent.append(cmd)
        self._switch.write(cmd)
