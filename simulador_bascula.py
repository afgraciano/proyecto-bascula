import serial
import time
import tkinter as tk
import threading
from datetime import datetime

# Configuración inicial
simulando = [False]
peso_actual = [0.0]
puerto_simulado = 'COM6'
velocidad = 9600
intervalo_envio = 0.25  # segundos

# Genera línea con el formato de la báscula
def generar_linea_formato_bascula(peso):
    peso_formateado = f"{peso:>8.2f}"  # Alineado a la derecha con 2 decimales
    return f"ST,GS,+{peso_formateado}kg\r\n"

# Función que ejecuta la simulación
def iniciar_simulacion():
    try:
        ser = serial.Serial(puerto_simulado, velocidad)
        id_simulado = 1
        while simulando[0]:
            linea = generar_linea_formato_bascula(peso_actual[0])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"id={id_simulado}, peso={peso_actual[0]:.2f}kg, fecha_hora={timestamp}")
            ser.write(linea.encode('utf-8'))
            time.sleep(intervalo_envio)
            id_simulado += 1
        ser.close()
    except Exception as e:
        print(f"Error al abrir puerto {puerto_simulado}: {e}")

# Botón para iniciar/detener
def al_presionar_boton_simulacion():
    if not simulando[0]:
        simulando[0] = True
        hilo = threading.Thread(target=iniciar_simulacion, daemon=True)
        hilo.start()
        boton_inicio.config(text="Detener Simulación")
    else:
        simulando[0] = False
        boton_inicio.config(text="Iniciar Simulación")

# Botones de cambio de peso
def cambiar_peso(nuevo_peso):
    peso_actual[0] = nuevo_peso
    print(f">>> Peso simulado cambiado a {nuevo_peso} kg")

# GUI
root = tk.Tk()
root.title("Simulador de Báscula Prometalicos")

tk.Label(root, text="Simulador: salida continua por COM6").pack(pady=10)

boton_inicio = tk.Button(root, text="Iniciar Simulación", command=al_presionar_boton_simulacion)
boton_inicio.pack(pady=10)

tk.Label(root, text="Selecciona el peso simulado:").pack(pady=5)

frame_botones = tk.Frame(root)
frame_botones.pack(pady=5)

tk.Button(frame_botones, text="0 kg", width=10, command=lambda: cambiar_peso(0)).grid(row=0, column=0, padx=5)
tk.Button(frame_botones, text="500 kg", width=10, command=lambda: cambiar_peso(500)).grid(row=0, column=1, padx=5)
tk.Button(frame_botones, text="2700 kg", width=10, command=lambda: cambiar_peso(2700)).grid(row=0, column=2, padx=5)
tk.Button(frame_botones, text="10000 kg", width=10, command=lambda: cambiar_peso(10000)).grid(row=0, column=3, padx=5)

tk.Label(root, text="Formato: ST,GS,+   XXXX.XXkg | Intervalo: 0.25 seg").pack(pady=10)

root.mainloop()
