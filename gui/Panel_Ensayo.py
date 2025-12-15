
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox



class PanelEnsayo(ttk.LabelFrame):
    """
    Panel que controla:
     - Duración del ensayo (segundos)
     - Iniciar / finalizar ensayo
     - Procesar binario previo
     - Limpiar datos
    """

    def __init__(
        self,
        parent,
        on_iniciar_callback=None,
        on_finalizar_callback=None,
        on_cargar_crudo_callback=None,
        on_limpiar_callback=None,
        validar_inicio_callback=None
    ):
        super().__init__(parent, text="Ensayo", padding=5)

        # Guardamos callbacks
        self.on_iniciar = on_iniciar_callback
        self.on_finalizar = on_finalizar_callback
        self.on_cargar_crudo = on_cargar_crudo_callback
        self.on_limpiar = on_limpiar_callback
        self.validar_inicio = validar_inicio_callback


        # ---------------------------
        #     TÍTULO DEL PANEL
        # ---------------------------
        ttk.Label(
            self,
            text="Control del Ensayo",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0,5))

        # ----------------------------------
        #   DURACION DEL ENSAYO [seg]
        # ----------------------------------
        ttk.Label(self, text="Duración del ensayo (seg):").grid(row=1, column=0, sticky="w")

        self.var_duracion = tk.StringVar(value="")
        self.entry_duracion = ttk.Entry(self, textvariable=self.var_duracion, width=8)
        self.entry_duracion.grid(row=1, column=1, sticky="w", padx=5)

        # ---------------------------
        #     BOTÓN: INICIAR
        # ---------------------------
        self.boton_iniciar = ttk.Button(
            self,
            text="Iniciar ensayo",
            command=self._iniciar
        )
        self.boton_iniciar.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

        # ---------------------------
        #     BOTÓN: FINALIZAR
        # ---------------------------
        self.boton_finalizar = ttk.Button(
            self,
            text="Finalizar ensayo",
            command=self._finalizar
        )
        self.boton_finalizar.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        # ---------------------------
        #   BOTÓN: CARGAR CRUDO
        # ---------------------------
        self.boton_crudo = ttk.Button(
            self,
            text="Procesar binario previo",
            command=self._cargar_crudo
        )
        self.boton_crudo.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")

        # ---------------------------
        #     BOTÓN: LIMPIAR
        # ---------------------------
        self.boton_limpiar = ttk.Button(
            self,
            text="Limpiar datos",
            command=self._limpiar
        )
        self.boton_limpiar.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")

        # ----------------------------
        #       ETIQUETA DE ESTADO
        # ----------------------------
        ttk.Label(self, text="Estado:").grid(row=6, column=0, sticky="w", padx=(20,0), pady=(8,0))

        self.var_estado = tk.StringVar(value="—")
        self.lbl_estado = ttk.Label(self, textvariable=self.var_estado)
        self.lbl_estado.grid(row=6, column=1, sticky="w", padx=(0,20), pady=(8,0))

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    # ======================================================
    #    MÉTODOS INTERNOS — llamados por botones
    # ======================================================

    def _iniciar(self):
        """Callback al presionar 'Iniciar ensayo'."""

        # ---------------------------
        # Validar duración
        # ---------------------------
        duracion = self.var_duracion.get()
        try:
            dur = int(duracion)
            if dur <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Duración inválida",
                "La duración del ensayo debe ser un entero positivo (en segundos)."
            )
            return

        # -------------------------
        # Validación cruzada (GUI)
        # -------------------------
        if hasattr(self, "validar_inicio_callback") and self.validar_inicio_callback:
            ok, msg = self.validar_inicio_callback()
            if not ok:
                messagebox.showwarning("No se puede iniciar el ensayo", msg)
                return

        # ---------------------------
        # Validar condiciones externas
        # ---------------------------
        if self.validar_inicio:
            ok, msg = self.validar_inicio()
            if not ok:
                messagebox.showwarning("No se puede iniciar ensayo", msg)
                return

        # ---------------------------
        # Iniciar ensayo
        # ---------------------------
        self.var_estado.set(f"Iniciando ({dur} s)...")

        if self.on_iniciar:
            self.on_iniciar(dur)


    def _finalizar(self):
        if self.on_finalizar:
            self.on_finalizar()
        self.var_estado.set("Ensayo finalizado")

    def _cargar_crudo(self):
        if self.on_cargar_crudo:
            self.on_cargar_crudo()
        self.var_estado.set("Procesando binario previo...")

    def _limpiar(self):
        if self.on_limpiar:
            self.on_limpiar()
        self.var_estado.set("Registros limpios")

    def mostrar_histograma(self):
        if hasattr(self, "hist_panel"):
            self.hist_panel.actualizar_grafico()

    def bloquear_duracion(self, flag: bool):
        """ Bloquea / desbloquea la edición de la duración del ensayo."""
        state = "disabled" if flag else "normal"
        self.entry_duracion.config(state=state)
