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
Python 3.9 o superior, puede ejcutar en una PowerShell:  
```bash
python --version
```
  para verificar su versión de python.  
### Librerías externas:  
 - pyserial  
 - matplotlib  
En caso de no tener instaladas estas ultimas,  
```bash
python -m pip install pyserial matplotlib
```
  para instalar las dependencias externas.  

---

## Flujo de datos  
El firmware TAR envía frames binarios por puerto serie.  
RecibirDatos recibe los bytes y los pasa a la GUI.  
ProcesaDatosTAR.feed():
 - Extrae frames completos.  
 - Decodifica timestamps, canales y valores.
Los datos Se almacenan en buffers internos.  
Durante el ensayo:
 - Se realizan autoguardados y se generan archivos .bin y .csv  periódicamente.  
 - Se visualizan en tiempo real.  
Al finalizar el ensayo:  
 - Se genera un archivo final .bin y .csv.  
 - Se reinician los buffers.  
