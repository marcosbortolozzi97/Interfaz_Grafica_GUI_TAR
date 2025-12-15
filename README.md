# Descripción general  

Este proyecto implementa una interfaz gráfica en Python (Tkinter) para la adquisición, procesamiento, visualización y almacenamiento de datos provenientes de un sistema TAR conectado por puerto serie.
La aplicación permite ejecutar ensayos temporizados, procesar frames binarios del firmware TAR, detectar overflows de tiempo, generar archivos BIN y CSV por canal, y visualizar los datos en tiempo real mediante histogramas.
  
El diseño separa claramente:  
 - adquisición de datos  
 - procesamiento y decodificación  
 - lógica de ensayo  
 - presentación gráfica  
