import serial
from blinker import signal
from serial.tools import list_ports


class SerialConn:
    def __init__(self):        
        # public
        self.__baud_rate = "9600"
        self.__port = self.available_ports()[0]
        
        # private
        self.__serial = serial.Serial()
        self.__init_char = "None"
        self.__end_char = "No Line Ending"
        self.__status = False
        
        # signals
        self.status_changed = signal('status_changed')
        self.error_occurred = signal('error_occurred')

    def start_conn(self):
        try:
            if self.__serial.is_open:
                self.close_conn()
            self.__serial.baudrate = int(self.__baud_rate)
            self.__serial.port = self.__port
            self.__serial.open()
            self.status = self.__serial.is_open
                
        except serial.SerialException as exp:
            print(f"SerialExpection ocurred: {exp}")
            self.error_occurred.send(self, exp=exp)
        except:
            msg = "Error in connection process"
            print(msg)
            self.error_occurred.send(self, exp=msg)

    def close_conn(self):
        self.__serial.close()
        self.status = self.__serial.is_open

    def send_msg(self, msg):
        init_char = self.initial_characters()[self.__init_char]
        end_char = self.end_line_characters()[self.__end_char]
        cmd = f"{init_char}{msg}{end_char}".encode("utf-8")
        if self.status:
            self.__serial.write(cmd)

    def on_read_response(self) -> str:
        try:
            if self.__serial.in_waiting > 0:
                msg = self.__serial.read_until(expected=b'\r')
                msg = msg.decode("utf-8").strip()
                return msg
            return ""
        except serial.SerialException as exp:
            print(f"SerialException ocurred: {exp}")
            return ""

    @property
    def baud_rate(self) -> str:
        return self.__baud_rate

    @baud_rate.setter
    def baud_rate(self, new_baud_rate: str):
        if new_baud_rate == self.__baud_rate:
            return
        self.__baud_rate = new_baud_rate

    @property
    def port(self) -> str:
        return self.__port

    @port.setter
    def port(self, new_port: str):
        if new_port == self.__port:
            return
        self.__port = new_port
        
    @property
    def status(self):
        return self.__status
        
    @status.setter
    def status(self, new_status: bool):
        if new_status == self.__status:
            return
        self.__status = new_status
        self.status_changed.send(self)

    def set_initial_character(self, new_init_char):
        if new_init_char == self.__init_char:
            return
        self.__init_char = new_init_char

    def set_end_line_character(self, new_end_char):
        if new_end_char == self.__end_char:
            return
        self.__end_char = new_end_char

    @staticmethod
    def baud_rates() -> list[str]:
        return [
            "1200",
            "2400",
            "4800",
            "9600",
            "19200",
            "38400",
            "57600",
            "115200",
        ]

    @staticmethod
    def available_ports() -> list[str]:
        ports = list_ports.comports()
        return [port.device for port in ports]

    @staticmethod
    def initial_characters() -> dict[str, str]:
        return {
            "None": "",
            "Start of Text (STX)": "\x02",
            "Start of header (SOH)": "\x01",
            "Escape (ESC)": "\x1B",
        }

    @staticmethod
    def end_line_characters() -> dict[str, str]:
        return {
            "No Line Ending": "",
            "Newline": "\n",
            "Carriage Return": "\r",
            "Both NL & CR": "\r\n",
        }
