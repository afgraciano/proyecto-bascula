import serial
import time
import os
import subprocess
import tkinter as tk
import re
import socket
import json
import threading
from datetime import datetime
from config import PUERTO_CONFIGURADO
import config
import psutil  # ✅ Para verificar si el proceso aún está vivo

# Ejecuta módulo 3
def ejecutar_modulo3():
    ruta_modulo3 = os.path.join(os.path.dirname(__file__), 'modulo3_servicio_unificado.py')
    return subprocess.Popen(["python", ruta_modulo3], shell=True)

# Verifica si el proceso aún está vivo
def proceso_activo(proceso):
    return proceso is not None and proceso.poll() is None and psutil.pid_exists(proceso.pid)

# Alerta por desconexión
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
        self.ventana.attributes("-topmost", True)
        self.ventana.lift()
        self.ventana.focus_force()
        self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)

        tk.Label(self.ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11)).pack(pady=10)
        tk.Button(self.ventana, text="Corte de energía", width=25,
                  command=lambda: self.cerrar("Corte de energía")).pack(pady=5)
        tk.Button(self.ventana, text="Desconexión de cable", width=25,
                  command=lambda: self.cerrar("Desconexión de cable")).pack(pady=5)

    def cerrar(self, motivo=None):
        if motivo:
            print(f"📝 Usuario indicó: {motivo}")
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.destroy()
        self.activa = False

    def verificar_estado(self):
        if self.ventana and self.ventana.winfo_exists():
            if self.ventana.state() == 'iconic':
                self.ventana.deiconify()
                self.ventana.lift()
                self.ventana.focus_force()

# Ventana de alerta de sobrepeso no bloqueante
class VentanaAlertaPeso:
    def __init__(self):
        self.ventana = None

    def mostrar(self, peso):
        # Si no existe ventana, crear una ventana independiente (Tk) no bloqueante
        if self.ventana is None or not self.ventana.winfo_exists():
            self.ventana = tk.Tk()  # ✅ Se convierte en ventana raíz, no subordinada
            self.ventana.title("¡Peso Excesivo!")
            self.ventana.geometry("350x100")
            self.ventana.resizable(False, False)
            self.ventana.attributes("-topmost", True)  # Se mantiene al frente de todo
            self.ventana.lift()                        # La eleva explícitamente
            self.ventana.focus_force()                 # Le da foco de inmediato
            self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)

            tk.Label(self.ventana,
                     text=f"⚠️ Peso actual: {peso} kg\nSupera los 80,000 kg",
                     font=("Arial", 12)).pack(pady=20)

    def cerrar(self):
        if self.ventana and self.ventana.winfo_exists():
            print("✅ Cerrando ventana de peso excesivo")
            self.ventana.destroy()
            self.ventana = None
# Socket para transmitir peso actual al módulo 3
def iniciar_socket():
    HOST = "127.0.0.1"
    PORT = 5000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"🟢 Servidor socket en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                respuesta = {"peso": config.peso_actual, "timestamp": now}
                conn.sendall(json.dumps(respuesta).encode())

# Lógica principal
def verificar_peso():
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado. Usa modulo2_configuracion.py.")
        return

    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=0.05)
            ser.reset_input_buffer()  # ✅ Limpia el búfer de entrada para quitar residuos fantasmas en el puerto com
            print(f"✅ Conectado a {PUERTO_CONFIGURADO}")
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, reintentando...")
            time.sleep(2)

    print("▶️ Iniciando monitoreo de la báscula...")

    root = tk.Tk()
    root.withdraw()

    ventana_desconexion = VentanaDesconexion(root)
    ventana_alerta_peso = VentanaAlertaPeso()
    proceso_modulo3 = None
    tiempo_sin_datos = 0
    intervalo_reconexion = 30

    datos_validos_previos = 0
    esperando_datos = True

    while True:
        root.update()

        try:
            raw_line = ser.readline()
            if not raw_line:
                tiempo_sin_datos += 1
                if tiempo_sin_datos >= intervalo_reconexion:
                    print("⚠️ Sin datos del COM.")
                    ventana_alerta_peso.cerrar()  # ✅ Cerramos alerta si no hay datos
            else:
                try:
                    linea = raw_line.decode('utf-8').strip()
                except UnicodeDecodeError:
                    print("⚠️ Error de codificación en los datos recibidos.")
                    tiempo_sin_datos += 1
                    continue

                if re.search(r"[+-]\s*\d+\s*kg", linea):
                    # 🧹 Esperar 2 lecturas válidas antes de procesar normalmente para evitar residuos fantasma del puerto com
                    if esperando_datos:
                        datos_validos_previos += 1
                        print(f"⏳ Esperando datos válidos ({datos_validos_previos}/2): {linea}")
                        if datos_validos_previos < 2:
                            continue
                        else:
                            esperando_datos = False                    
                    
                    tiempo_sin_datos = 0
                    ventana_desconexion.cerrar()
                    print(f"📥 Peso recibido: {linea}")
                    match = re.search(r"[+-]\s*(\d+)\s*kg", linea)
                    if match:
                        peso = int(match.group(1))
                        config.peso_actual = peso
                        #verificamos si el peso es mayor a 80 toneladas para abir aviso de sobrepeso
                        if peso >= 80000:
                            ventana_alerta_peso.mostrar(peso)
                        else:
                            ventana_alerta_peso.cerrar()
                        #verificamos si el peso es mayor a 300 para abrir el modulo 3
                        if peso >= 300:
                            if proceso_modulo3 is None or proceso_modulo3.poll() is not None or not psutil.pid_exists(proceso_modulo3.pid):
                                print(f"🚨 Peso alto detectado: {peso} kg")
                                proceso_modulo3 = ejecutar_modulo3()
                            else:
                                print("⏳ módulo3 ya está abierto.")
                        else:
                            print(f"✅ Peso bajo: {peso} kg")
                else:
                    tiempo_sin_datos += 1
                    print("⚠️ Línea no válida o vacía recibida.")

        except serial.SerialException:
            print("❌ Conexión perdida con el puerto.")
            tiempo_sin_datos += 1
            ventana_desconexion.mostrar()
            ventana_desconexion.verificar_estado()

        if tiempo_sin_datos >= intervalo_reconexion:
            ventana_desconexion.mostrar()
            ventana_desconexion.verificar_estado()

        time.sleep(0.05)

# Inicia servidor socket y monitoreo
if __name__ == "__main__":
    threading.Thread(target=iniciar_socket, daemon=True).start()
    verificar_peso()
