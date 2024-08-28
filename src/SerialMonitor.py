import time
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror

from SerialConn import SerialConn


class SerialMonitor(tk.Tk):
    def __init__(self):
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
        self.title("Serial Monitor")
        self.geometry("800x400")

    def __connection_row(self):
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
        self.text_area = tk.Text(self, wrap="none")
        self.text_area.pack(expand=True, fill="both")

        self.scrollbar = tk.Scrollbar(self, command=self.text_area.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.text_area.config(yscrollcommand=self.scrollbar.set)

    def receive_data(self):
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
        self.stop_event.set()
        self.receive_thread.join()
        self.__serial_conn.close_conn()
        self.destroy()

    def __on_port_changed(self):
        self.__serial_conn.port = self.__port.get()

    def __on_baud_rate_changed(self):
        self.__serial_conn.baud_rate = self.__baud_rate.get()

    def __on_btn_conn_clicked(self):
        if self.__serial_conn.status:
            self.__serial_conn.close_conn()
        else:
            self.__serial_conn.start_conn()
        self.btn_conn.configure(
            text="Disconnect" if self.__serial_conn.status else "Connect"
        )

    def __on_init_char_changed(self):
        self.__serial_conn.set_initial_character(self.__init_char.get())

    def __on_end_line_char_changed(self):
        self.__serial_conn.set_end_line_character(self.__end_line_char.get())

    def __on_send_message(self):
        msg = self.msg_entry.get()
        if not msg:
            return
        self.__serial_conn.send_msg(msg)

    def __on_status_changed(self, _):
        status = self.__serial_conn.status
        self.btn_conn.configure(text="Disconnect" if status else "Connect")
        self.port_cb.state(["disabled" if status else "!disabled"])
        self.baud_rate_cb.state(["disabled" if status else "!disabled"])
        self.init_char_cb.state(["!disabled" if status else "disabled"])
        self.msg_entry.state(["!disabled" if status else "disabled"])
        self.end_line_char_cb.state(["!disabled" if status else "disabled"])
        self.btn_send.state(["!disabled" if status else "disabled"])

    def __on_error_occurred(self, **kwargs):
        if "exp" not in kwargs:
            return
        showerror("Error", kwargs["exp"])
