import serial
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
import pyodbc
import os
from datetime import datetime
import win32com.client  # Requiere: pip install pywin32

# Configuración global
lectura_activa = False
hilo_lectura = None
access_path = "C:/Documentos/pesajes.accdb"

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
                print(texto)
                salida_texto.insert(tk.END, texto + '\n')
                salida_texto.see(tk.END)

        ser.close()
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", str(e))

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
    messagebox.showinfo("Lectura", "Lectura iniciada. Revisa los datos en pantalla.")

# Detener la lectura
def detener_lectura():
    global lectura_activa
    lectura_activa = False
    messagebox.showinfo("Lectura detenida", "La lectura ha sido detenida.")

# Construir GUI
root = tk.Tk()
root.title("Lectura Báscula Prometalicos")
root.geometry("500x500")

tk.Label(root, text="Selecciona el puerto COM:").pack(pady=5)

# Mostrar COM1 a COM10 manualmente
seleccion_puerto = tk.StringVar()
for i in range(1, 11):
    com_name = f'COM{i}'
    tk.Radiobutton(root, text=com_name, variable=seleccion_puerto, value=com_name).pack(anchor="w")

# Botones
tk.Button(root, text="Crear Base de Datos Access", command=crear_base_access).pack(pady=10)
tk.Button(root, text="Iniciar Lectura", command=iniciar_lectura).pack(pady=5)
tk.Button(root, text="Detener Lectura", command=detener_lectura).pack(pady=5)

# Salida en pantalla
tk.Label(root, text="Lecturas de la báscula:").pack(pady=5)
salida_texto = scrolledtext.ScrolledText(root, width=60, height=15)
salida_texto.pack(pady=5)

root.mainloop()
