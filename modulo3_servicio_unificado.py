import tkinter as tk
import socket
import json

def obtener_datos_peso():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5000))
            data = s.recv(1024)
            resultado = json.loads(data.decode())
            return resultado.get("peso", 0), resultado.get("timestamp", "")
    except:
        return 0, ""

def actualizar_peso():
    peso, hora = obtener_datos_peso()
    peso_label.config(text=f"{peso:.2f} kg")
    hora_label.config(text=f"{hora}")
    root.after(500, actualizar_peso)

root = tk.Tk()
root.title("Monitor de Peso en Tiempo Real")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

tk.Label(frame, text="Peso actual:", font=("Arial", 14)).pack()
peso_label = tk.Label(frame, text="---", font=("Arial", 28, "bold"), fg="blue")
peso_label.pack()

hora_label = tk.Label(frame, text="", font=("Arial", 10), fg="gray")
hora_label.pack(pady=(5, 0))

actualizar_peso()
root.mainloop()
