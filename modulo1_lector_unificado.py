import serial
import importlib
import time
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox #para mostrar alertas
import re
import socket
import threading
import signal
from datetime import datetime
#from config import PUERTO_CONFIGURADO
#import config
import psutil  # ✅ Para verificar si el proceso aún está vivo
from estado_pesajes import pesajes_temporales
import json # Para leer archivo de estado
from integracion_mysql import guardar_evento_desconexion  # 👈 Asegúrate de importar esto para la base de datos



# 🔹 Detectar carpeta real del ejecutable o del script
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)

RUTA_CONFIG = os.path.join(BASE_DIR, "config.py")
RUTA_ESTADO_PESAJES = os.path.join(BASE_DIR, "estado_actual_pesajes.json")

# Rutas de modulo3 según entorno
MODULO3_EXE = os.path.join(BASE_DIR, "modulo3_servicio_unificado.exe")
MODULO3_PY  = os.path.join(BASE_DIR, "modulo3_servicio_unificado.py")

# 🟢 ULTIMA MODIFICACION: Se inicializa Tk principal solo una vez
root = tk.Tk()
root.withdraw()  # Ocultamos la raíz, solo se usa para manejar Toplevel()

def _procesos_modulo3_en_ejecucion():
    """Devuelve lista de psutil.Process que corresponden a modulo3 (exe o py) en este mismo directorio."""
    procs = []
    frozen = getattr(sys, 'frozen', False)
    for p in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'cwd']):
        try:
            info = p.info
            name = (info.get('name') or '').lower()
            exe  = info.get('exe') or ''
            cwd  = info.get('cwd') or ''
            cmd  = info.get('cmdline') or []

            if frozen:
                # Buscar por ejecutable exacto o por nombre + carpeta
                if exe and os.path.exists(exe):
                    try:
                        if os.path.samefile(exe, MODULO3_EXE):
                            procs.append(p); continue
                    except FileNotFoundError:
                        pass
                if name == os.path.basename(MODULO3_EXE).lower() and cwd:
                    try:
                        if os.path.samefile(cwd, BASE_DIR):
                            procs.append(p); continue
                    except FileNotFoundError:
                        pass
            else:
                # Modo .py: buscar el script en la cmdline
                for arg in cmd:
                    if isinstance(arg, str) and arg.endswith(".py"):
                        try:
                            if os.path.samefile(os.path.abspath(arg), os.path.abspath(MODULO3_PY)):
                                procs.append(p); break
                        except FileNotFoundError:
                            pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs

def hay_modulo3_activo():
    return len(_procesos_modulo3_en_ejecucion()) > 0

def cerrar_todos_modulo3(timeout=2.0):
    """Intenta cerrar TODAS las instancias de modulo3 (no solo la lanzada por este proceso)."""
    procs = _procesos_modulo3_en_ejecucion()
    if not procs:
        print("✅ No hay instancias de módulo3 para cerrar.")
        return
    print("🟡 Intentando cerrar módulo3, PIDs:", [p.pid for p in procs])
    # terminate
    for p in procs:
        try: p.terminate()
        except Exception as e: print(f"⚠️ terminate() falló PID {p.pid}: {e}")
    _, vivos = psutil.wait_procs(procs, timeout=timeout)
    # kill si aún siguen
    if vivos:
        for p in vivos:
            try: 
                print(f"⚠️ Forzando kill() PID {p.pid}")
                p.kill()
            except Exception as e:
                print(f"❌ kill() falló PID {p.pid}: {e}")

# Crear archivo JSON si no existe
if not os.path.exists(RUTA_ESTADO_PESAJES):
    with open(RUTA_ESTADO_PESAJES, 'w') as f:
        json.dump({}, f)
    print(f"🟢 Archivo creado: {RUTA_ESTADO_PESAJES}")

# 🟢 MODIFICADO: usamos peso_actual local, no en config
peso_actual = 0

ultimo_inicio_modulo3 = 0  # Inicializamos si no existe con variable global

# 🟢 MODIFICADO: Carga o recarga el archivo config.py desde BASE_DIR sin importar global "config"
import importlib.util
def cargar_config():
    try:
        if os.path.exists(RUTA_CONFIG):
            spec = importlib.util.spec_from_file_location("config_local", RUTA_CONFIG)
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)
            return cfg
        return None
    except Exception as e:
        print(f"Error cargando config: {e}")
        return None

# Verifica si el puerto COM está disponible
def puerto_disponible(puerto):
   
    try:
        ser = serial.Serial(puerto, 9600)
        ser.close()
        return True
    except serial.SerialException:
        return False

# Espera a que se modifique config.py cuando no hay puerto válido.
def esperar_configuracion():
   
    ultima_modificacion = os.path.getmtime(RUTA_CONFIG) if os.path.exists(RUTA_CONFIG) else 0
    print("⚠ No se encontró un puerto válido. Abra ConfigBascula para configurarlo.")
    while True:
        time.sleep(1)
        if os.path.exists(RUTA_CONFIG):
            nueva_modificacion = os.path.getmtime(RUTA_CONFIG)
            if nueva_modificacion != ultima_modificacion:
                ultima_modificacion = nueva_modificacion  # 🔹 Actualizamos la referencia
                print("✅ Se detectó cambio en config.py. Intentando reconectar...")
                return True
 
 
# Ejecuta módulo 3 de forma distinta si está empaquetado en exe o no
#def ejecutar_modulo3():
    #ruta_modulo3 = os.path.join(BASE_DIR, 'modulo3_servicio_unificado.py')
    #return subprocess.Popen(["python", ruta_modulo3])
    """ruta_modulo3 = os.path.join(BASE_DIR, "modulo3_servicio_unificado.py")

    if getattr(sys, 'frozen', False):  # empaquetado .exe
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen([sys.executable, ruta_modulo3], startupinfo=startupinfo)
    else:  # desarrollo normal con Python
        return subprocess.Popen(["python", ruta_modulo3])"""

def ejecutar_modulo3():
    if getattr(sys, 'frozen', False):  # 👈 Significa que estamos empaquetados con PyInstaller
        ruta_modulo3 = os.path.join(BASE_DIR, "modulo3_servicio_unificado.exe")
        if not os.path.exists(ruta_modulo3):
            print(f"❌ No se encontró {ruta_modulo3}")
            return None
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen([ruta_modulo3], startupinfo=startupinfo)
    else:  # 👈 Modo desarrollo normal (con Python instalado)
        ruta_modulo3 = os.path.join(BASE_DIR, "modulo3_servicio_unificado.py")
        return subprocess.Popen([sys.executable, ruta_modulo3])

# Verifica si el proceso aún está vivo
def proceso_activo(proceso):
    if getattr(sys, 'frozen', False):  # en exe revisa por psutil
        return hay_modulo3_activo()
    return proceso is not None and proceso.poll() is None and psutil.pid_exists(proceso.pid)

#funcion para centrar la ventana
def centrar_ventana(ventana, ancho, alto, margen_superior=200):
    ventana.update_idletasks()
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho - ancho) // 2
    y = margen_superior
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

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
        self.ventana.withdraw()  # 👈 Oculta la ventana antes de mostrarla
        self.ventana.title("Desconexión de báscula")
        self.ventana.resizable(False, False)
        self.ventana.attributes("-topmost", True)
        self.ventana.lift()
        self.ventana.focus_force()
        self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Centrar la ventana en la pantalla
        centrar_ventana(self.ventana, 300, 170, margen_superior=200)  # Puedes ajustar el margen si quieres más arriba

        # Crear contenido
        tk.Label(self.ventana, text="⚠️ Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11)).pack(pady=10)
        tk.Button(self.ventana, text="Corte de energía", width=25,
                  command=lambda: self.cerrar("Corte de energía")).pack(pady=5)
        tk.Button(self.ventana, text="Desconexión de cable", width=25,
                  command=lambda: self.cerrar("Desconexión de cable")).pack(pady=5)
        self.ventana.deiconify()  # 👈 Ahora sí mostrar centrada
        
    def cerrar(self, motivo=None):
        if motivo:
            print(f"📝 Usuario indicó: {motivo}")
            guardar_evento_desconexion(motivo)  # 👈 Aquí se guarda el evento en la base de datos
            
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
            self.ventana = tk.Toplevel()  # ✅ Se convierte en ventana raíz, no subordinada
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
                # 🟢 MODIFICADO: usamos peso_actual local
                respuesta = {"peso": peso_actual, "timestamp": now}
                conn.sendall(json.dumps(respuesta).encode())


# Lógica principal
def verificar_peso():
    global peso_actual# vamos a actualizar la variable local con la global
    global ultimo_inicio_modulo3# vamos a actualizar la variable local con la global
    cfg = cargar_config()
    
    if peso_actual is None:
        peso_actual = 0  # Evita error si el socket lo consulta antes de recibir datos

    while not cfg or not hasattr(cfg, "PUERTO_CONFIGURADO") or not puerto_disponible(cfg.PUERTO_CONFIGURADO):
        print("⚠️ Puerto no configurado o no disponible.")
        print("💡 Abra ConfigBascula para establecer el puerto.")
        root_temp = tk.Tk()
        root_temp.withdraw()
        messagebox.showwarning("Puerto no disponible", "Abra ConfigBascula para configurar el puerto.")
        root_temp.destroy()
        esperar_configuracion()
        cfg = cargar_config()
        if peso_actual is None:
            peso_actual = 0

    PUERTO_ACTUAL = cfg.PUERTO_CONFIGURADO
    print(f"🔌 Conectando a {PUERTO_ACTUAL}...")
    
    ser = None # Inicializamos ser para evitar NameError si nunca se abre
    
    while True:
        try:
            if not puerto_disponible(PUERTO_ACTUAL):
                raise serial.SerialException("Puerto no disponible")
            ser = serial.Serial(PUERTO_ACTUAL, 9600, timeout=0.05)
            ser.reset_input_buffer()
            print(f"✅ Conectado a {PUERTO_ACTUAL}")
            tiempo_sin_datos = 0  # 🔹 Reset tras conexión exitosa
            break
        except serial.SerialException:
            print("❌ Puerto no disponible, esperando reconfiguración...")
            esperar_configuracion()
            cfg = cargar_config()
            """if not hasattr(config, "peso_actual"):
                config.peso_actual = 0"""
            if cfg and hasattr(cfg, "PUERTO_CONFIGURADO"):
                PUERTO_ACTUAL = cfg.PUERTO_CONFIGURADO

    print("▶️ Iniciando monitoreo de la báscula...")

    root = tk.Tk()
    root.withdraw()
    ventana_desconexion = VentanaDesconexion(root)
    ventana_alerta_peso = VentanaAlertaPeso()
    proceso_modulo3 = None  # inicializamos el proceso aquí
    tiempo_sin_datos = 0
    intervalo_reconexion = 10
    datos_validos_previos = 0
    esperando_datos = True

    try:  # 🔹  protección para cierre seguro del puerto
        while True:
            try:  # 🔹  evitar que un error de ventana mate el loop
                # 🔹 MODIFICADO: mover root.update() fuera del flujo pesado, para que GUI responda siempre
                root.update_idletasks()
                root.update()
            except tk.TclError:
                pass
            
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
                            peso_actual = peso   # 🟢 MODIFICADO: actualizamos la variable local
                            
                                                  
                            #verificamos si el peso es mayor a 80 toneladas para abir aviso de sobrepeso
                            if peso >= 80000:
                                ventana_alerta_peso.mostrar(peso)
                            else:
                                ventana_alerta_peso.cerrar()
                            
                            # Verifica si debe abrir o cerrar el módulo 3 con base en peso y pesajes abiertos
                            def hay_pesajes_abiertos():
                                try:
                                    with open(RUTA_ESTADO_PESAJES, 'r') as f:
                                        claves = json.load(f)
                                        return bool(claves)
                                except:
                                    return False

                    
                            def hay_impresion_Proceso():
                                return os.path.exists(os.path.join(BASE_DIR, '.proceso_impresion_activo'))
                            
                            hay_pesaje_abierto = hay_pesajes_abiertos() or hay_impresion_Proceso()

                            # Control de tiempo mínimo entre lanzamientos para evitar parpadeo
                            
                            TIEMPO_ESPERA_INICIO = 3 # segundos
                           
                            # 🟢 solo abre modulo3 si peso>=300 o hay pesajes
                            # 🟢 CORREGIDO: solo abre modulo3 si peso>=300 o hay pesajes
                            if peso >= 300 or hay_pesaje_abierto:
                                tiempo_actual = time.time()
                                if (not proceso_activo(proceso_modulo3)) and (tiempo_actual - ultimo_inicio_modulo3 > TIEMPO_ESPERA_INICIO):
                                    # En .exe validamos si ya hay una instancia corriendo ANTES de abrir otra
                                    if getattr(sys, 'frozen', False) and hay_modulo3_activo():
                                        print("⏳ módulo3 ya está abierto (detectado con psutil), no se abre otro.")
                                    else:
                                        print(f"🚨 Activando módulo3 (peso={peso} kg, pesajes_abiertos={hay_pesaje_abierto})")
                                        proceso_modulo3 = ejecutar_modulo3()
                                        ultimo_inicio_modulo3 = tiempo_actual
                                else:
                                    print("⏳ módulo3 ya está abierto o se inició hace poco, esperando...")

                            
                            # 🟢 CORREGIDO: solo cierra modulo3 si peso<10 y NO hay pesajes
                            elif peso < 10 and not hay_pesaje_abierto:
                                if proceso_activo(proceso_modulo3) or (getattr(sys, 'frozen', False) and hay_modulo3_activo()):
                                    print("🟡 Cerrando módulo3 (peso < 10 kg y sin pesajes abiertos)")
                                    if getattr(sys, 'frozen', False):  
                                        cerrar_todos_modulo3(timeout=1.0)  # en exe, cerrar todas
                                    else:
                                        try:
                                            proceso_modulo3.terminate()
                                            time.sleep(0.5)
                                            if proceso_activo(proceso_modulo3):
                                                print("⚠️ Terminate no fue suficiente, forzando kill()")
                                                proceso_modulo3.kill()
                                            else:
                                                print("✅ módulo3 cerrado correctamente")
                                        except Exception as e:
                                            print(f"❌ Error al cerrar módulo3: {e}")
                                    proceso_modulo3 = None
                                else:
                                    print(f"✅ Peso bajo y sin pesajes abiertos ({peso} kg)")



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

            time.sleep(0.02)
            
    finally:
        if ser and ser.is_open:  # 🔹 Comprobación segura antes de cerrar
            ser.close()

# Inicia servidor socket y monitoreo
if __name__ == "__main__":
    threading.Thread(target=iniciar_socket, daemon=True).start()
    verificar_peso()
