# modulo1_lector.py

import serial
import time
import os
import subprocess
import tkinter as tk
from config import PUERTO_CONFIGURADO

# Ejecuta el módulo de servicio (modulo3_servicio.py)
def ejecutar_modulo3():
    ruta_modulo3 = os.path.join(os.path.dirname(__file__), 'modulo3_servicio.py')
    subprocess.Popen(["python", ruta_modulo3], shell=True)

# Clase para la ventana de desconexión con botones
class VentanaDesconexion:
    def __init__(self, root):
        self.root = root
        self.ventana = None
        self.activa = False
        self.motivo = None

    def mostrar(self):
        if self.activa:
            return
        self.activa = True

        self.ventana = tk.Toplevel(self.root)
        self.ventana.title("Desconexión de báscula")
        self.ventana.geometry("300x170")
        self.ventana.resizable(False, False)
        self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)

        label = tk.Label(self.ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11))
        label.pack(pady=10)

        boton1 = tk.Button(self.ventana, text="Corte de energía", width=25, command=lambda: self.set_motivo("Corte de energía"))
        boton1.pack(pady=5)

        boton2 = tk.Button(self.ventana, text="Desconexión de cable", width=25, command=lambda: self.set_motivo("Desconexión de cable"))
        boton2.pack(pady=5)

    def set_motivo(self, motivo):
        self.motivo = motivo
        print(f"📝 Usuario indicó: {motivo}")
        self.cerrar()

    def cerrar(self):
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.destroy()
        self.activa = False

# Función principal
def verificar_peso():
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado. Usa modulo2_configuracion.py.")
        return

    # Intento de conexión
    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=1)
            print(f"✅ Conectado a {PUERTO_CONFIGURADO}")
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, reintentando...")
            time.sleep(2)

    pesos_estables = []
    print("▶️ Iniciando monitoreo de la báscula...")

    root = tk.Tk()
    root.withdraw()

    ventana_desconexion = VentanaDesconexion(root)
    tiempo_sin_datos = 0
    intervalo_reconexion = 2  # segundos sin datos antes de mostrar ventana

    while True:
        root.update()

        try:
            linea = ser.readline().decode('utf-8').strip()

            if linea:
                # Reinicia el temporizador de inactividad
                tiempo_sin_datos = 0

                # Cierra la ventana si estaba abierta
                ventana_desconexion.cerrar()

                print(f"📥 Peso recibido: {linea}")
                try:
                    peso = float(linea)
                except ValueError:
                    continue

                if peso >= 300:
                    print(f"🚨 Peso alto detectado: {peso} kg")
                    ejecutar_modulo3()
                    break  # Si quieres que continúe después de abrir módulo3, quita este break

                # Mantiene los últimos 5 pesos
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
            ventana_desconexion.mostrar()
            tiempo_sin_datos += 1

        time.sleep(1)

    ser.close()
    print("⛔ Finalizando módulo 1.")

if __name__ == "__main__":
    verificar_peso()
