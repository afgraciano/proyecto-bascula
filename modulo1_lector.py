# modulo1_lector.py

import serial
import time
import os
import subprocess
import tkinter as tk
from config import PUERTO_CONFIGURADO

# Ejecuta el módulo de servicio y devuelve el proceso
def ejecutar_modulo3():
    ruta_modulo3 = os.path.join(os.path.dirname(__file__), 'modulo3_servicio.py')
    return subprocess.Popen(["python", ruta_modulo3], shell=True)

# Clase para la ventana de desconexión
class VentanaDesconexion:
    def __init__(self, root):
        self.root = root
        self.ventana = None
        self.activa = False

    def mostrar(self):
        if self.activa:
            return
        self.activa = True

        self.ventana = tk.Toplevel(self.root)
        self.ventana.title("Desconexión de báscula")
        self.ventana.geometry("300x170")
        self.ventana.resizable(False, False)

        # Siempre al frente
        self.ventana.attributes("-topmost", True)
        self.ventana.lift()
        self.ventana.focus_force()

        self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)

        label = tk.Label(self.ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11))
        label.pack(pady=10)

        boton1 = tk.Button(self.ventana, text="Corte de energía", width=25,
                           command=lambda: self.cerrar("Corte de energía"))
        boton1.pack(pady=5)

        boton2 = tk.Button(self.ventana, text="Desconexión de cable", width=25,
                           command=lambda: self.cerrar("Desconexión de cable"))
        boton2.pack(pady=5)

    def cerrar(self, motivo=None):
        if motivo:
            print(f"📝 Usuario indicó: {motivo}")
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.destroy()
        self.activa = False

# Función principal
def verificar_peso():
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado. Usa modulo2_configuracion.py.")
        return

    # Conexión serial
    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=1)
            print(f"✅ Conectado a {PUERTO_CONFIGURADO}")
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, reintentando...")
            time.sleep(2)

    print("▶️ Iniciando monitoreo de la báscula...")

    root = tk.Tk()
    root.withdraw()

    ventana_desconexion = VentanaDesconexion(root)
    proceso_modulo3 = None  # Proceso activo de modulo3
    tiempo_sin_datos = 0
    intervalo_reconexion = 2  # segundos sin datos antes de mostrar ventana
    pesos_estables = []

    while True:
        root.update()

        try:
            linea = ser.readline().decode('utf-8').strip()

            if linea:
                tiempo_sin_datos = 0
                ventana_desconexion.cerrar()

                print(f"📥 Peso recibido: {linea}")
                try:
                    peso = float(linea)
                except ValueError:
                    continue

                # Condición para abrir modulo3 solo si no está activo
                if peso >= 300:
                    if proceso_modulo3 is None or proceso_modulo3.poll() is not None:
                        print(f"🚨 Peso alto detectado: {peso} kg")
                        proceso_modulo3 = ejecutar_modulo3()
                    else:
                        print("⏳ Esperando que se cierre modulo3...")

                pesos_estables.append(peso)
                pesos_estables = pesos_estables[-5:]

                if len(pesos_estables) == 5 and all(p < 300 for p in pesos_estables):
                    print("✅ Peso estable por debajo de 300 kg.")

            else:
                tiempo_sin_datos += 1
                if tiempo_sin_datos >= intervalo_reconexion:
                    ventana_desconexion.mostrar()

        except serial.SerialException:
            print("❌ Conexión perdida con el puerto.")
            tiempo_sin_datos += 1
            ventana_desconexion.mostrar()

        time.sleep(1)

    ser.close()
    print("⛔ Finalizando módulo 1.")

if __name__ == "__main__":
    verificar_peso()
