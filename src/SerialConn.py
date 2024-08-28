import serial
from blinker import signal
from serial.tools import list_ports


class SerialConn:
    """
    A class to handle serial communication.

    This class provides methods to start and close a serial connection, send messages,
    read responses, and manage connection settings such as baud rate, port, initial
    character, and end line character.
    """
    def __init__(self):
        """
        Initialize the SerialConn instance.

        Sets default values for baud rate, port, and connection status. Initializes
        the serial connection and sets up signal handlers for status changes and errors.
        """        
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
        """
        Start the serial connection.

        Opens the serial port with the specified baud rate and port. Emits an error
        signal if an exception occurs during the connection process.
        """
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
        """
        Close the serial connection.

        Closes the serial port and updates the connection status.
        """
        self.__serial.close()
        self.status = self.__serial.is_open

    def send_msg(self, msg: str):
        """
        Send a message through the serial connection.

        Encodes the message with the specified initial and end line characters and
        sends it through the serial port if the connection is active.

        Args:
            msg (str): The message to send.
        """
        init_char = self.initial_characters()[self.__init_char]
        end_char = self.end_line_characters()[self.__end_char]
        cmd = f"{init_char}{msg}{end_char}".encode("utf-8")
        if self.status:
            self.__serial.write(cmd)

    def on_read_response(self) -> str:
        """
        Read a response from the serial connection.

        Reads data from the serial port until a carriage return character is encountered.
        Decodes the received data and returns it as a string.

        Returns:
            str: The decoded message received from the serial port.
        """
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
        """
        Get the current baud rate.

        Returns:
            str: The current baud rate as a string.
        """
        return self.__baud_rate

    @baud_rate.setter
    def baud_rate(self, new_baud_rate: str):
        """
        Set a new baud rate.

        Updates the baud rate if the new value is different from the current one.

        Args:
            new_baud_rate (str): The new baud rate as a string.
        """
        if new_baud_rate == self.__baud_rate:
            return
        self.__baud_rate = new_baud_rate

    @property
    def port(self) -> str:
        """
        Get the current serial port.

        Returns:
            str: The current serial port as a string.
        """
        return self.__port

    @port.setter
    def port(self, new_port: str):
        """
        Set a new serial port.

        Updates the serial port if the new value is different from the current one.

        Args:
            new_port (str): The new serial port as a string.
        """
        if new_port == self.__port:
            return
        self.__port = new_port
        
    @property
    def status(self) -> bool:
        """
        Get the current connection status.

        Returns:
            bool: The current connection status.
        """
        return self.__status
        
    @status.setter
    def status(self, new_status: bool):
        """
        Set a new connection status.

        Updates the connection status and emits a status_changed signal if the new
        value is different from the current one.

        Args:
            new_status (bool): The new connection status.
        """
        if new_status == self.__status:
            return
        self.__status = new_status
        self.status_changed.send(self)

    def set_initial_character(self, new_init_char: str):
        """
        Set a new initial character.

        Updates the initial character if the new value is different from the current one.

        Args:
            new_init_char (str): The new initial character.
        """
        if new_init_char == self.__init_char:
            return
        self.__init_char = new_init_char

    def set_end_line_character(self, new_end_char: str):
        """
        Set a new end line character.

        Updates the end line character if the new value is different from the current one.

        Args:
            new_end_char (str): The new end line character.
        """
        if new_end_char == self.__end_char:
            return
        self.__end_char = new_end_char

    @staticmethod
    def baud_rates() -> list[str]:
        """
        Get the list of available baud rates.

        Returns:
            list[str]: A list of available baud rates as strings.
        """
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
        """
        Get the list of available serial ports.

        Returns:
            list[str]: A list of available serial ports as strings.
        """
        ports = list_ports.comports()
        return [port.device for port in ports]

    @staticmethod
    def initial_characters() -> dict[str, str]:
        """
        Get the dictionary of initial characters.

        Returns:
            dict[str, str]: A dictionary mapping initial character names to their corresponding characters.
        """
        return {
            "None": "",
            "Start of Text (STX)": "\x02",
            "Start of Header (SOH)": "\x01",
            "Escape (ESC)": "\x1B",
        }

    @staticmethod
    def end_line_characters() -> dict[str, str]:
        """
        Get the dictionary of end line characters.

        Returns:
            dict[str, str]: A dictionary mapping end line character names to their corresponding characters.
        """
        return {
            "No Line Ending": "",
            "Newline": "\n",
            "Carriage Return": "\r",
            "Both NL & CR": "\r\n",
        }
