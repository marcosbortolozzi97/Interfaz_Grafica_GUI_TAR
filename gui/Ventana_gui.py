import tkinter as tk
from tkinter import ttk
from gui.Panel_Serial import SerialPanel
from core.recibir_datos import RecibirDatos
from core.procesar_datos import ProcesaDatosTAR
from gui.Panel_Ensayo import PanelEnsayo
from gui.Panel_Parametros import PanelParametros
from gui.Panel_Histograma import PanelHistograma

from datetime import datetime
import os, time
from pathlib import Path

BASE_DATA_DIR = Path.home() / "Documents" / "TAR_GUI"
ENSAYOS_DIR = BASE_DATA_DIR / "ensayos"

ENSAYOS_DIR.mkdir(parents=True, exist_ok=True)

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TAR GUI")
        self.state('zoomed')

        # Procesador TAR con auto-guardado (carpetas se reasignan al iniciar un ensayo)
        self.process = ProcesaDatosTAR(
            carpeta_bin=None,
            carpeta_csv=None,
            auto_periodo_seg=None,
            auto_prefix="tar"
        )


        # Serial handler (Manejo de los datos serie)
        self.serial_handler = RecibirDatos(
            on_data_callback=self.on_serial_data,
            on_error_callback=self.on_serial_error
        )

        #  Organizacion UI
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # --------------------------------------------
        # PANEL GRÁFICO IZQUIERDO 
        # --------------------------------------------
        left_panel = ttk.Frame(container)
        left_panel.grid(row=0, column=0, sticky="n")

        ttk.Label(
            left_panel, text="PANEL DE CONTROL",
            font=("Arial", 13, "bold")
        ).pack(pady=5, padx=100, anchor="center")

        left_inner = ttk.Frame(left_panel)
        left_inner.pack(expand=True)

        # Panel de conexión serie
        serial_panel = SerialPanel(
            left_inner,
            on_connect_callback=self.connect_serial,
            on_disconnect_callback=self.disconnect_serial
        )
        serial_panel.pack()

        # Panel parámetros TAR
        self.param_panel = PanelParametros(
            left_inner,
            on_apply_params_callback=self._aplicar_parametros
        )
        self.param_panel.pack(pady=5, fill="x")

        # Panel manejo de ensayos
        self.ensayo_panel = PanelEnsayo(
            left_inner,
            on_iniciar_callback=self.iniciar_ensayo,
            on_finalizar_callback=self.finalizar_ensayo,
            on_cargar_crudo_callback=self.cargar_crudo_viejo,
            on_limpiar_callback=self.limpiar_datos,
            validar_inicio_callback=self._validar_inicio_ensayo
        )
        self.ensayo_panel.pack(pady=5)


        # Panel Ensayo para las validaciones cruzadas
        self.ensayo_panel.check_parametros = lambda: self.param_panel.parametros_aplicados
        self.ensayo_panel.check_puerto = lambda: self.serial_handler.is_connected()


        # --------------------------------------------
        # PANEL GRÁFICO DERECHO
        # --------------------------------------------
        right_panel = ttk.Frame(container)
        right_panel.grid(row=0, column=1, sticky="nsew")

        ttk.Label(
            right_panel, text="GRÁFICAS",
            font=("Arial", 13, "bold")
        ).pack(pady=5, padx=10, anchor="center")

        # Panel manejo de histogramas
        self.hist_panel = PanelHistograma(
            right_panel,
            procesador_datos=self.process,
            update_ms=300
        )
        self.hist_panel.pack(fill="both", expand=True)

        # Variables internas
        self.ensayo_activo = False
        self._last_ind = 0


    # ==============================================
    # Conectar / desconectar puerto serie
    # ==============================================
    def connect_serial(self, port):
        print(f"[GUI] Intentando conectar a {port}")
        ok = self.serial_handler.open(port)
        if ok:
            print(f"[GUI] Conectado correctamente a {port}")
        else:
            print("[GUI] Error al conectar")
        return ok

    def disconnect_serial(self):
        print("[GUI] Desconectando...")
        self.serial_handler.close()


    # ==============================================
    # Manejo del ensayo
    # ==============================================
    def iniciar_ensayo(self, duracion_seg):
        # Crear carpeta del ensayo
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = ENSAYOS_DIR / f"ensayo_{fecha}"
        ruta_csv = base / "csv"
        ruta_bin = base / "bin"

        # ProcesaDatosTAR guardará automáticamente ahí
        self.process.set_output_folders(
            carpeta_csv=str(ruta_csv),
            carpeta_bin=str(ruta_bin)
        )

        # Configurar auto-guardado cada 15 segundos
        self.process.auto_periodo_seg = 15
        self.process._ultimo_guardado_ts = time.time()
        self.process._start_auto_loop()

        # Variables internas
        self.ensayo_duracion = duracion_seg
        self.ensayo_restante = duracion_seg
        self.ensayo_activo = True
        self._last_ind = 0

        # Limpiar buffers previos
        self.process.clear()

        # Actualizar UI
        self.ensayo_panel.var_estado.set(f"Corriendo ({self.ensayo_restante}s)")
        self.ensayo_panel.boton_iniciar.config(state="disabled")
        self.ensayo_panel.boton_finalizar.config(state="normal")
        self.hist_panel.bloquear(True)
        self.param_panel.bloquear(True)
        self.ensayo_panel.bloquear_duracion(True)

        # Ordenar inicio al hardware
        if self.serial_handler:
            self.serial_handler.iniciar_captura()

        # Inicia ticker de UI
        self.after(1000, self._tick_ensayo)


    def _tick_ensayo(self):
        if not self.ensayo_activo:
            return

        self.ensayo_restante -= 1

        if self.ensayo_restante <= 0:
            self.finalizar_ensayo()
            return

        self.ensayo_panel.var_estado.set(
            f"Corriendo ({self.ensayo_restante}s restantes)"
        )
        self.after(1000, self._tick_ensayo)


    def finalizar_ensayo(self):
        self.ensayo_activo = False

        # Ordenar STOP al hardware
        if self.serial_handler:
            self.serial_handler.detener_captura()
        
        # Detener autoguardado para evitar condiciones de carrera
        self.process.stop_auto()

        # Guardado final (ProcesaDatosTAR guarda archivos dentro del ensayo actual)
        print("[GUI] Guardando dump final...")
        self.process.dump_and_reset()

        # Restaurar UI
        self.ensayo_panel.boton_iniciar.config(state="normal")
        self.ensayo_panel.boton_finalizar.config(state="disabled")
        self.hist_panel.bloquear(False)
        self.param_panel.bloquear(False)
        self.ensayo_panel.bloquear_duracion(False)
        self.ensayo_panel.var_estado.set("Ensayo finalizado")


    # ==============================================
    # Callbacks del SerialHandler
    # ==============================================
    def on_serial_data(self, data: bytes):
        # Enviar datos al parser
        self.process.feed(data)

        # Actualización rápida de gráficos
        total = self.process.total_registros()
        if total - self._last_ind >= 50:
            nuevos = self.process.registros_nuevos_desde(self._last_ind)
            self._last_ind = total
            try:
                self.hist_panel.procesar_nuevos_registros(nuevos)
            except Exception:
                pass

    def on_serial_error(self, msg: str):
        print(f"[ERROR] {msg}")


    # ==============================================
    # Reprocesado y limpieza
    # ==============================================
    def cargar_crudo_viejo(self):
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Seleccionar archivo binario TAR",
            initialdir=str(ENSAYOS_DIR),
            filetypes=[("Binarios TAR", "*.bin")]
        )

        if not filename:
            return

        print("[GUI] Reprocesando crudo:", filename)
        self.process.load_raw_and_reprocesar(filename)

        try:
            self.hist_panel.refrescar_completo()
        except Exception:
            pass

    def limpiar_datos(self):
        self.process.clear()
        print("[GUI] Datos limpiados.")


    # ==============================================
    # Aplicar parámetros al TAR
    # ==============================================
    def _aplicar_parametros(self, params):
        A_min = params["umbral_cha_min"]
        A_max = params["umbral_cha_max"]
        B_min = params["umbral_chb_min"]
        B_max = params["umbral_chb_max"]

        print(f"[MainWindow] Aplicando parámetros: {params}")

        if not self.serial_handler:
            print("[MainWindow] SerialHandler no inicializado")
            return

        # Envío ASCII simple al firmware
        self.serial_handler.send(f"UMBRAL CHA_MIN {A_min}\n".encode())
        self.serial_handler.send(f"UMBRAL CHA_MAX {A_max}\n".encode())
        self.serial_handler.send(f"UMBRAL CHB_MIN {B_min}\n".encode())
        self.serial_handler.send(f"UMBRAL CHB_MAX {B_max}\n".encode())

        print("[MainWindow] Parámetros enviados correctamente al TAR.")
        try:
            self.param_panel.bloquear(True)
        except Exception:
            pass


    # ==============================================
    # Se valida las condiciones para iniciar un ensayo
    # ==============================================

    def _validar_inicio_ensayo(self):
        """
        Valida si el ensayo puede iniciarse.
        Retorna (True, "") si todo está OK.
        Retorna (False, mensaje) si hay algún problema.
        """

        # 1. Puerto serie conectado
        if not self.serial_handler or not self.serial_handler.is_connected():
            return False, "No hay ningún puerto COM conectado."

        # 2. Parámetros aplicados
        if not getattr(self.param_panel, "parametros_aplicados", False):
            return False, "Los parámetros de umbral no fueron aplicados."

        # 3. Todo OK
        return True, ""


    


