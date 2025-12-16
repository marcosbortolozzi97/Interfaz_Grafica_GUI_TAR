# **Descripción general**  

Este proyecto implementa una interfaz gráfica en Python (Tkinter) para la adquisición, procesamiento, visualización y almacenamiento de datos provenientes de un sistema TAR conectado por puerto serie.
La aplicación permite ejecutar ensayos temporizados, procesar frames binarios del firmware TAR, detectar overflows de tiempo, generar archivos BIN y CSV por canal, y visualizar los datos en tiempo real mediante histogramas.
  
El diseño separa:  
 - adquisición de datos  
 - procesamiento y decodificación  
 - lógica de ensayo  
 - presentación gráfica  

---

## **Flujo de datos**  
### El firmware TAR envía frames binarios por puerto serie.  
### RecibirDatos recibe los bytes y los pasa a la GUI.  
### ProcesaDatosTAR.feed():
 - Extrae frames completos.  
 - Decodifica timestamps, canales y valores.  
### Los datos se almacenan en buffers internos.  
### Durante el ensayo:
 - Se realizan autoguardados y se generan archivos .bin y .csv  periódicamente.  
 - Se visualizan en tiempo real.  
### Al finalizar el ensayo:  
 - Se genera un archivo final .bin y .csv.  
 - Se reinician los buffers.  

---

## **Dependencias necesarias**  
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

## **Ejecución del programa**  
Clonar o descargar el repositorio.  
Abrir el proyecto en un entorno Python (VSCode, etc).  
Ejecutar el archivo principal:  
```bash
python main.py
```
Alternativamente, desde el editor, abrir main.py y ejecutarlo directamente.

---

## **Procedimiento Ensayo**  
Conectar el dispositivo TAR por puerto serie, recargar y abrir la solapa, seleccionar el puerto disponible, presionar *conectar*.  
Configurar parámetros, los umbrales de la ventana de histeresis, *aplicar*.  
Es opcional fijar la ventana de los histogramas a efectos del inicio de ensayo, pero se los puede configurar para la visualización gráfica.  
Establecer la temporización del ensayo en unidades de segundos.  
Presionar *Iniciar ensayo* (es obligatorio para dar inicio al ensayo conectar el puerto, la aplicación de los parámetros y el seteo de la temporización).  
Puede finalizar el ensayo antes de finalizada la temporización presionando *finalizar ensayo*.  

---

## **Resultados y extra**  
Se genera un archivo .bin y dos archivos .csv (correspondiente a cada canal) cada 15 segundos durante el ensayo y se guardan en una carpeta llamada *ensayos*. Dentro de *ensayos* se crean las carpetas correspondientes a los datos guardados cada 15 segundos, denominadas *ensayo_AAAA-MM-DD_HH-MM-SS* (ej, ensayo_2024-10-22_13-51-32), que dentro incluye carpetas separadas *bin* y *csv*, las cuales contienen los archivos correspondientes al respectivo intervalo de 15 segundos.  
Se puede por otro lado, reprocesar los archivos binarios crudos (raw) presionando *Procesar binario previo*, se abre una carpeta en el directorio que se han creado los archivos y se pueden seleccionar el archivo .bin deseado. Se puede visualizar los resultados o realizar los análisis solicitados.
