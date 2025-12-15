# Descripción general  

Este proyecto implementa una interfaz gráfica en Python (Tkinter) para la adquisición, procesamiento, visualización y almacenamiento de datos provenientes de un sistema TAR conectado por puerto serie.
La aplicación permite ejecutar ensayos temporizados, procesar frames binarios del firmware TAR, detectar overflows de tiempo, generar archivos BIN y CSV por canal, y visualizar los datos en tiempo real mediante histogramas.
  
El diseño separa:  
 - adquisición de datos  
 - procesamiento y decodificación  
 - lógica de ensayo  
 - presentación gráfica  

---

## Dependencias necesarias  
Asegurarse de tener instalado en el sistema:  
Python 3.9 o superior  
Librerías estándar:  
 - tkinter  
 - threading  
 - csv  
 - os  
 - time  
Librerías externas:  
 - pyserial  
 - matplotlib  
En caso de no tener instaladas estas ultimas, puede ejcutar en una PowerShell:
```bash
python --version
```
  para verificar su versión de python.
```bash
python -m pip install pyserial matplotlib
```
