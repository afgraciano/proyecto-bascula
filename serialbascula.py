#detecta lo que arroja la bascula en el puerto serial y lo mete en un access

import serial
import serial.tools.list_ports
import pyodbc
import os
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import win32com.client  # pip install pywin32

# Variables globales
lectura_activa = False
hilo_lectura = None
access_path = "C:/Documentos/pesajes.accdb"

# Detectar puertos COM disponibles
def detectar_puertos():
    puertos = []
    for port in serial.tools.list_ports.comports():
        nombre = f"{port.device} - {port.description}"
        puertos.append((port.device, nombre))
    return puertos

# Crear base de datos Access si no existe
def crear_base_access():
    if not os.path.exists(access_path):
        access_engine = win32com.client.Dispatch("Access.Application")
        access_engine.NewCurrentDatabase(access_path)
        access_engine.Quit()

        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path};')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE Pesajes (
                id AUTOINCREMENT PRIMARY KEY,
                peso TEXT,
                fecha_hora DATETIME
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Éxito", "Base de datos Access creada.")
    else:
        messagebox.showinfo("Información", "La base de datos ya existe.")

# Función de lectura del puerto COM
def leer_puerto_serial(puerto):
    global lectura_activa
    try:
        ser = serial.Serial(puerto, 9600, timeout=1)
        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path};')
        cursor = conn.cursor()

        while lectura_activa:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if linea:
                fecha = datetime.now()
                cursor.execute("INSERT INTO Pesajes (peso, fecha_hora) VALUES (?, ?)", linea, fecha)
                conn.commit()
                texto = f"[{fecha.strftime('%Y-%m-%d %H:%M:%S')}] Peso: {linea}"
                salida_texto.insert(tk.END, texto + '\n')
                salida_texto.see(tk.END)
                print(texto)  # También imprime en consola

        ser.close()
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer el puerto {puerto}:\n{str(e)}")

# Iniciar la lectura
def iniciar_lectura():
    global lectura_activa, hilo_lectura
    puerto = seleccion_puerto.get()
    if not puerto:
        messagebox.showwarning("Atención", "Selecciona un puerto COM primero.")
        return

    if not os.path.exists(access_path):
        messagebox.showwarning("Base de datos", "Primero crea la base de datos con el botón correspondiente.")
        return

    lectura_activa = True
    hilo_lectura = threading.Thread(target=leer_puerto_serial, args=(puerto,), daemon=True)
    hilo_lectura.start()
    messagebox.showinfo("Lectura", "Lectura iniciada. Revisa los datos en pantalla y en consola.")

# Detener la lectura
def detener_lectura():
    global lectura_activa
    lectura_activa = False

# Al cerrar la ventana
def al_cerrar():
    global hilo_lectura
    if lectura_activa:
        detener_lectura()
        if hilo_lectura and hilo_lectura.is_alive():
            hilo_lectura.join(timeout=2)
    root.destroy()

# GUI principal
root = tk.Tk()
root.title("Lectura Báscula Prometalicos")
root.geometry("700x550")
root.protocol("WM_DELETE_WINDOW", al_cerrar)

tk.Label(root, text="Selecciona el puerto COM:").pack(pady=5)

seleccion_puerto = tk.StringVar()
puertos_disponibles = detectar_puertos()

# Si hay puertos detectados, se listan
if puertos_disponibles:
    frame_puertos = tk.Frame(root)
    frame_puertos.pack()
    for device, descripcion in puertos_disponibles:
        tk.Radiobutton(frame_puertos, text=descripcion, variable=seleccion_puerto, value=device).pack(side="left", padx=5)
else:
    # Si no se detectan, mostrar manualmente COM1 a COM10 en 2 filas
    tk.Label(root, text="No se detectaron puertos automáticamente.\nSelecciona un puerto manualmente:").pack(pady=5)

    frame_puertos1 = tk.Frame(root)
    frame_puertos1.pack(pady=2)
    frame_puertos2 = tk.Frame(root)
    frame_puertos2.pack(pady=2)

    for i in range(1, 6):
        com_name = f"COM{i}"
        tk.Radiobutton(frame_puertos1, text=com_name, variable=seleccion_puerto, value=com_name).pack(side="left", padx=5)

    for i in range(6, 11):
        com_name = f"COM{i}"
        tk.Radiobutton(frame_puertos2, text=com_name, variable=seleccion_puerto, value=com_name).pack(side="left", padx=5)

# Botones
tk.Button(root, text="Crear Base de Datos Access", command=crear_base_access).pack(pady=10)
tk.Button(root, text="Iniciar Lectura", command=iniciar_lectura).pack(pady=5)
tk.Button(root, text="Detener Lectura", command=detener_lectura).pack(pady=5)

# Consola de salida en GUI
tk.Label(root, text="Lecturas de la báscula:").pack(pady=5)
salida_texto = scrolledtext.ScrolledText(root, width=80, height=15)
salida_texto.pack(padx=10, pady=5)

root.mainloop()
