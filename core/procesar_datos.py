
from typing import Callable, Dict, List, Optional, Tuple
import os
import csv
import threading
import time

# ============================================================
#   DEFINICIONES DEL PROTOCOLO TAR (firmware real — 8 bytes)
# ============================================================
FRAME_SIZE = 8                    # Tamaño fijo de frame
T_PERIOD = 0xFFFFFFFF             # Para eventos CH=3

# Máscaras del firmware real (binToCSV.h)
MSK_HEADER = 0xFF00000000000000
MSK_TS     = 0x00FFFFFFFF000000
MSK_CH     = 0x0000000000C00000
MSK_VP     = 0x00000000003FFF00
MSK_FOOTER = 0x00000000000000FF

OFF_TS = 24
OFF_CH = 22
OFF_VP = 8

# Definición de la resolución 
ZMODADC1410_RESOLUTION = 3.21 # mv

# ====================================================================
#                       CLASE PROCESAR
# ====================================================================
class ProcesaDatosTAR:
    """
    Procesador a TAR real adaptado a la GUI. Gestiona la recepción de frames de 8 bytes (big-endian),
    el autoguardado, y la conversión de BIN a CSV.
    """

    def __init__(
        self,
        carpeta_bin: str = "data/bin",
        carpeta_csv: str = "data/csv",
        auto_prefix: str = "tar",
        interpretar_frame: Optional[Callable[[bytes], Dict]] = None,
        auto_periodo_seg: Optional[int] = None,
    ):
        # Interpretador 
        self.interpretar_frame = interpretar_frame or self._interpretador_TAR

        # Buffers internos
        self._buffer = bytearray()
        self.registros: List[Dict] = []
        self._raw_frames: List[bytes] = []
        self._offset = 0  # offset acumulado por CH=3


        # Lock para concurrencia
        self._lock = threading.Lock()

        # Carpetas raíz
        self.carpeta_bin_root = carpeta_bin
        self.carpeta_csv_root = carpeta_csv
        self.carpeta_bin = None
        self.carpeta_csv = None

        if carpeta_bin:
            os.makedirs(carpeta_bin, exist_ok=True)
            self.carpeta_bin = carpeta_bin

        if carpeta_csv:
            os.makedirs(carpeta_csv, exist_ok=True)
            self.carpeta_csv = carpeta_csv

        # Prefijo por defecto
        self.auto_prefix = auto_prefix

        # Guardado automático interno
        self.auto_periodo_seg = auto_periodo_seg
        self._auto_running = False
        self._auto_thread: Optional[threading.Thread] = None
        self._ultimo_guardado_ts = time.time()

        if self.auto_periodo_seg and self.auto_periodo_seg > 0:
            self._start_auto_loop()

    # -------------------------
    # Métodos públicos de configuración
    # -------------------------
    def set_output_folders(self, carpeta_csv: str, carpeta_bin: str):
        """Configura carpetas de salida al iniciar el ensayo, y cada 15 segundos."""
        self.carpeta_csv = carpeta_csv
        self.carpeta_bin = carpeta_bin
        os.makedirs(self.carpeta_csv, exist_ok=True)
        os.makedirs(self.carpeta_bin, exist_ok=True)

    def set_auto_prefix(self, prefix: str):
        self.auto_prefix = prefix

    def _start_auto_loop(self):
        """Inicia hilo que ejecuta dump_and_reset periódicamente."""
        if self._auto_running:
            return
        self._auto_running = True
        self._auto_thread = threading.Thread(target=self._auto_loop, daemon=True)
        self._auto_thread.start()

    def stop_auto(self):
        """Detiene el autoguardado interno."""
        self._auto_running = False
        if self._auto_thread:
            self._auto_thread.join(timeout=1.0)
            self._auto_thread = None

    def _auto_loop(self):
        """Bucle interno para el autoguardado."""
        while self._auto_running:
            time.sleep(1)
            if time.time() - self._ultimo_guardado_ts >= self.auto_periodo_seg:
                print(f"[AutoSave] Guardando datos parciales ({self.auto_prefix})...")
                self.dump_and_reset(prefix=f"{self.auto_prefix}_part")
                self._ultimo_guardado_ts = time.time()

    # -------------------------
    # Alimentación desde puerto serie
    # -------------------------
    def feed(self, data: bytes):
        """Alimentar con bytes crudos desde RecibirDatos."""
        if not data:
            return

        with self._lock:
            self._buffer.extend(data)
            self._extraer_frames()

    def _extraer_frames(self):
        """Procesa el buffer para extraer todos los frames completos de 8 bytes."""
        b = self._buffer
        i = 0
        while len(b) - i >= FRAME_SIZE:
            frame = bytes(b[i:i + FRAME_SIZE])
            reg = self.interpretar_frame(frame)
            self.registros.append(reg)
            self._raw_frames.append(frame)
            i += FRAME_SIZE
        # conservar el resto
        self._buffer = bytearray(b[i:])

    # -------------------------
    # Interpretador 
    # -------------------------
    def _interpretador_TAR(self, frame: bytes) -> Dict:
        """Decodifica un frame de 8 bytes en sus componentes (TS, CH, VP)."""
        if len(frame) != FRAME_SIZE:
            return {"error": "frame_len_invalid", "_raw": frame}

        # Equivalente a la lógica C de reconstrucción de uint64_t (big-endian)
        pulse = int.from_bytes(frame, byteorder="big", signed=False)

        raw_ts = (pulse & MSK_TS) >> OFF_TS
        ch = (pulse & MSK_CH) >> OFF_CH
        vp = (pulse & MSK_VP) >> OFF_VP

        # overflow 
        if ch == 3:
            self._offset += T_PERIOD
            return {"ts": None, "ts_abs": None, "chan": 3, "vp": None, "_raw": frame, "_overflow": True}

        # En C se usaba vp * 3.21, 'vp' ya es el valor en 'cad' (counts)
        voltage_mv = vp * ZMODADC1410_RESOLUTION    # Conversión a mV 
        
        # unidades: ns -> según implementación original *10 
        ts_abs_ns = (self._offset + raw_ts) * 10 

        return {"ts": raw_ts, "ts_abs_ns": ts_abs_ns, "chan": ch, "vp_counts": vp, "vp_mv": voltage_mv, "_raw": frame}

    # -------------------------
    # Nombres de archivos 
    # -------------------------
    def _timestamp(self) -> str:
        return time.strftime("%Y-%m-%d_%H-%M-%S")

    def _map_chan_letter(self, ch_id: int) -> str:
        if ch_id == 0:
            return "A"
        if ch_id == 1:
            return "B"

        raise ValueError(
            f"Índice de canal inválido para CSV: {ch_id}. "
            "Solo se permiten A (0) y B (1)."
        )


    def _nombre_bin(self, tstamp: str, prefix: Optional[str] = None) -> str:
        base = f"Datos_bin_{tstamp}"
        if prefix:
            base = f"{prefix}_{tstamp}"
        name = f"{base}.bin"
        return os.path.join(self.carpeta_bin, name)

    def _nombre_csv(self, tstamp: str, chan: int, prefix: Optional[str] = None) -> str:
        letra = self._map_chan_letter(chan)
        base = f"Datos_csv_{tstamp}"
        if prefix:
            base = f"{prefix}_{tstamp}"
        # Se usa el formato del C: [prefix/Datos_csv_][timestamp]_canal_[A/B].csv
        name = f"{base}_canal_{letra}.csv"
        return os.path.join(self.carpeta_csv, name)

    # -------------------------
    # Guardado atómico: guarda BIN + CSV por canal y reinicia buffers
    # -------------------------
    def dump_and_reset(self, prefix: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
        """
        Guarda los buffers actuales en archivos .bin y .csv, y reinicia el estado interno.
        """

        if not self.carpeta_bin or not self.carpeta_csv:
            print("[WARN] dump_and_reset llamado sin carpetas configuradas")
            return None, []

        with self._lock:
            if not self._raw_frames:
                print("-> No hay datos para guardar. Buffers vacíos.")
                return None, []

            tstamp = self._timestamp()
            print(f"-> Guardando datos con timestamp: {tstamp}")

            # Guardar bin (equivalente a openBinFile/writeBinFile/closeBinFile)
            raw_path = self._nombre_bin(tstamp, prefix=prefix)
            with open(raw_path, "wb") as f:
                for fr in self._raw_frames:
                    f.write(fr)
            print(f"\tBIN guardado en: {raw_path}")

            # Guardar CSV por canal (equivalente a binToCSV())
            registros_por_ch: Dict[int, List[Dict]] = {}
            overflow_count = 0

            for r in self.registros:
                ch = r.get("chan")
                if ch is None:
                    continue

                # Overflow de base de tiempo
                if ch == 3:
                    overflow_count += 1
                    continue

                # Canal A → chan = 2
                if ch == 2:
                    map_ch = 0   # índice interno para Canal A

                # Canal B → chan = 1
                elif ch == 1:
                    map_ch = 1   # índice interno para Canal B

                # chan = 0 u otros → reservado / inválido
                else:
                    continue

                registros_por_ch.setdefault(map_ch, []).append(r)


            csv_paths: List[str] = []
            for ch_id, regs in registros_por_ch.items():
                csv_path = self._nombre_csv(tstamp, ch_id, prefix=prefix)
                with open(csv_path, "w", newline="") as csvfile:
                    w = csv.writer(csvfile)
                    # Headers del C original: Index,Timestamp (ns),Value (mV)
                    w.writerow(["Index", "Timestamp (ns)", "Value (mV)"])
                    for index, rec in enumerate(regs):
                        w.writerow([
                            index, 
                            rec.get("ts_abs_ns"), 
                            rec.get("vp_mv")
                        ])
                csv_paths.append(csv_path)
                print(f"\tCSV CH{self._map_chan_letter(ch_id)} guardado en: {csv_path} ({len(regs)} pulsos)")

            print(f"\tMarcas de tiempo (overflows): {overflow_count}")
            self._last_overflow_count = overflow_count

            # Reiniciar buffers y offset
            self._buffer.clear()
            self.registros.clear()
            self._raw_frames.clear()
            self._offset = 0

            # actualizar último guardado
            self._ultimo_guardado_ts = time.time()
            
            return raw_path, csv_paths

    # -------------------------
    # Método para reprocesar archivos existentes 
    # -------------------------
    def load_raw_and_reprocesar(self, input_bin_path: str, output_prefix: Optional[str] = None):
        """
        Carga un archivo binario existente, lo procesa y guarda los CSVs resultantes.
        Equivalente a las funciones C binToCSV_console y binToCSV.
        """
        print(f"-> Iniciando reprocesamiento de: {input_bin_path}")

        # Limpiamos buffers antes de cargar nuevos datos
        self._buffer.clear()
        self.registros.clear()
        self._raw_frames.clear()
        self._offset = 0
        
        try:
            with open(input_bin_path, 'rb') as f:
                raw_data = f.read()
        except FileNotFoundError:
            print(f"ERROR: Archivo no encontrado en {input_bin_path}")
            return None, []
        except Exception as e:
            print(f"ERROR leyendo archivo binario: {e}")
            return None, []

        print(f"-> {len(raw_data)} bytes leídos ({len(raw_data)//FRAME_SIZE} registros)")

        # Usamos feed() para cargar los datos en el buffer interno y extraer los frames
        self.feed(raw_data)
        
        # Usamos dump_and_reset() para guardar los CSVs y limpiar los buffers.
        # dump_and_reset utiliza el timestamp actual para los nombres de archivo.
        prefix_final = output_prefix if output_prefix is not None else "reprocesado"
        
        raw_path_out, csv_paths_out = self.dump_and_reset(prefix=prefix_final)
        
        print("-> Reprocesamiento completo a CSV.")
        return raw_path_out, csv_paths_out


    # ======================================================
    #                 Utilidades para GUI
    # ======================================================
    def clear(self):
        with self._lock:
            self._buffer.clear()
            self.registros.clear()
            self._raw_frames.clear()
            self._offset = 0


    def registros_nuevos_desde(self, indice: int):
        """Devuelve los registros desde un índice en adelante."""
        with self._lock:
            return self.registros[indice:]

    def total_registros(self) -> int:
        """Devuelve la cantidad total de registros interpretados acumulados."""
        with self._lock:
            return len(self.registros)
