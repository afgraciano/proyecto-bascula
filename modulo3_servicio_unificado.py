import tkinter as tk
from tkinter import simpledialog, messagebox
import socket
import json
from datetime import datetime

pesajes_temporales = {}

def obtener_datos_peso():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5000))
            data = s.recv(1024)
            resultado = json.loads(data.decode())
            return resultado.get("peso", 0), resultado.get("timestamp", "")
    except:
        return 0, ""

def modulo_servicio():
    def verificar_servicio(tipo):
        #tipo = tipo_var.get()
        peso, _ = obtener_datos_peso()

        if tipo == "Externo":
            messagebox.showinfo("Servicio", f"Pesaje externo detectado: {peso:.2f} kg")

        elif tipo in ["Inmuniza", "Aserrio"]:
            id_ingresado = simpledialog.askstring("ID", "Ingrese el ID del pesaje:")
            if not id_ingresado:
                return
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if id_ingresado in pesajes_temporales:
                peso_inicial, fecha_inicial = pesajes_temporales[id_ingresado]
                peso_neto = peso - peso_inicial
                messagebox.showinfo("Resultado",
                    f"Pesaje final registrado.\nID: {id_ingresado}\nPeso Neto: {peso_neto:.2f} kg\nInicio: {fecha_inicial}\nFin: {fecha_actual}")
                del pesajes_temporales[id_ingresado]
            else:
                pesajes_temporales[id_ingresado] = (peso, fecha_actual)
                messagebox.showinfo("Pesaje inicial",
                    f"Peso inicial registrado: {peso:.2f} kg\nID: {id_ingresado}")

        else:  # Astillero
            messagebox.showinfo("Astillero", f"Peso actual mostrado: {peso:.2f} kg")

    def actualizar_peso_gui():
        peso, hora = obtener_datos_peso()
        peso_label.config(text=f"{peso:.2f} kg")
        hora_label.config(text=hora)
        ventana.after(500, actualizar_peso_gui)

    ventana = tk.Tk()
    ventana.title("Servicio de Báscula")

    # Pantalla de monitoreo
    marco_peso = tk.Frame(ventana, bg="white", relief="sunken", bd=2)
    marco_peso.pack(pady=10, fill="x")

    tk.Label(marco_peso, text="Peso actual (kg):", font=("Arial", 12)).pack()
    peso_label = tk.Label(marco_peso, text="---", font=("Arial", 24, "bold"), fg="blue")
    peso_label.pack()
    hora_label = tk.Label(marco_peso, text="", font=("Arial", 10), fg="gray")
    hora_label.pack(pady=(2, 5))

    actualizar_peso_gui()

    # Selección de tipo de servicio
    
    
    tk.Label(ventana, text="Seleccione el tipo de servicio:", font=("Arial", 12)).pack(pady=10)

    frame_botones = tk.Frame(ventana)
    frame_botones.pack(pady=5)

    tipos = ["Externo", "Inmuniza", "Aserrio", "Astillero"]
    for tipo in tipos:
        tk.Button(frame_botones, text=tipo, width=15, font=("Arial", 11),
                  command=lambda t=tipo: verificar_servicio(t)).pack(side="left", padx=5)

    ventana.mainloop()

if __name__ == "__main__":
    modulo_servicio()
