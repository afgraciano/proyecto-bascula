# modulo2_configuracion.py

import tkinter as tk
from tkinter import ttk, messagebox
import os

# Guarda la configuración del puerto COM en el archivo config.py
def guardar_puerto_config(puerto):
    ruta_config = os.path.join(os.path.dirname(__file__), 'config.py')
    try:
        with open(ruta_config, 'w') as f:
            f.write(f'PUERTO_CONFIGURADO = "{puerto}"\n')
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False

# Valida la selección y guarda el puerto
def guardar_configuracion():
    puerto = seleccion_puerto.get()
    if not puerto:
        messagebox.showwarning("Advertencia", "Debes seleccionar un puerto COM.")
        return

    if guardar_puerto_config(puerto):
        messagebox.showinfo("Guardado", f"Puerto {puerto} guardado en config.py.")
        root.destroy()
    else:
        messagebox.showerror("Error", "No se pudo guardar la configuración.")

# Ventana principal de configuración
root = tk.Tk()
root.title("Configuración de Puerto")
root.geometry("300x200")

tk.Label(root, text="Selecciona el puerto COM").pack(pady=10)

puertos = [f"COM{i}" for i in range(1, 11)]  # Lista de puertos disponibles
seleccion_puerto = ttk.Combobox(root, values=puertos, state="readonly")
seleccion_puerto.pack()

btn_guardar = tk.Button(root, text="Aceptar", command=guardar_configuracion)
btn_guardar.pack(pady=20)

root.mainloop()
