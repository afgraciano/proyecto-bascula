import serial
import serial.tools.list_ports
import pyodbc
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import win32com.client  # Requiere: pip install pywin32

# Variables globales
lectura_activa = False
hilo_lectura = None

# Detectar todos los puertos COM disponibles
def detectar_puertos():
    return list(serial.tools.list_ports.comports())

# Crear base de datos Access si no existe, si existe solo se conecta
def crear_base_access(path):
    if not os.path.exists(path):
        access_engine = win32com.client.Dispatch("Access.Application")
        access_engine.NewCurrentDatabase(path)
        access_engine.Quit()

    conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};')
    cursor = conn.cursor()

    tablas = [row.table_name for row in cursor.tables(tableType='TABLE')]
    if 'Pesajes' not in tablas:
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

# Leer desde puerto serial
def iniciar_lectura(puerto, consola):
    global lectura_activa
    lectura_activa = True
    try:
        ser = serial.Serial(puerto, 9600, timeout=1)
        while lectura_activa:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                peso = line
                fecha = datetime.now()
                msg = f"[{fecha.strftime('%Y-%m-%d %H:%M:%S')}] Peso: {peso}\n"
                consola.insert(tk.END, msg)
                consola.see(tk.END)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer: {e}")
    finally:
        if 'ser' in locals(): ser.close()

# Insertar datos en Access desde consola
def guardar_en_access(path, datos):
    conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};')
    cursor = conn.cursor()
    for peso, fecha in datos:
        cursor.execute("INSERT INTO Pesajes (peso, fecha_hora) VALUES (?, ?)", peso, fecha)
    conn.commit()
    cursor.close()
    conn.close()

# Botón: crear Access
def boton_crear_access():
    crear_base_access("C:/Documentos/pesajes.accdb")
    messagebox.showinfo("Access", "Base de datos creada o abierta correctamente.")

# Botón: iniciar lectura
def boton_iniciar():
    global hilo_lectura
    puerto = seleccion_puerto.get()
    if not puerto:
        messagebox.showwarning("Puerto COM", "Seleccione un puerto COM.")
        return
    consola.delete("1.0", tk.END)
    hilo_lectura = threading.Thread(target=iniciar_lectura, args=(puerto, consola), daemon=True)
    hilo_lectura.start()

# Botón: detener lectura
def boton_detener():
    global lectura_activa
    lectura_activa = False
    messagebox.showinfo("Lectura detenida", "Se ha detenido la lectura del puerto.")

# GUI con tkinter
root = tk.Tk()
root.title("Lectura de Báscula Prometalicos")
root.geometry("600x400")

tk.Label(root, text="Selecciona el puerto COM:").pack()

puertos_disponibles = detectar_puertos()
seleccion_puerto = tk.StringVar()
for puerto in puertos_disponibles:
    tk.Radiobutton(root, text=f"{puerto.device} - {puerto.description}", variable=seleccion_puerto, value=puerto.device).pack(anchor="w")

tk.Button(root, text="Iniciar Lectura", command=boton_iniciar).pack(pady=5)
tk.Button(root, text="Detener Lectura", command=boton_detener).pack(pady=5)
tk.Button(root, text="Crear o Actualizar Access", command=boton_crear_access).pack(pady=5)

tk.Label(root, text="Pesos leídos en tiempo real:").pack()
consola = scrolledtext.ScrolledText(root, width=70, height=10)
consola.pack(padx=10, pady=5)

root.mainloop()
