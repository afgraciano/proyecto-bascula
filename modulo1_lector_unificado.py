import serial
import time
import threading
import socket
import json
from datetime import datetime
from config import PUERTO_CONFIGURADO
import tkinter as tk
from tkinter import messagebox

peso_actual = 0
alerta_mostrada = False

# Crear ventana oculta para permitir messagebox
ventana_alerta = tk.Tk()
ventana_alerta.withdraw()

def leer_puerto():
    global peso_actual, alerta_mostrada
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado.")
        return

    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=0.1)
            break
        except serial.SerialException:
            print("❌ Puerto no disponible.")
            time.sleep(2)

    print("✅ Conectado. Iniciando lectura...")
    while True:
        try:
            raw = ser.readline()
            if raw:
                try:
                    linea = raw.decode("utf-8").strip()
                    if "+" in linea or "-" in linea:
                        import re
                        match = re.search(r"[+-]\s*(\d+)\s*kg", linea)
                        if match:
                            peso = int(match.group(1))
                            peso_actual = peso

                            # Alerta solo una vez mientras esté alto
                            if peso_actual >= 80000 and not alerta_mostrada:
                                alerta_mostrada = True
                                print("🚨 ¡ALERTA! Peso máximo superado.")
                                messagebox.showwarning("¡Peso excesivo!",
                                    f"El peso actual ({peso_actual} kg) supera el límite de 80,000 kg.")
                            elif peso_actual < 80000:
                                alerta_mostrada = False

                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"Error leyendo: {e}")
        time.sleep(0.1)

def iniciar_socket():
    HOST = "127.0.0.1"
    PORT = 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"🟢 Servidor socket escuchando en {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                respuesta = {"peso": peso_actual, "timestamp": now}
                conn.sendall(json.dumps(respuesta).encode())

if __name__ == "__main__":
    hilo_alerta = threading.Thread(target=ventana_alerta.mainloop, daemon=True)
    hilo_alerta.start()

    hilo_lector = threading.Thread(target=leer_puerto, daemon=True)
    hilo_lector.start()

    iniciar_socket()
