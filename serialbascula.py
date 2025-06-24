import serial
import serial.tools.list_ports
import pyodbc
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import threading

# Función para detectar puertos COM disponibles
def detectar_puertos():
    return list(serial.tools.list_ports.comports())

# Crear base de datos Access con tabla si no existe
def crear_base_access(path):
    if not os.path.exists(path):
        import win32com.client  # Requiere 'pywin32': pip install pywin32
        access_engine = win32com.client.Dispatch("Access.Application")
        access_engine.NewCurrentDatabase(path)
        access_engine.Quit()
    # Conectar e insertar tabla si no existe
    conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Pesajes (
            id AUTOINCREMENT PRIMARY KEY,
            peso TEXT,
            fecha_hora DATETIME
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Función para leer datos del puerto serial y guardar en Access
def iniciar_lectura(puerto, access_path):
    try:
        ser = serial.Serial(puerto, 9600, timeout=1)
        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path};')
        cursor = conn.cursor()

        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                peso = line
                fecha = datetime.now()
                print(f"[{fecha.strftime('%Y-%m-%d %H:%M:%S')}] Peso leído: {peso}")
                cursor.execute("INSERT INTO Pesajes (peso, fecha_hora) VALUES (?, ?)", peso, fecha)
                conn.commit()
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        if 'ser' in locals(): ser.close()
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# Función que se ejecuta al presionar el botón
def al_presionar_boton():
    puerto = seleccion_puerto.get()
    if not puerto:
        messagebox.showwarning("Atención", "Seleccione un puerto COM primero.")
        return

    access_path = "C:/Documentos/pesajes.accdb"
    crear_base_access(access_path)

    messagebox.showinfo("Acción iniciada", "Se iniciará la lectura. Revisa la consola para ver los datos.")
    hilo = threading.Thread(target=iniciar_lectura, args=(puerto, access_path), daemon=True)
    hilo.start()

# GUI con tkinter
root = tk.Tk()
root.title("Lectura de Báscula Prometalicos")

tk.Label(root, text="Selecciona el puerto COM:").pack(pady=5)

puertos_disponibles = detectar_puertos()
seleccion_puerto = tk.StringVar()
for puerto in puertos_disponibles:
    tk.Radiobutton(root, text=str(puerto), variable=seleccion_puerto, value=puerto.device).pack(anchor="w")

tk.Button(root, text="Crear Access e Iniciar Lectura", command=al_presionar_boton).pack(pady=10)

tk.Label(root, text="Revisa la consola para ver los pesos recibidos en tiempo real").pack(pady=5)

root.mainloop()
