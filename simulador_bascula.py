# simulador_bascula_gui.py

import serial
import time
import random
import tkinter as tk
import threading
from datetime import datetime

# Función para generar un peso con el mismo formato de la báscula real
def generar_linea_formato_bascula():
    peso = round(random.uniform(10, 100), 2)  # Simular un peso entre 10 y 100 kg
    peso_formateado = f"{peso:>8}"            # Alinear el número a la derecha (8 espacios)
    return f"ST,GS,+{peso_formateado}kg\r\n", peso

# Función de simulación: escribe al puerto COM y muestra en pantalla
def iniciar_simulacion(puerto='COM6', velocidad=9600, intervalo=0.25):
    try:
        ser = serial.Serial(puerto, velocidad)
        id_simulado = 1
        while simulando[0]:
            linea, peso = generar_linea_formato_bascula()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"id={id_simulado}, peso={peso:.2f}kg, fecha_hora={timestamp}")
            ser.write(linea.encode('utf-8'))
            time.sleep(intervalo)
            id_simulado += 1
        ser.close()
    except Exception as e:
        print(f"Error al abrir puerto {puerto}: {e}")

# Acción del botón
def al_presionar_boton():
    if not simulando[0]:
        simulando[0] = True
        hilo = threading.Thread(target=iniciar_simulacion, daemon=True)
        hilo.start()
        boton.config(text="Detener Simulación")
    else:
        simulando[0] = False
        boton.config(text="Iniciar Simulación")

# Estado de simulación
simulando = [False]

# GUI con Tkinter
root = tk.Tk()
root.title("Simulador de Báscula Prometalicos")

tk.Label(root, text="Simula la salida de una báscula en COM6").pack(pady=10)

boton = tk.Button(root, text="Iniciar Simulación", command=al_presionar_boton)
boton.pack(pady=20)

tk.Label(root, text="Formato: ST,GS,+   XX.XXkg | Intervalo: 0.25 seg").pack(pady=10)

root.mainloop()
