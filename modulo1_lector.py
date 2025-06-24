# modulo1_lector.py
import serial
import time
import threading
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from config import PUERTO_CONFIGURADO

def ejecutar_modulo3():
    ruta_modulo3 = os.path.join(os.path.dirname(__file__), 'modulo3_servicio.py')
    subprocess.Popen(["python", ruta_modulo3], shell=True)

def mostrar_mensaje_desconexion():
    root = tk.Tk()
    root.withdraw()

    motivo = tk.StringVar()

    def set_motivo(valor):
        motivo.set(valor)
        ventana.quit()

    ventana = tk.Toplevel()
    ventana.title("Desconexión de báscula")
    ventana.geometry("300x150")
    ventana.resizable(False, False)

    label = tk.Label(ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11))
    label.pack(pady=10)

    boton1 = tk.Button(ventana, text="Corte de energía", command=lambda: set_motivo("Corte de energía"))
    boton1.pack(pady=5)

    boton2 = tk.Button(ventana, text="Desconexión de cable", command=lambda: set_motivo("Desconexión de cable"))
    boton2.pack(pady=5)

    ventana.protocol("WM_DELETE_WINDOW", lambda: None)  # Evita que cierren la ventana

    ventana.mainloop()
    ventana.destroy()
    return motivo.get()

def verificar_peso():
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado. Usa modulo2_configuracion.py.")
        return

    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=1)
            print(f"✅ Conectado a {PUERTO_CONFIGURADO}")
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, reintentando...")
            time.sleep(2)

    pesos_estables = []

    print("▶️ Esperando datos desde la báscula...")

    datos_recibidos = False
    tiempo_ultimo_mensaje = 0
    intervalo_mensaje = 5  # segundos

    while not datos_recibidos:
        try:
            linea = ser.readline().decode('utf-8').strip()
            if linea:
                print(f"📥 Primer dato recibido: {linea}")
                datos_recibidos = True
                break
            else:
                tiempo_actual = time.time()
                if tiempo_actual - tiempo_ultimo_mensaje >= intervalo_mensaje:
                    motivo = mostrar_mensaje_desconexion()
                    print(f"📝 Usuario indicó: {motivo}")
                    tiempo_ultimo_mensaje = tiempo_actual
        except serial.SerialException:
            tiempo_actual = time.time()
            if tiempo_actual - tiempo_ultimo_mensaje >= intervalo_mensaje:
                motivo = mostrar_mensaje_desconexion()
                print(f"📝 Usuario indicó: {motivo}")
                tiempo_ultimo_mensaje = tiempo_actual
        time.sleep(1)

    print("▶️ Iniciando lectura continua...")

    while True:
        try:
            linea = ser.readline().decode('utf-8').strip()
            if not linea:
                continue

            print(f"📥 Peso recibido: {linea}")
            try:
                peso = float(linea)
            except ValueError:
                continue

            if peso >= 300:
                print(f"🚨 Peso alto detectado: {peso} kg")
                ejecutar_modulo3()
                break

            pesos_estables.append(peso)
            pesos_estables = pesos_estables[-5:]

            if len(pesos_estables) == 5 and all(p < 300 for p in pesos_estables):
                print("✅ Peso estable por debajo de 300 kg.")

            time.sleep(1)

        except serial.SerialException:
            print("❌ Conexión perdida.")
            break

    ser.close()
    print("⛔ Finalizando módulo 1.")

if __name__ == "__main__":
    hilo = threading.Thread(target=verificar_peso)
    hilo.daemon = True
    hilo.start()

    try:
        while hilo.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("⛔ Interrumpido manualmente.")
