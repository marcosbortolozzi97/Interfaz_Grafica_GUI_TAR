import tkinter as tk
from tkinter import ttk
from core.procesar_datos import ProcesaDatosTAR

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
#   HISTOGRAMA INDIVIDUAL (UNO POR CANAL: A, B)
# ============================================================
class PanelHistogramaIndividual(ttk.LabelFrame):

    def __init__(self, parent, procesador_datos, canal, update_ms=300):
        titulo = "Histograma Canal A" if canal == 0 else "Histograma Canal B"
        super().__init__(parent, text=titulo, padding=5)

        self.canal = canal
        self.process = procesador_datos
        self.update_ms = update_ms
        self.last_index = 0
        self.bloqueado = False

        # ==================================================
        # Configuración superior
        # ==================================================
        cfg = ttk.Frame(self)
        cfg.pack(fill="x", pady=5)

        ttk.Label(cfg, text="Min (mV):").grid(row=0, column=0, padx=5)
        ttk.Label(cfg, text="Max (mV):").grid(row=0, column=2, padx=5)
        ttk.Label(cfg, text="Intervalo (mV):").grid(row=0, column=4, padx=5)

        self.var_min = tk.StringVar(value="")
        self.var_max = tk.StringVar(value="") 
        self.var_bin = tk.StringVar(value="")

        self.entry_min = ttk.Entry(cfg, textvariable=self.var_min, width=6)
        self.entry_max = ttk.Entry(cfg, textvariable=self.var_max, width=6)
        self.entry_bin = ttk.Entry(cfg, textvariable=self.var_bin, width=6)

        self.entry_min.grid(row=0, column=1, padx=5)
        self.entry_max.grid(row=0, column=3, padx=5)
        self.entry_bin.grid(row=0, column=5, padx=5)

        self.btn_aplicar = ttk.Button(cfg, text="Aplicar", command=self.aplicar)
        self.btn_borrar  = ttk.Button(cfg, text="Borrar", command=self.limpiar)

        self.btn_aplicar.grid(row=0, column=6, padx=10)
        self.btn_borrar.grid(row=0, column=7, padx=5)

        # ==================================================
        # Figura Matplotlib
        # ==================================================
        self.fig = Figure(figsize=(5, 4), dpi=50)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Amplitud (mV)", fontsize=13)
        self.ax.set_ylabel("Frecuencia", fontsize=13)
        self.ax.tick_params(axis='both', labelsize=11)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Timer de refresco
        self.after(self.update_ms, self._update_plot)

    # ==================================================
    # Métodos funcionales
    # ==================================================
    def aplicar(self):
        if not self.bloqueado:
            self.last_index = 0
            self._recalcular()

    def limpiar(self):
        self.last_index = 0
        self.ax.cla()

        self.ax.set_xlabel("Amplitud (mV)", fontsize=13)
        self.ax.set_ylabel("Frecuencia", fontsize=13)
        self.ax.tick_params(axis='both', labelsize=11)

        self.canvas.draw()


    def _bloquear(self, flag: bool):
        self.bloqueado = flag
        state = "disabled" if flag else "normal"

        self.entry_min.config(state=state)
        self.entry_max.config(state=state)
        self.entry_bin.config(state=state)
        self.btn_aplicar.config(state=state)
        self.btn_borrar.config(state=state)

    # ==================================================
    # Actualización periódica
    # ==================================================
    def _update_plot(self):
        nuevos = self.process.registros_nuevos_desde(self.last_index)
        self.last_index += len(nuevos)

        if nuevos and not self.bloqueado:
            self._recalcular()

        self.after(self.update_ms, self._update_plot)

    # ==================================================
    # Cálculo del histograma
    # ==================================================
    def _recalcular(self):
        registros = self.process.registros
        if not registros:
            return

        try:
            minv = int(self.var_min.get())
            maxv = int(self.var_max.get())
            bin_size = int(self.var_bin.get())
        except ValueError:
            return

        if bin_size <= 0 or minv >= maxv:
            return

        bins = list(range(minv, maxv + bin_size, bin_size))

        # Filtrar solo el canal correspondiente
        vals = [
            r["vp"] for r in registros
            if r.get("chan") == self.canal and "error" not in r
        ]

        self.ax.cla()
        titulo = "Histograma Canal A" if self.canal == 0 else "Histograma Canal B"
        # No hay título interno
        self.ax.set_xlabel("Amplitud (mV)", fontsize=13)
        self.ax.set_ylabel("Frecuencia", fontsize=13)
        self.ax.tick_params(axis='both', labelsize=11)


        if vals:
            self.ax.hist(vals, bins=bins, alpha=0.8)

        self.canvas.draw()


# ============================================================
#   PANEL GENERAL, CONTIENE LOS DOS HISTOGRAMAS (A y B)
# ============================================================
class PanelHistograma(ttk.Frame):

    def __init__(self, parent, procesador_datos, update_ms=300):
        super().__init__(parent)

        self.hist_A = PanelHistogramaIndividual(
            self, procesador_datos, canal=0, update_ms=update_ms
        )
        self.hist_A.pack(fill="both", expand=True, pady=5)

        self.hist_B = PanelHistogramaIndividual(
            self, procesador_datos, canal=1, update_ms=update_ms
        )
        self.hist_B.pack(fill="both", expand=True, pady=5)

    # Permite que MainWindow bloquee ambos al iniciar ensayo
    def bloquear(self, flag: bool):
        self.hist_A._bloquear(flag)
        self.hist_B._bloquear(flag)
