import time
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror

from SerialConn import SerialConn


class SerialMonitor(tk.Tk):
    """
    A GUI application to monitor and send data through a serial connection.

    This class extends tk.Tk to create a window with controls for serial communication
    and a text area to display received messages.
    """
    def __init__(self):
        """
        Initialize the SerialMonitor application.

        This includes setting up the serial connection, creating the main window,
        and initializing UI components such as comboboxes, buttons, and text areas.
        """
        super().__init__()

        self.__serial_conn = SerialConn()
        self.__serial_conn.status_changed.connect(self.__on_status_changed)
        self.__serial_conn.error_occurred.connect(self.__on_error_occurred)

        self.__window()
        self.__connection_row()
        self.__message_row()
        self.__monitor_area()

        self.stop_event = threading.Event()
        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

        self.receive_thread = threading.Thread(target=self.receive_data)
        self.receive_thread.start()

    def __window(self):
        """
        Configure the main window of the application.

        Sets the title and geometry of the window.
        """
        self.title("Serial Monitor")
        self.geometry("800x400")

    def __connection_row(self):
        """
        Create the connection row UI components.

        This includes labels, comboboxes for selecting the serial port and baud rate,
        and a connect/disconnect button.
        """
        frame = tk.Frame(self)
        frame.pack()

        tk.Label(frame, text="Serial port:").pack(side="left")
        ports = SerialConn.available_ports()
        self.__port = tk.StringVar(value=ports[0])
        self.port_cb = ttk.Combobox(
            frame, textvariable=self.__port, values=SerialConn.available_ports()
        )
        self.port_cb.pack(side="left")
        self.port_cb.bind("<<ComboboxSelected>>", lambda _: self.__on_port_changed())

        tk.Label(frame, text="Baud rade:").pack(side="left")
        self.__baud_rate = tk.StringVar(value=self.__serial_conn.baud_rate)
        self.baud_rate_cb = ttk.Combobox(
            frame,
            textvariable=self.__baud_rate,
            values=SerialConn.baud_rates(),
        )
        self.baud_rate_cb.pack(side="left")
        self.baud_rate_cb.bind(
            "<<ComboboxSelected>>", lambda _: self.__on_baud_rate_changed()
        )

        self.btn_conn = ttk.Button(
            frame, text="Connect", command=self.__on_btn_conn_clicked
        )
        self.btn_conn.pack(side="left")

    def __message_row(self):
        """
        Create the message row UI components.

        This includes labels, comboboxes for selecting initial and end line characters,
        an entry for the message, and a send button.
        """
        frame = tk.Frame(self)
        frame.pack()

        tk.Label(frame, text="Initial character:").pack(side="left")
        init_chars = list(SerialConn.initial_characters().keys())
        self.__init_char = tk.StringVar(value=init_chars[0])
        self.init_char_cb = ttk.Combobox(
            frame,
            textvariable=self.__init_char,
            values=init_chars,
        )
        self.init_char_cb.pack(side="left")
        self.init_char_cb.bind(
            "<<ComboboxSelected>>", lambda _: self.__on_init_char_changed()
        )
        self.init_char_cb.state(["disabled"])

        tk.Label(frame, text="Message:").pack(side="left")
        self.msg_entry = ttk.Entry(frame)
        self.msg_entry.pack(side="left")
        self.msg_entry.bind("<Return>", lambda _: self.__on_send_message())
        self.msg_entry.state(["disabled"])

        tk.Label(frame, text="End line character:").pack(side="left")
        end_line_chars = list(SerialConn.end_line_characters().keys())
        self.__end_line_char = tk.StringVar(value=end_line_chars[0])
        self.end_line_char_cb = ttk.Combobox(
            frame,
            textvariable=self.__end_line_char,
            values=end_line_chars,
        )
        self.end_line_char_cb.pack(side="left")
        self.end_line_char_cb.bind(
            "<<ComboboxSelected>>", lambda _: self.__on_end_line_char_changed()
        )
        self.end_line_char_cb.state(["disabled"])

        self.btn_send = ttk.Button(frame, text="Send", command=self.__on_send_message)
        self.btn_send.pack(side="right")
        self.btn_send.state(["disabled"])

    def __monitor_area(self):
        """
        Create the monitor area UI components.

        This includes a text area to display received messages and a scrollbar.
        """
        self.text_area = tk.Text(self, wrap="none")
        self.text_area.pack(expand=True, fill="both")

        self.scrollbar = tk.Scrollbar(self, command=self.text_area.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.text_area.config(yscrollcommand=self.scrollbar.set)

    def receive_data(self):
        """
        Continuously receive data from the serial connection and display it in the text area.

        This method runs in a separate thread and updates the text area with received data.
        """
        while not self.stop_event.is_set():
            time.sleep(0.1)
            if not self.__serial_conn.status:
                continue
            try:
                data = self.__serial_conn.on_read_response()
                if len(data) == 0:
                    continue
                self.text_area.insert(tk.END, data + "\n")
                self.text_area.see(tk.END)
            except Exception as e:
                print(f"Error receiving data: {e}")

    def __on_closing(self):
        """
        Handle the window closing event.

        Closes the serial connection, stops the data receiving thread, and destroys the window.
        """
        self.__serial_conn.close_conn()
        self.stop_event.set()
        self.receive_thread.join()
        self.destroy()

    def __on_port_changed(self):
        """
        Handle the event when the selected serial port changes.

        Updates the serial connection with the new port.
        """
        self.__serial_conn.port = self.__port.get()

    def __on_baud_rate_changed(self):
        """
        Handle the event when the selected baud rate changes.

        Updates the serial connection with the new baud rate.
        """
        self.__serial_conn.baud_rate = self.__baud_rate.get()

    def __on_btn_conn_clicked(self):
        """
        Handle the event when the connect/disconnect button is clicked.

        Toggles the connection status and updates the button text accordingly.
        """
        if self.__serial_conn.status:
            self.__serial_conn.close_conn()
        else:
            self.__serial_conn.start_conn()
        self.btn_conn.configure(
            text="Disconnect" if self.__serial_conn.status else "Connect"
        )

    def __on_init_char_changed(self):
        """
        Handle the event when the selected initial character changes.

        Updates the serial connection with the new initial character.
        """
        self.__serial_conn.set_initial_character(self.__init_char.get())

    def __on_end_line_char_changed(self):
        """
        Handle the event when the selected end line character changes.

        Updates the serial connection with the new end line character.
        """
        self.__serial_conn.set_end_line_character(self.__end_line_char.get())

    def __on_send_message(self):
        """
        Handle the event when the send message button is clicked.

        Sends the message entered in the message entry to the serial connection.
        """
        msg = self.msg_entry.get()
        if not msg:
            return
        self.__serial_conn.send_msg(msg)
        self.msg_entry.delete(0, tk.END)

    def __on_status_changed(self, _):
        """
        Handle the event when the status of the serial connection changes.

        Updates the UI components to reflect the new connection status.
        """
        status = self.__serial_conn.status
        self.btn_conn.configure(text="Disconnect" if status else "Connect")
        self.port_cb.state(["disabled" if status else "!disabled"])
        self.baud_rate_cb.state(["disabled" if status else "!disabled"])
        self.init_char_cb.state(["!disabled" if status else "disabled"])
        self.msg_entry.state(["!disabled" if status else "disabled"])
        self.end_line_char_cb.state(["!disabled" if status else "disabled"])
        self.btn_send.state(["!disabled" if status else "disabled"])

    def __on_error_occurred(self, **kwargs):
        """
        Handle the event when an error occurs in the serial connection.

        Displays an error message dialog with the exception details.
        """
        if "exp" not in kwargs:
            return
        showerror("Error", kwargs["exp"])
