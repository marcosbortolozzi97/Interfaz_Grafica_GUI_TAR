import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports


class SerialPanel(ttk.LabelFrame):
    """
    Panel lateral encargado exclusivamente de:
    - listar puertos serie disponibles,
    - permitir selección,
    - solicitar conexión/desconexión mediante callbacks,
    - mostrar el estado actual.
    """

    def __init__(self, parent, on_connect_callback, on_disconnect_callback):
        super().__init__(parent, text="Puertos", padding=5)

        self.on_connect = on_connect_callback
        self.on_disconnect = on_disconnect_callback

        # ---------------------------------------------------------
        # Título
        # ---------------------------------------------------------
        ttk.Label(
            self,
            text="Conexión Serie/USB",
            font=("Arial", 11, "bold"),
        ).pack(pady=(0, 5))

        # ---------------------------------------------------------
        # Selección de puertos disponibles
        # ---------------------------------------------------------
        ports_frame = ttk.Frame(self)
        ports_frame.pack(fill="x")

        ttk.Label(ports_frame, text="Puerto COM:").pack(side="left")

        self.port_var = tk.StringVar()
        self.combo_ports = ttk.Combobox(
            ports_frame,
            textvariable=self.port_var,
            state="readonly",
            width=20
        )
        self.combo_ports.pack(side="left", padx=5)

        refresh_btn = ttk.Button(
            ports_frame,
            text="↻",
            width=3,
            command=self.refresh_ports
        )
        refresh_btn.pack(side="left")

        # ---------------------------------------------------------
        # Botones conectar / desconectar
        # ---------------------------------------------------------
        btns_frame = ttk.Frame(self)
        btns_frame.pack(pady=10)

        self.btn_connect = ttk.Button(
            btns_frame,
            text="Conectar",
            command=self._connect
        )
        self.btn_connect.pack(side="left", padx=5)

        self.btn_disconnect = ttk.Button(
            btns_frame,
            text="Desconectar",
            state="disabled",
            command=self._disconnect
        )
        self.btn_disconnect.pack(side="left", padx=5)

        # ---------------------------------------------------------
        # Estado visual
        # ---------------------------------------------------------
        self.status_var = tk.StringVar(value="Estado: Desconectado")
        ttk.Label(self, textvariable=self.status_var).pack(pady=5)

        # cargar listado inicial
        self.refresh_ports()

    # =========================================================================
    # Actualización de puertos disponibles
    # =========================================================================
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        ports_list = [p.device for p in ports]

        self.combo_ports["values"] = ports_list
        if ports_list:
            self.combo_ports.current(0)
        else:
            self.port_var.set("")

    # =========================================================================
    # Conectar / desconectar
    # =========================================================================
    def _connect(self):
        port = self.port_var.get()

        if not port:
            self.status_var.set("Estado: No hay puerto seleccionado")
            return

        ok = self.on_connect(port)

        if ok:
            self.status_var.set(f"Estado: Conectado a {port}")
            self.btn_connect["state"] = "disabled"
            self.btn_disconnect["state"] = "normal"
        else:
            self.status_var.set("Estado: Error al conectar")

    def _disconnect(self):
        self.on_disconnect()

        self.status_var.set("Estado: Desconectado")
        self.btn_connect["state"] = "normal"
        self.btn_disconnect["state"] = "disabled"


