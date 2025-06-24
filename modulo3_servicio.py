# modulo3_servicio.py

import tkinter as tk
from tkinter import simpledialog, messagebox
import config
from datetime import datetime

# Diccionario para almacenar pesajes temporales con sus fechas
pesajes_temporales = {}

# Función principal del módulo de servicio
def modulo_servicio():
    def verificar_servicio():
        tipo = tipo_var.get()
        if tipo == "Externo":
            # Muestra el peso actual para el servicio externo
            messagebox.showinfo("Servicio", f"Pesaje externo detectado: {config.peso_actual:.2f} kg")
        elif tipo in ["Inmuniza", "Aserrio"]:
            # Solicita ID del pesaje
            id_ingresado = simpledialog.askstring("ID", "Ingrese el ID del pesaje:")
            if not id_ingresado:
                return
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if id_ingresado in pesajes_temporales:
                # Calcula peso neto
                peso_inicial, fecha_inicial = pesajes_temporales[id_ingresado]
                peso_neto = config.peso_actual - peso_inicial
                messagebox.showinfo("Resultado",
                    f"Pesaje final registrado.\nID: {id_ingresado}\nPeso Neto: {peso_neto:.2f} kg\nInicio: {fecha_inicial}\nFin: {fecha_actual}")
                del pesajes_temporales[id_ingresado]
            else:
                # Registra peso inicial
                pesajes_temporales[id_ingresado] = (config.peso_actual, fecha_actual)
                messagebox.showinfo("Pesaje inicial",
                    f"Peso inicial registrado: {config.peso_actual:.2f} kg\nID: {id_ingresado}")
        else:  # Astillero
            # Solo muestra el peso actual
            messagebox.showinfo("Astillero", f"Peso actual mostrado: {config.peso_actual:.2f} kg")

    # Crea ventana de selección de tipo de servicio
    ventana = tk.Tk()
    ventana.title("Servicio de Báscula")

    tk.Label(ventana, text="Tipo de servicio:").pack(pady=5)
    tipo_var = tk.StringVar(value="Externo")
    for tipo in ["Externo", "Inmuniza", "Aserrio", "Astillero"]:
        tk.Radiobutton(ventana, text=tipo, variable=tipo_var, value=tipo).pack(anchor="w")

    tk.Button(ventana, text="Aceptar", command=verificar_servicio).pack(pady=10)
    ventana.mainloop()

# Ejecuta si es archivo principal
if __name__ == "__main__":
    modulo_servicio()
