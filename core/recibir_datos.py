
import serial
import threading
import time


class RecibirDatos:
    """Encapsula toda la lógica de comunicación serie, utiliza un hilo secundario para leer datos constantemente sin congelar 
    la aplicación principal, se utilizan eventos para no hacer polling sobre el estado del puerto, y se gestiona si el puerto
    está abierto o cerrado y controla el ciclo de vida del hilo de lectura."""
    def __init__(self, on_data_callback=None, on_error_callback=None):
        # on_data nos avisa la llegada de datos, on_error si surgen errores en el puerto       
        self.serial = None      # Incializar variable datos en serie 
        self.port = None        # Inicializar variable puerto
        self.baudrate = 115200  # ajustable al TAR

        # Callbacks externos
        self.on_data = on_data_callback     # Se configura el callback para la llegada de datos
        self.on_error = on_error_callback   

        # Control del hilo
        self._stop_event = threading.Event()    # Se configura una variable como evento de accion sobre el hilo
        self._thread = None         # Inicializa una variable que representa estrictamente el hilo

    # ============================================================
    #                 APERTURA Y CIERRE DEL PUERTO
    # ============================================================
    def open(self, port):
        """Intenta abrir el puerto serie y arrancar el hilo de lectura."""
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=0.1
            )
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error al abrir puerto: {e}")
            return False

        self.port = port
        self._stop_event.clear()

        # Iniciar hilo de lectura
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

        return True

    def close(self):
        """Detiene el hilo y cierra el puerto."""
        self._stop_event.set()      # Es el evento que detiene el funcionamiento del hilo, hay datos

        if self._thread:
            self._thread.join(timeout=1.0)

        if self.serial and self.serial.is_open:
            self.serial.close()     # Cierra la lectura

        self.serial = None
        self._thread = None

    # ============================================================
    #                       ENVÍO DE COMANDOS
    # ============================================================
    def send(self, data: bytes):    # Envio de datos en formato bytes
        """Envía datos al firmware TAR."""
        if not self.serial or not self.serial.is_open:
            if self.on_error:
                self.on_error("Intento de enviar sin conexión")
            return False

        try:
            self.serial.write(data)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error al enviar datos: {e}")
            return False

    # ============================================================
    #                   HILO DE LECTURA CONTINUA
    # ============================================================
    def _read_loop(self):
        """Hilo que lee constantemente del puerto serie."""

        while not self._stop_event.is_set():    # Bucle infinito mientras no hay datos entrantes
            try:
                if self.serial and self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)

                    # Llamar callback con los bytes crudos
                    if self.on_data:
                        self.on_data(data)  

            except Exception as e:
                if self.on_error:
                    self.on_error(f"Error leyendo puerto: {e}")
                break

            time.sleep(0.005)  # control para no saturar CPU

    # ============================================================
    #                   PARAMETROS AL TAR
    # ============================================================

    def set_umbral_cha(self, valor):
        cmd = f"UMBRAL CHA {valor}\n".encode()
        self._enviar(cmd)

    def set_umbral_chb(self, valor):
        cmd = f"UMBRAL CHB {valor}\n".encode()
        self._enviar(cmd)

    def _enviar(self, data: bytes):
        if self.serial and self.serial.is_open:
            self.serial.write(data)
            print("[SerialHandler] Enviado:", data)
        else:
            print("[SerialHandler] No hay puerto abierto, simulando:", data)
  
    def iniciar_captura(self):
        """Comienza la transmisión de tramas desde el TAR."""
        self._enviar(b"START\n")

    def detener_captura(self):
        """Detiene la transmisión de tramas desde el TAR."""
        self._enviar(b"STOP\n")


    def is_connected(self) -> bool:
        return self.serial is not None and self.serial.is_open

