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
import psutil  #  Para verificar si el proceso aún está vivo
from estado_pesajes import pesajes_temporales
import json # Para leer archivo de estado
from integracion_mysql import autenticar_usuario, registrar_personal, guardar_evento_desconexion  # importar esto para la base de datos

# =======================
#  VARIABLES GLOBALES
# =======================

#  Detectar carpeta real del ejecutable o del script
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)

usuario_actual = None  # guardará el usuario logueado

#Direccionamiento de archivos
ARCHIVO_PUNTERO_IMPRESION = ".proceso_impresion_activo"# archivo puntero para bloquear logout en impresión
FLAG_CAMBIO_USUARIO = os.path.join(BASE_DIR, ".cambiar_usuario.flag")# archivo puntero para pedir cambio usuario
RUTA_USUARIO_ACTUAL = os.path.join(BASE_DIR, "usuario_actual.json") #archivo json con usuario logueado
RUTA_ESTADO_PESAJES = os.path.join(BASE_DIR, "estado_actual_pesajes.json")#archivo json con pesajes iniciados
RUTA_CONFIG = os.path.join(BASE_DIR, "config.py") #archivo de configuracion de puerto


# Rutas de modulo3 según entorno
MODULO3_EXE = os.path.join(BASE_DIR, "modulo3_servicio_unificado.exe")
MODULO3_PY  = os.path.join(BASE_DIR, "modulo3_servicio_unificado.py")

#  Se inicializa Tk principal solo una vez como global (sin mainloop)
root = tk.Tk()
root.withdraw()  # Ocultamos la raíz, solo se usa para manejar Toplevel()



# Crear archivo JSON de pesos iniciados si no existe
if not os.path.exists(RUTA_ESTADO_PESAJES):
    with open(RUTA_ESTADO_PESAJES, 'w') as f:
        json.dump({}, f)
    print(f" Archivo creado: {RUTA_ESTADO_PESAJES}")
    
# Crear archivo JSON de usuario logueado si no existe
if not os.path.exists(RUTA_USUARIO_ACTUAL):
    with open(RUTA_USUARIO_ACTUAL, 'w') as f:
        json.dump({}, f)
    print(f" Archivo creado: {RUTA_USUARIO_ACTUAL}")

# Estado de sesión / control de flujo
peso_actual = 0
ultimo_inicio_modulo3 = 0  # Inicializamos si no existe con variable global
LOGOUT_EVENT = threading.Event()  # <- cuando se cambia de usuario, se setea


# =======================
#  FUNCION CENTRADORA VENTANAS
# =======================

#funcion para centrar la ventana
def centrar_ventana(ventana, ancho, alto, margen_superior=200):
    ventana.update_idletasks()
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho - ancho) // 2
    y = margen_superior
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# =======================
#  FUNCIONES MODULO 3
# =======================

#cerrar procesos abiertos de modulo3
def matar_modulo3_abiertos():
    actual_pid = os.getpid()
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["pid"] != actual_pid and "python" in proc.info["name"].lower():
                # Si el proceso ejecuta modulo3, lo matamos
                if any("modulo3_servicio_unificado.py" in str(c) for c in proc.info["cmdline"]):
                    print(f" Cerrando módulo3 antiguo PID={proc.info['pid']}")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

"""Devuelve lista de psutil.Process que corresponden a modulo3 (exe o py) en este mismo directorio."""
def _procesos_modulo3_en_ejecucion():
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
        print(" No hay instancias de módulo3 para cerrar.")
        return
    print(" Intentando cerrar módulo3, PIDs:", [p.pid for p in procs])
    # terminate
    for p in procs:
        try: p.terminate()
        except Exception as e: print(f"⚠️ terminate() falló PID {p.pid}: {e}")
    _, vivos = psutil.wait_procs(procs, timeout=timeout)
    # kill si aún siguen
    if vivos:
        for p in vivos:
            try: 
                print(f" Forzando kill() PID {p.pid}")
                p.kill()
            except Exception as e:
                print(f" kill() falló PID {p.pid}: {e}")


# =======================
#  FUNCIONES CONFIG.PY-PUERTO
# =======================

# Carga o recarga el archivo config.py desde BASE_DIR sin importar global "config"
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
 
 

# =======================
#  LOGIN (BLOQUEANTE)
# =======================
#funcion para Ventana de login obligatoria. Hasta que no se loguee el usuario no se abre nada más.
#def mostrar_login():
def mostrar_login_bloqueante():
    global usuario_actual
    usuario_actual = None  # limpia usuario previo
    LOGOUT_EVENT.clear()  # ciclo nuevo
    
    ventana = tk.Toplevel(root)
    ventana.title("Login - Usuario Autorizado")
    centrar_ventana(ventana, 350, 250)

    # Mantener ventana al frente
    ventana.attributes("-topmost", True)
    ventana.lift()
    ventana.focus_force()
    
    # --- Campos ---
    tk.Label(ventana, text="Login:").pack(pady=2)
    entry_login = tk.Entry(ventana)
    entry_login.pack()
    #entry_login.focus_set()   # 🔹 Foco inicial en login

    tk.Label(ventana, text="Contraseña:").pack(pady=2)
    entry_pass = tk.Entry(ventana, show="*")
    entry_pass.pack()

    #  Checkbox para mostrar/ocultar contraseña
    var_mostrar = tk.BooleanVar(value=False)
    def toggle_password():
        entry_pass.config(show="" if var_mostrar.get() else "*")
    tk.Checkbutton(ventana, text="Mostrar contraseña", variable=var_mostrar, command=toggle_password).pack()

    # Botón de ingresar
    def intentar_login(event=None):  # aceptar Enter también
        nonlocal ventana
        global usuario_actual
        login = entry_login.get().strip()
        password = entry_pass.get().strip()
        user = autenticar_usuario(login, password)
        if user:
            usuario_actual = user
            # Guardar usuario actual en JSON para que modulo3 lo lea
            try:
                with open(RUTA_USUARIO_ACTUAL, "w") as f:
                    json.dump({
                        "id_autorizado": user["id_autorizado"],
                        "nombre": user["nombre"],
                        "login": user["login"]
                    }, f)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo de sesión.\n{e}")
                return
                        
            messagebox.showinfo("Acceso concedido", f"Bienvenido {user['nombre']}")
            ventana.destroy()        
        else:
            # No se destruye la ventana, solo se muestra el error y se queda en el login
            messagebox.showerror("Error", "Login o contraseña incorrectos. Intente de nuevo")

    def abrir_registro():
        ventana.destroy()
        mostrar_registro()
        # volver a login
        mostrar_login_bloqueante()
        
    tk.Button(ventana, text="Ingresar", command=intentar_login).pack(pady=5)
    tk.Button(ventana, text="Registrarse (nuevo usuario)", command=abrir_registro).pack(pady=5)
    
    # Manejo del Enter en los campos
    def focus_password(event):
        entry_pass.focus_set()
        return "break"
    def submit_login(event):
        intentar_login()
        return "break"

    entry_login.bind("<Return>", focus_password)  # Enter en login → pasa a contraseña
    entry_pass.bind("<Return>", submit_login)     # Enter en pass → login directo

    # 🔹 Foco inicial garantizado (después de dibujar la ventana)
    ventana.after(100, lambda: entry_login.focus_set())
    
    ventana.protocol("WM_DELETE_WINDOW", lambda: None)  # Bloquea cerrar con la X
    ventana.grab_set()
    ventana.focus_force()
    root.wait_window(ventana)   # <- BLOQUEA hasta destroy()
    

#Ventana para registrar nuevo usuario autorizado.
def mostrar_registro():

    ventana = tk.Toplevel(root)
    ventana.title("Registro nuevo personal")
    centrar_ventana(ventana, 350, 320)

    labels = ["Nombre", "Login", "Contraseña", "Cédula"]
    entries = {}
    for l in labels:
        tk.Label(ventana, text=l).pack()
        e = tk.Entry(ventana, show="*" if l == "Contraseña" else None)
        e.pack()
        entries[l] = e

    def registrar():
        nombre = entries["Nombre"].get().strip()
        login = entries["Login"].get().strip()
        password = entries["Contraseña"].get().strip()
        cedula = entries["Cédula"].get().strip()

        # Validaciones
        if not (nombre and login and password and cedula):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        if len(password) < 4 or len(password) > 20:
            messagebox.showerror("Error", "La contraseña debe tener entre 4 y 20 caracteres")
            return

        try:
            registrar_personal(nombre, login, password, cedula)
            messagebox.showinfo("Éxito", "Usuario registrado, vuelva a loguearse")
            ventana.destroy()
            #mostrar_login()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(ventana, text="Registrar", command=registrar).pack(pady=10)
    ventana.protocol("WM_DELETE_WINDOW", lambda: None)
    ventana.grab_set()
    ventana.focus_force()
    root.wait_window(ventana)
    #ventana.mainloop()
    
    
# =======================
# FUNCION DE DESLOGUEO DE SESIÓN
# =======================    

#No abre login aquí. Solo marca logout y limpia sesión. El ciclo principal abrirá login.
def desloguear_usuario(origen="Manual"):
    global usuario_actual

    #  No se puede cerrar sesión si hay impresión activa
    if os.path.exists(ARCHIVO_PUNTERO_IMPRESION):
        messagebox.showwarning("Impresión en curso", "No puede cambiar de usuario mientras haya un tiquete abierto.")
        return

    if usuario_actual:
        usuario_actual = None
        # Borrar archivo usuario_actual.json si existe
        if os.path.exists(RUTA_USUARIO_ACTUAL):
            try:
                os.remove(RUTA_USUARIO_ACTUAL)
                # Eliminado sin mostrar nada
            except Exception:
                # Si quieres avisar en ventana:
                messagebox.showwarning("Aviso", "No se pudo eliminar usuario_actual.json")
                pass
        try:
            cerrar_todos_modulo3(timeout=1.0)  #  aseguramos cierre de modulo3 si estaba abierto
        except:
            pass
    LOGOUT_EVENT.set()  # <- hará que verificar_peso() retorne


# =======================
#  FUNCIONES VENTANAS
# =======================

# Ventana Alerta por desconexión
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
        self.ventana.withdraw()  #  Oculta la ventana antes de mostrarla
        self.ventana.title("Desconexión de báscula")
        self.ventana.resizable(False, False)
        self.ventana.attributes("-topmost", True)
        self.ventana.lift()
        self.ventana.focus_force()
        self.ventana.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Centrar la ventana en la pantalla
        centrar_ventana(self.ventana, 300, 170, margen_superior=200)  # Puedes ajustar el margen si quieres más arriba

        # Crear contenido
        tk.Label(self.ventana, text="Báscula desconectada.\nSeleccione la causa:", font=("Arial", 11)).pack(pady=10)
        tk.Button(self.ventana, text="Corte de energía", width=25,
                  command=lambda: self.cerrar("Corte de energía")).pack(pady=5)
        
        tk.Button(self.ventana, text="Desconexión de cable", width=25,
                  command=lambda: self.cerrar("Desconexión de cable")).pack(pady=5)
        # Cambiar usuario: llama directamente a desloguear_usuario()
        tk.Button(self.ventana, text="Cambiar usuario",
                  command=lambda: self.cerrar("Cambio de usuario autorizado")).pack(pady=5)
        self.ventana.deiconify()  # Ahora sí mostrar centrada
        
   
    def cerrar(self, motivo=None):
        if motivo:
            print(f" Usuario indicó: {motivo}")
            guardar_evento_desconexion(motivo)

        if self.ventana and self.ventana.winfo_exists():
            self.ventana.destroy()
        self.activa = False

        if motivo == "Cambio de usuario autorizado":
            desloguear_usuario("Desconexion")

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
            self.ventana = tk.Toplevel()  # Se convierte en ventana raíz, no subordinada
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
            print(" Cerrando ventana de peso excesivo")
            self.ventana.destroy()
            self.ventana = None
            
            
# =======================
#  SOCKET (PESO EN TIEMPO REAL PARA MÓDULO 3)
# =======================
def iniciar_socket():
    #global peso_actual   #  NECESARIO para que lea el valor actualizado
    HOST = "127.0.0.1"
    PORT = 5000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f" Servidor socket en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # usamos peso_actual local
                respuesta = {"peso": peso_actual, "timestamp": now}
                print(f"[SOCKET] Conexión desde {addr} -> enviando: {respuesta}")
                conn.sendall(json.dumps(respuesta).encode())
                


"""def iniciar_socket():
    global peso_actual
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 5000))
    server.listen()

    print("Servidor socket en 127.0.0.1:5000")

    while True:
        conn, addr = server.accept()
        with conn:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            respuesta = {"peso": peso_actual, "timestamp": now}
            print(f"[SOCKET] {addr} -> {respuesta}")
            conn.sendall(json.dumps(respuesta).encode())"""

# =======================
#  EJECUTAR / CERRAR MÓDULO 3
# =======================

# Ejecuta módulo 3 de forma distinta si está empaquetado en exe o no

def ejecutar_modulo3():
    if not os.path.exists(RUTA_USUARIO_ACTUAL):
        messagebox.showwarning(
            "Usuario no autorizado",
            "No hay usuario autorizado logueado.\nDebe iniciar sesión antes de abrir módulo 3."
        )
        #mostrar_login()  # fuerza la ventana de login
        return None
    
    if getattr(sys, 'frozen', False):  # Significa que estamos empaquetados con PyInstaller analizando .exe
        ruta = MODULO3_EXE
        if not os.path.exists(ruta):
            messagebox.showerror(
                "Error",
                f"No se encontró el archivo ejecutable:\n{ruta}"
            )
            return None
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen([ruta], startupinfo=startupinfo)
    else:  # Modo desarrollo normal (con Python instalado) analizando .py
        ruta = MODULO3_PY
        if not os.path.exists(ruta):
            messagebox.showerror(
                "Error",
                f"No se encontró el archivo de Python:\n{ruta}"
            )
            return None
        return subprocess.Popen([sys.executable, ruta])

# Verifica si el proceso aún está vivo
def proceso_activo(proceso):
    if getattr(sys, 'frozen', False):  # en exe revisa por psutil
        return hay_modulo3_activo()
    return proceso is not None and proceso.poll() is None and psutil.pid_exists(proceso.pid)



# =======================
#  LÓGICA PRINCIPAL
# =======================

# REVISA SI ESTA FUNCIONANDO PUERTO, ABRE VENTANA DE DESCONEXION, REVISA PESAJE 0KG
#Loop principal de conexión/lectura/acciones de módulo3. Retorna cuando se hace logout.
def verificar_peso():
    global peso_actual# vamos a actualizar la variable local con la global
    global ultimo_inicio_modulo3# vamos a actualizar la variable local con la global
    
    LOGOUT_EVENT.clear()
    
    cfg = cargar_config()    
    if peso_actual is None:
        peso_actual = 0  # Evita error si el socket lo consulta antes de recibir datos

    while not cfg or not hasattr(cfg, "PUERTO_CONFIGURADO") or not puerto_disponible(cfg.PUERTO_CONFIGURADO):
        if LOGOUT_EVENT.is_set():   # por si hacen logout aquí
            return
        print("Puerto no configurado o no disponible.")
        print("Abra ConfigBascula para establecer el puerto.")
        #root_temp = tk.Tk()
        #root_temp.withdraw()
        messagebox.showwarning("Puerto no disponible", "Abra ConfigBascula para configurar el puerto.")
        #root_temp.destroy()
        esperar_configuracion()
        cfg = cargar_config()
        if peso_actual is None:
            peso_actual = 0

    PUERTO_ACTUAL = cfg.PUERTO_CONFIGURADO
    print(f" Conectando a {PUERTO_ACTUAL}...")
    
    ser = None # Inicializamos ser para evitar NameError si nunca se abre
    while True:
        if LOGOUT_EVENT.is_set():
            return
        try:
            if not puerto_disponible(PUERTO_ACTUAL):
                raise serial.SerialException("Puerto no disponible")
            ser = serial.Serial(PUERTO_ACTUAL, 9600, timeout=0.05)
            ser.reset_input_buffer()
            print(f"Conectado a {PUERTO_ACTUAL}")
            tiempo_sin_datos = 0  # 🔹 Reset tras conexión exitosa
            break
        except serial.SerialException:
            print("Puerto no disponible, esperando reconfiguración...")
            esperar_configuracion()
            cfg = cargar_config()
            if cfg and hasattr(cfg, "PUERTO_CONFIGURADO"):
                PUERTO_ACTUAL = cfg.PUERTO_CONFIGURADO

    print(" Iniciando monitoreo de la báscula...")

    #root = tk.Tk()
    #root.withdraw()
    ventana_desconexion = VentanaDesconexion(root)
    ventana_alerta_peso = VentanaAlertaPeso()
    proceso_modulo3 = None  # inicializamos el proceso aquí
    tiempo_sin_datos = 0
    intervalo_reconexion = 10
    datos_validos_previos = 0
    esperando_datos = True

    try:  # 🔹  protección para cierre seguro del puerto
        #while True:
        while not LOGOUT_EVENT.is_set():
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
                        print(" Sin datos del COM.")
                        ventana_alerta_peso.cerrar()  #  Cerramos alerta si no hay datos
                        ventana_desconexion.mostrar()
                        ventana_desconexion.verificar_estado()
                else:
                    try:
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                    except Exception:
                        print("Error de codificación en los datos recibidos.")
                        tiempo_sin_datos += 1
                        continue

                    if re.search(r"[+-]\s*\d+\s*kg", linea):
                        # Esperar 2 lecturas válidas antes de procesar normalmente para evitar residuos fantasma del puerto com
                        if esperando_datos:
                            datos_validos_previos += 1
                            print(f"Esperando datos válidos ({datos_validos_previos}/2): {linea}")
                            if datos_validos_previos < 2:
                                continue
                            else:
                                esperando_datos = False                    
                        
                        tiempo_sin_datos = 0
                        ventana_desconexion.cerrar()
                        print(f"Peso recibido: {linea}")
                        match = re.search(r"[+-]\s*(\d+)\s*kg", linea)
                        if match:
                            peso = int(match.group(1))
                            peso_actual = peso   #  actualizamos la variable local
                            
                                                  
                            #verificamos si el peso es mayor a 80 toneladas para abir aviso de sobrepeso
                            if peso >= 80000:
                                ventana_alerta_peso.mostrar(peso)
                            else:
                                ventana_alerta_peso.cerrar()
                            
                            # Verifica estado de pesajes / impresión
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
                            
                            # REGLAS PARA ABRIR MODULO 3 SI PESO>300 O JSON TIENE PESAJES ABIERTOS
                            # Control de tiempo mínimo entre lanzamientos para evitar parpadeo                            
                            TIEMPO_ESPERA_INICIO = 3 # segundos
                            if peso >= 300 or hay_pesaje_abierto:
                                tiempo_actual = time.time()
                                if (not proceso_activo(proceso_modulo3)) and (tiempo_actual - ultimo_inicio_modulo3 > TIEMPO_ESPERA_INICIO):
                                    # En .exe validamos si ya hay una instancia corriendo ANTES de abrir otra
                                    if getattr(sys, 'frozen', False) and hay_modulo3_activo():
                                        print("módulo3 ya está abierto (detectado con psutil), no se abre otro.")
                                    else:
                                        print(f"Activando módulo3 (peso={peso} kg, pesajes_abiertos={hay_pesaje_abierto})")
                                        proceso_modulo3 = ejecutar_modulo3()
                                        ultimo_inicio_modulo3 = tiempo_actual
                                else:
                                    print("módulo3 ya está abierto o se inició hace poco, esperando...")
                            # solo cierra modulo3 si peso<10 y NO hay pesajes
                            elif peso < 10 and not hay_pesaje_abierto:
                                if proceso_activo(proceso_modulo3) or (getattr(sys, 'frozen', False) and hay_modulo3_activo()):
                                    print(" Cerrando módulo3 (peso < 10 kg y sin pesajes abiertos)")
                                    if getattr(sys, 'frozen', False):  
                                        cerrar_todos_modulo3(timeout=1.0)  # en exe, cerrar todas
                                    else:
                                        try:
                                            proceso_modulo3.terminate()
                                            time.sleep(0.5)
                                            if proceso_activo(proceso_modulo3):
                                                print("Terminate no fue suficiente, forzando kill()")
                                                proceso_modulo3.kill()
                                            else:
                                                print("módulo3 cerrado correctamente")
                                        except Exception as e:
                                            print(f"Error al cerrar módulo3: {e}")
                                    proceso_modulo3 = None
                                else:
                                    print(f" Peso bajo y sin pesajes abiertos ({peso} kg)")
                    else:
                        tiempo_sin_datos += 1
                        if tiempo_sin_datos >= intervalo_reconexion:
                            ventana_desconexion.mostrar()
                            ventana_desconexion.verificar_estado()

            except serial.SerialException:
                print("Conexión perdida con el puerto.")
                tiempo_sin_datos += 1
                ventana_desconexion.mostrar()
                ventana_desconexion.verificar_estado()

            if tiempo_sin_datos >= intervalo_reconexion:
                ventana_desconexion.mostrar()
                ventana_desconexion.verificar_estado()

            # Revisar si módulo3 pidió cambio de usuario y lo cerrarmos
            
            if os.path.exists(FLAG_CAMBIO_USUARIO):
                print(" Solicitud de cambio de usuario recibida desde módulo3.")
                try:
                    os.remove(FLAG_CAMBIO_USUARIO)
                except: 
                    pass
                 # Guardamos evento en la base de datos
                try:
                    guardar_evento_desconexion("Cambio de usuario autorizado")
                    print(" Evento de cambio de usuario registrado en la BD.")
                except Exception as e:
                    print(f" Error al guardar evento de desconexión (cambio usuario): {e}")

                # 🔹 Cerramos sesión / matamos módulo3
                desloguear_usuario("Cambio desde módulo3")

            
            time.sleep(0.02)
            
    finally:
        try:
            ventana_alerta_peso.cerrar()
            ventana_desconexion.cerrar()
        except Exception:
            pass
        if ser and ser.is_open:  #  Comprobación segura antes de cerrar
            ser.close()
           
        # Reforzamos: matar cualquier módulo3 que aún quede abierto
        try:
            cerrar_todos_modulo3(timeout=1.0)  # Asegura que no queden instancias vivas de módulo3
        except Exception as e:
            print(f"Error cerrando módulo3 en finally: {e}")

# Inicia servidor socket y monitoreo
"""if __name__ == "__main__":
    threading.Thread(target=iniciar_socket, daemon=True).start()
    mostrar_login()   #  Login obligatorio antes de todo. Esto bloquea hasta que se loguee el usuario
    verificar_peso()"""

"""if __name__ == "__main__":
    threading.Thread(target=iniciar_socket, daemon=True).start()
    mostrar_login()   # crea la ventana de login
    root.mainloop()   # mantiene la interfaz viva hasta que cierre login
    #verificar_peso()  # se ejecuta solo después de login exitoso y destroy()
    """

# =======================
#  MAIN LOOP
# =======================

if __name__ == "__main__":
    # Hilo del socket que entrega peso_actual a módulo 3
    threading.Thread(target=iniciar_socket, daemon=True).start()
    
    # Hook para cierre limpio de la ventana principal
    def salir_seguro():
        print(" Cerrando aplicación: matando todos los módulo3...")
        try:
            cerrar_todos_modulo3(timeout=1.0)
        except Exception as e:
            print(f"Error cerrando módulo3 en salida: {e}")
        root.destroy()
        os._exit(0)  # 🔹 mata hilos residuales (socket, etc.)

    root.protocol("WM_DELETE_WINDOW", salir_seguro)

    # Ciclo principal claro: LOGIN -> VERIFICAR -> (si logout) vuelve a LOGIN
    while True:
        mostrar_login_bloqueante()   # Paso 1: login obligatorio
        if usuario_actual is None:
            # Si cerraran la app, rompemos
            break
        verificar_peso()             # Paso 2/3: desconexión + control de módulo3
  # Si retorna es porque hubo logout o error de puerto. Repite el ciclo.

