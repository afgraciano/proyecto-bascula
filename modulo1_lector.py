# modulo1_lector.py

import serial               # Para comunicación con el puerto serial
import time                 # Para manejar pausas de tiempo
import os                   # Para operaciones con archivos y rutas
import subprocess           # Para ejecutar otro script (modulo3)
import tkinter as tk        # Para la interfaz gráfica
import re                   # Para extraer peso del texto usando expresiones regulares
from config import PUERTO_CONFIGURADO  # Puerto configurado desde otro archivo
import config  # Puerto configurado desde otro archivo

# Función para ejecutar el módulo3 cuando se detecta peso alto
def ejecutar_modulo3():
    ruta_modulo3 = os.path.join(os.path.dirname(__file__), 'modulo3_servicio.py')
    return subprocess.Popen(["python", ruta_modulo3], shell=True)

# Clase que maneja la ventana emergente cuando no se reciben datos de la báscula
class VentanaDesconexion:
    def __init__(self, root):
        self.root = root              # Referencia a la ventana principal oculta
        self.ventana = None           # Ventana emergente de advertencia
        self.activa = False           # Estado: si ya está mostrada o no

    def mostrar(self):
        if self.activa:
            return  # Si ya está activa, no hace nada
        self.activa = True

        # Crear ventana emergente
        self.ventana = tk.Toplevel(self.root)
        self.ventana.title("Desconexión de báscula")
        self.ventana.geometry("300x170")
        self.ventana.resizable(False, False)

        # Hacer que esté siempre al frente
        self.ventana.attributes("-topmost", True)
        self.ventana.lift()
        self.ventana.focus_force()

        # Deshabilitar botón de cerrar (X)
        self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)

        # Etiqueta de advertencia
        label = tk.Label(self.ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11))
        label.pack(pady=10)

        # Botón: Corte de energía
        boton1 = tk.Button(self.ventana, text="Corte de energía", width=25,
                           command=lambda: self.cerrar("Corte de energía"))
        boton1.pack(pady=5)

        # Botón: Desconexión de cable
        boton2 = tk.Button(self.ventana, text="Desconexión de cable", width=25,
                           command=lambda: self.cerrar("Desconexión de cable"))
        boton2.pack(pady=5)

    # Cerrar la ventana y registrar motivo si se indica
    def cerrar(self, motivo=None):
        if motivo:
            print(f"📝 Usuario indicó: {motivo}")
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.destroy()
        self.activa = False

    # Verifica si la ventana está minimizada y la restaura si es necesario
    def verificar_estado(self):
        if self.ventana and self.ventana.winfo_exists():
            if self.ventana.state() == 'iconic':
                self.ventana.deiconify()        # Restaurar ventana
                self.ventana.lift()             # Traer al frente
                self.ventana.focus_force()      # Darle foco

# Función principal que se conecta al puerto y monitorea los datos de la báscula
def verificar_peso():
    if PUERTO_CONFIGURADO is None:
        print("⚠️ Puerto no configurado. Usa modulo2_configuracion.py.")
        return

    # Intentar conectar con el puerto configurado
    while True:
        try:
            ser = serial.Serial(PUERTO_CONFIGURADO, 9600, timeout=0.1)  # 🔄 Modificado para mayor velocidad de lectura
            print(f"✅ Conectado a {PUERTO_CONFIGURADO}")
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, reintentando...")
            time.sleep(2)

    print("▶️ Iniciando monitoreo de la báscula...")

    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal

    ventana_desconexion = VentanaDesconexion(root)  # Instancia de la clase ventana
    proceso_modulo3 = None                          # Referencia al proceso de módulo3
    tiempo_sin_datos = 0                            # Contador de segundos sin datos
    intervalo_reconexion = 2                        # Tiempo en segundos para mostrar advertencia

    while True:
        root.update()  # Necesario para que Tkinter procese eventos

        try:
            # Leer una línea cruda del puerto
            raw_line = ser.readline()

            if not raw_line:
                # Si no se recibió nada, incrementar contador
                tiempo_sin_datos += 1
                print("⚠️ Sin datos del COM.")

            else:
                try:
                    # Intentar decodificar la línea
                    linea = raw_line.decode('utf-8').strip()
                except UnicodeDecodeError:
                    # Si hay error de codificación, ignorar la línea
                    print("⚠️ Error de codificación en los datos recibidos.")
                    tiempo_sin_datos += 1
                    continue

                # Validar que la línea contenga el patrón esperado
                if re.search(r"[+-]\s*\d+\s*kg", linea):
                    tiempo_sin_datos = 0         # Reiniciar contador si la línea es válida
                    ventana_desconexion.cerrar() # Cerrar ventana si estaba activa

                    print(f"📥 Peso recibido: {linea}")
                    try:
                        # Buscar patrón: después de '+' seguido de espacios y números hasta 'kg'
                        match = re.search(r"[+-]\s*(\d+)\s*kg", linea)
                        if match:
                           if match:
                            peso = int(match.group(1))  # Extrae el número como entero

                            config.peso_actual = peso   # ✅ Actualiza el valor global para el módulo 3
                        else:
                            continue  # Si no coincide el patrón, ignorar
                    except Exception as e:
                        print(f"⚠️ Error al interpretar peso: {e}")
                        continue   # Ignorar si no es un número válido

                    # Ejecutar módulo 3 si el peso es mayor o igual a 300
                    if peso >= 300:
                        if proceso_modulo3 is None or proceso_modulo3.poll() is not None:
                            print(f"🚨 Peso alto detectado: {peso} kg")
                            proceso_modulo3 = ejecutar_modulo3()
                        else:
                            print("⏳ modulo3 ya está abierto.")
                    else:
                        print(f"✅ Peso bajo: {peso} kg")

                else:
                    # Línea recibida no válida o vacía
                    tiempo_sin_datos += 1
                    print("⚠️ Línea no válida o vacía recibida.")

        except serial.SerialException:
            # Si se pierde conexión con el puerto
            print("❌ Conexión perdida con el puerto.")
            tiempo_sin_datos += 1
            ventana_desconexion.mostrar()
            ventana_desconexion.verificar_estado()  # Restaurar ventana si está minimizada

        # Si se superó el intervalo sin datos válidos, mostrar advertencia
        if tiempo_sin_datos >= intervalo_reconexion:
            ventana_desconexion.mostrar()
            ventana_desconexion.verificar_estado()  # Verificar si está minimizada y restaurarla

        time.sleep(0.25)  # 🔄 Modificado para leer 4 veces por segundo

    ser.close()  # Cerrar el puerto (nunca se alcanza por el while True)
    print("⛔ Finalizando módulo 1.")

# Punto de entrada del programa
if __name__ == "__main__":
    verificar_peso()
