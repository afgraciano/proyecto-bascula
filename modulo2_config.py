"""
modulo2_config.py

Módulo gráfico para configurar el puerto COM de la báscula.

Funcionalidad principal:
- Mostrar ventana Tkinter con lista de posibles puertos (COM1 a COM10).
- Permitir seleccionar un puerto y guardarlo en un archivo config.py.
- Almacenar además la fecha y hora de la configuración.
- Validar que se seleccione un puerto antes de guardar.

Archivos generados:
- config.py : contiene constantes PUERTO_CONFIGURADO y FECHA_CONFIGURACION.

Modo de ejecución:
- Puede usarse como script independiente.
- En modo 'frozen' (ejecutable) detecta el directorio real del .exe para ubicar config.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime

# Guarda la configuración del puerto COM en el archivo config.py
def guardar_puerto_config(puerto):
    # Detectar carpeta real del ejecutable o del script
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(__file__)

    ruta_config = os.path.join(base_dir, 'config.py')
    try:
        # Abrir config.py en modo escritura (se sobrescribe en cada configuración)
        with open(ruta_config, 'w') as f:
            f.write(f'PUERTO_CONFIGURADO = "{puerto}"\n')
            f.write(f'FECHA_CONFIGURACION = "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"\n')
            
        return True
    except Exception as e:
        #print(f"Error al guardar configuración: {e}")
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
