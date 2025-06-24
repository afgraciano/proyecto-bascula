import serial               # Comunicación con puerto serial
import time                 # Delays y manejo de tiempos
import os                   # Rutas de archivo
import subprocess           # Ejecutar procesos externos
import tkinter as tk        # Interfaz gráfica
import re                   # Expresiones regulares para extraer peso
import socket               # Comunicación de red local
import json                 # Para formatear datos transmitidos
from datetime import datetime
from config import PUERTO_CONFIGURADO
import config
import threading            # Hilos para multitarea

# Ejecuta módulo 3 en un nuevo proceso
def ejecutar_modulo3():
    ruta_modulo3 = os.path.join(os.path.dirname(__file__), 'modulo3_servicio_unificado.py')
    return subprocess.Popen(["python", ruta_modulo3], shell=True)

# Clase que muestra alerta de desconexión si no se recibe dato
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

        label = tk.Label(self.ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11))
        label.pack(pady=10)

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

# Nueva clase para mostrar alerta de sobrepeso sin bloquear el hilo
class VentanaAlertaPeso:
    def __init__(self, root):
        self.root = root  # Aunque guardamos root, no lo usaremos como padre para que no quede debajo de otras ventanas
        self.ventana = None

    def mostrar(self, peso):
        # Solo mostrar si no existe ya una ventana activa
        if self.ventana is None or not self.ventana.winfo_exists():
            self.ventana = tk.Toplevel()  # ❌ No usar self.root como padre para que sea totalmente independiente
            self.ventana.title("¡Peso Excesivo!")
            self.ventana.geometry("350x100")
            self.ventana.resizable(False, False)

            self.ventana.attributes("-topmost", True)  # 🟢 Siempre al frente
            self.ventana.lift()                        # 🟢 Traer al frente explícitamente
            self.ventana.focus_force()                 # 🟢 Darle foco para evitar quedar oculta

            self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)  # Desactiva cierre manual

            # Etiqueta con mensaje de peso alto
            tk.Label(self.ventana,
                     text=f"⚠️ Peso actual: {peso} kg\nSupera los 80,000 kg",
                     font=("Arial", 12)).pack(pady=20)

    def cerrar(self):
        # Cierra la ventana si existe
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.destroy()
# Servidor socket para enviar el peso actual al módulo 3
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

# Lógica principal: lectura de puerto y manejo de eventos
def verificar_peso():
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado. Usa modulo2_configuracion.py.")
        return

    # Conexión al puerto
    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=0.05)
            print(f"✅ Conectado a {PUERTO_CONFIGURADO}")
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, reintentando...")
            time.sleep(2)

    print("▶️ Iniciando monitoreo de la báscula...")

    root = tk.Tk()
    root.withdraw()  # Oculta ventana principal

    ventana_desconexion = VentanaDesconexion(root)
    ventana_alerta_peso = VentanaAlertaPeso(root)  # Alerta por sobrepeso
    proceso_modulo3 = None
    tiempo_sin_datos = 0
    intervalo_reconexion = 30  # tolerancia 1.5s

    while True:
        root.update()

        try:
            raw_line = ser.readline()
            if not raw_line:
                tiempo_sin_datos += 1
                if tiempo_sin_datos >= intervalo_reconexion:
                    print("⚠️ Sin datos del COM.")
            else:
                try:
                    linea = raw_line.decode('utf-8').strip()
                except UnicodeDecodeError:
                    print("⚠️ Error de codificación en los datos recibidos.")
                    tiempo_sin_datos += 1
                    continue

                if re.search(r"[+-]\s*\d+\s*kg", linea):
                    tiempo_sin_datos = 0
                    ventana_desconexion.cerrar()
                    print(f"📥 Peso recibido: {linea}")
                    match = re.search(r"[+-]\s*(\d+)\s*kg", linea)
                    if match:
                        peso = int(match.group(1))
                        config.peso_actual = peso

                        # Mostrar alerta si sobrepasa 80000, cerrar si baja
                        if peso >= 80000:
                            ventana_alerta_peso.mostrar(peso)
                        else:
                            ventana_alerta_peso.cerrar()

                        # Abrir módulo 3 si peso ≥ 300
                        if peso >= 300:
                            if proceso_modulo3 is None or proceso_modulo3.poll() is not None:
                                print(f"🚨 Peso alto detectado: {peso} kg")
                                proceso_modulo3 = ejecutar_modulo3()
                            else:
                                print("⏳ modulo3 ya está abierto.")
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

# Punto de entrada
if __name__ == "__main__":
    threading.Thread(target=iniciar_socket, daemon=True).start()
    verificar_peso()
