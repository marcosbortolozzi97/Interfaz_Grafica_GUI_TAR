import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class PanelParametros(ttk.LabelFrame):
    """
    Panel para configurar los umbrales de histéresis del TAR.
    Incluye:
    - Validación de rangos
    - Bloqueo de campos al aplicar
    - Envío de parámetros a MainWindow
    """

    def __init__(self, parent, on_apply_params_callback=None):
        super().__init__(parent, text="Parámetros", padding=10)

        self.MIN_VALUE = 0
        self.MAX_VALUE = 5000
        self.bloqueado = False
        self.on_apply_params_callback = on_apply_params_callback

        # Estado lógico del panel, umbrales inicialmente no aplicados
        self.parametros_aplicados = False 



        # ----------------------------------
        #   TÍTULO
        # ----------------------------------
        ttk.Label(
            self,
            text="Configuración de Ventanas de Histéresis",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=(0,5))

        # ----------------------------------
        #   UMBRALES CANAL A
        # ----------------------------------
        ttk.Label(self, text="Umbral CHA (mV):", font=("Arial", 9, "bold")).grid(
            row=1, column=0, sticky="w", pady=(5,0)
        )

        ttk.Label(self, text="Min:").grid(row=2, column=0, sticky="w")
        ttk.Label(self, text="Max:").grid(row=3, column=0, sticky="w")

        self.var_cha_min = tk.StringVar()
        self.var_cha_max = tk.StringVar()

        self.entry_cha_min = ttk.Entry(self, textvariable=self.var_cha_min, width=8)
        self.entry_cha_max = ttk.Entry(self, textvariable=self.var_cha_max, width=8)

        self.entry_cha_min.grid(row=2, column=1, padx=5)
        self.entry_cha_max.grid(row=3, column=1, padx=5)

        ttk.Label(self, text="mV").grid(row=2, column=2)
        ttk.Label(self, text="mV").grid(row=3, column=2)

        # ----------------------------------
        #   UMBRALES CANAL B
        # ----------------------------------
        ttk.Label(self, text="Umbral CHB (mV):", font=("Arial", 9, "bold")).grid(
            row=4, column=0, sticky="w", pady=(5,0)
        )

        ttk.Label(self, text="Min:").grid(row=5, column=0, sticky="w")
        ttk.Label(self, text="Max:").grid(row=6, column=0, sticky="w")

        self.var_chb_min = tk.StringVar()
        self.var_chb_max = tk.StringVar()

        self.entry_chb_min = ttk.Entry(self, textvariable=self.var_chb_min, width=8)
        self.entry_chb_max = ttk.Entry(self, textvariable=self.var_chb_max, width=8)

        self.entry_chb_min.grid(row=5, column=1, padx=5)
        self.entry_chb_max.grid(row=6, column=1, padx=5)

        ttk.Label(self, text="mV").grid(row=5, column=2)
        ttk.Label(self, text="mV").grid(row=6, column=2)

        # ----------------------------------
        #   BOTÓN APLICAR
        # ----------------------------------
        self.btn_apply = ttk.Button(self, text="Aplicar parámetros", command=self._aplicar)
        self.btn_apply.grid(row=7, column=0, columnspan=3, pady=5)

        # Configuración de columnas
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # Detectar cambios para invalidar parámetros aplicados
        self.var_cha_min.trace_add("write", self._on_param_change)
        self.var_cha_max.trace_add("write", self._on_param_change)
        self.var_chb_min.trace_add("write", self._on_param_change)
        self.var_chb_max.trace_add("write", self._on_param_change)



    # ============================================================
    #                 VALIDAR Y APLICAR
    # ============================================================
    def _aplicar(self):
        """Valida todos los campos y aplica parámetros si son correctos."""

        try:
            A_min = int(self.var_cha_min.get())
            A_max = int(self.var_cha_max.get())
            B_min = int(self.var_chb_min.get())
            B_max = int(self.var_chb_max.get())
        except ValueError:
            messagebox.showerror("Error", "Los campos son obligatorios y deben ser de tipo numérico.")
            return

        errores = []

        # Validación individual
        if not (self.MIN_VALUE <= A_min <= self.MAX_VALUE):
            errores.append("CHA Min fuera de rango.")
        if not (self.MIN_VALUE <= A_max <= self.MAX_VALUE):
            errores.append("CHA Max fuera de rango.")
        if not (self.MIN_VALUE <= B_min <= self.MAX_VALUE):
            errores.append("CHB Min fuera de rango.")
        if not (self.MIN_VALUE <= B_max <= self.MAX_VALUE):
            errores.append("CHB Max fuera de rango.")

        # Validación lógica
        if A_min >= A_max:
            errores.append("CHA Min debe ser < CHA Max.")
        if B_min >= B_max:
            errores.append("CHB Min debe ser < CHB Max.")

        if errores:
            messagebox.showerror("Error en parámetros", "\n".join(errores))
            return

        # Si está todo OK se envian parámetros al MainWindow
        params = {
            "umbral_cha_min": A_min,
            "umbral_cha_max": A_max,
            "umbral_chb_min": B_min,
            "umbral_chb_max": B_max
        }

        print("[PanelParametros] Parámetros OK:", params)

        if self.on_apply_params_callback:
            self.on_apply_params_callback(params)
        
        # Parametros correctamente aplicados
        self.parametros_aplicados = True

        # Bloquear entradas
        self.bloquear(True)


    # ============================================================
    #                     BLOQUEAR / DESBLOQUEAR
    # ============================================================
    def bloquear(self, flag: bool):
        """Deshabilita todos los campos luego de aplicar parámetros."""
        self.bloqueado = flag
        state = "disabled" if flag else "normal"

        for widget in [
            self.entry_cha_min, self.entry_cha_max,
            self.entry_chb_min, self.entry_chb_max,
            self.btn_apply
        ]:
            widget.config(state=state)

        print(f"[PanelParametros] Bloqueado = {flag}")



    # ============================================================
    #         DETECTAR CAMBIO EN PARÁMETROS
    # ============================================================
    def _on_param_change(self, *args):
        if self.parametros_aplicados:
            self.parametros_aplicados = False
            print("[PanelParametros] Parámetros modificados → requieren reaplicar")
