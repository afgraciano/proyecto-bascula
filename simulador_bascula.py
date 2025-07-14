
import serial
import serial.tools.list_ports
import time
import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
import os
from tkinter import messagebox

# Estado de simulación
simulando = [False]
hilo_simulacion = [None]  # Referencia al hilo de simulación
peso_actual = [0]
peso_objetivo = [0]
puerto_simulado = ['COM6']
velocidad = 9600
intervalo_envio = 0.25  # 4 Hz
num_pasos = 24
archivo_config = "config_com.txt"
pasos_pendientes = []
com_posiblemente_bloqueado = [None]  # Marca si un COM fue abierto pero no recibió respuesta


# 💾 Cargar COM guardado previamente
def cargar_com_guardado():
    if os.path.exists(archivo_config):
        with open(archivo_config, "r") as f:
            com = f.read().strip()
            if com:
                puerto_simulado[0] = com
                print(f"✔️ COM guardado encontrado: {com}")

# 💾 Guardar COM seleccionado
def guardar_com_actual():
    with open(archivo_config, "w") as f:
        f.write(puerto_simulado[0])
        print(f"💾 COM guardado: {puerto_simulado[0]}")

# Verifica si el COM existe
def puerto_existe(puerto):
    disponibles = [p.device for p in serial.tools.list_ports.comports()]
    return puerto in disponibles

# 🧾 Formato de línea de salida de báscula
def generar_linea_formato_bascula(peso, estable):
    estado = "ST" if estable else "US"
    return f"{estado},GS,+ {int(peso)}kg\r\n"

# 🔢 Genera pasos para transición de peso
def calcular_pasos(peso_ini, peso_fin):
    pasos = []
    if peso_ini == peso_fin:
        return [peso_ini] * num_pasos
    for i in range(1, num_pasos + 1):
        valor = peso_ini + ((peso_fin - peso_ini) * i / num_pasos)
        pasos.append(round(valor))
    return pasos

# 🔁 Simulación de transmisión de datos por COM
def iniciar_simulacion():
    global com_posiblemente_bloqueado  # Asegúrate de declarar esta variable global si usas dentro de función

    ser = None
    intentos = 0
    max_intentos = 3
    tiempo_espera_inicial = 2  # segundos
    ciclos_minimos = int(tiempo_espera_inicial / intervalo_envio)

    actividad_detectada = False

    while intentos < max_intentos:
        try:
            ser = serial.Serial(puerto_simulado[0], velocidad)
            print(f"✅ Puerto {puerto_simulado[0]} abierto.")
            break
        except Exception as e:
            intentos += 1
            print(f"❌ Intento {intentos}: Error al abrir puerto {puerto_simulado[0]}: {e}")
            if intentos < max_intentos:
                time.sleep(1)
            else:
                print("🚫 No se pudo abrir el puerto después de varios intentos.")
                return

    inicio_simulacion = time.time()
    contador_pesos = 0

    try:
        while simulando[0]:
            if pasos_pendientes:
                peso_actual[0] = pasos_pendientes.pop(0)
                estable = False
            else:
                peso_actual[0] = peso_objetivo[0]
                estable = True

            linea = generar_linea_formato_bascula(peso_actual[0], estable)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Peso: {linea.strip()}")
            ser.write(linea.encode('utf-8'))

            actividad_detectada = True  # ✅ Si llega aquí, hubo transmisión exitosa
            contador_pesos += 1
            time.sleep(intervalo_envio)

            if (time.time() - inicio_simulacion >= tiempo_espera_inicial and
                contador_pesos >= ciclos_minimos and
                not actividad_detectada):
                print(f"⏳ El puerto {puerto_simulado[0]} fue abierto pero no hay actividad inicial...")
                com_posiblemente_bloqueado[0] = puerto_simulado[0]
                root.after(100, lambda: messagebox.showinfo(
                    "Puerto sin actividad",
                    f"El puerto {puerto_simulado[0]} fue abierto pero no hay comunicación.\n\nVerifica que el otro extremo (COM emparejado por com0com) esté activo."
                ))
                break

    except Exception as e:
        print(f"❌ Error durante la simulación con puerto {puerto_simulado[0]}: {e}")
    finally:
        if ser:
            try:
                if ser.is_open:
                    ser.flush()
                    ser.close()
                    print("⛔ Puerto cerrado.")
            except Exception as cerrar_error:
                print(f"⚠️ Error al cerrar el puerto: {cerrar_error}")
            del ser
            time.sleep(0.5)

# ▶️ Botón iniciar/detener simulación
def al_presionar_boton_simulacion():
    if not simulando[0]:
        print(f"🔄 Intentando abrir {puerto_simulado[0]}...")
        simulando[0] = True

        def correr():
            try:
                iniciar_simulacion()
            except Exception as e:
                simulando[0] = False
                msg = f"❌ Error al abrir el puerto {puerto_simulado[0]}:\n{e}"
                print(msg)
                messagebox.showerror("Error de conexión", msg)
                boton_inicio.config(text="Iniciar Simulación")

        hilo_simulacion[0] = threading.Thread(target=correr, daemon=True)
        hilo_simulacion[0].start()
        boton_inicio.config(text="Detener Simulación")
    else:
        simulando[0] = False
        boton_inicio.config(text="Iniciar Simulación")

# ⚖️ Cambiar el peso de destino
def cambiar_peso(nuevo_peso):
    peso_objetivo[0] = nuevo_peso
    pasos = calcular_pasos(peso_actual[0], peso_objetivo[0])
    pasos_pendientes.clear()
    pasos_pendientes.extend(pasos)
    print(f">>> Transición de {peso_actual[0]} kg a {peso_objetivo[0]} kg en {num_pasos} pasos.")

# Entrada manual
def aplicar_peso_manual():
    entrada = entrada_peso.get()
    try:
        valor = int(entrada)
        if valor < 0:
            raise ValueError
        cambiar_peso(valor)
    except ValueError:
        print("⚠️ Ingresa un número entero válido y no negativo.")

# COMs fijos del 1 al 20
def obtener_puertos_disponibles():
    return [f'COM{i}' for i in range(1, 21)]

# 🔃 Actualizar lista de COMs
def actualizar_lista_com():
    puertos_fijos = [f'COM{i}' for i in range(1, 21)]
    disponibles = sorted([p.device for p in serial.tools.list_ports.comports()])
    disponibles_en_rango = [p for p in puertos_fijos if p in disponibles]
    no_disponibles = [p for p in puertos_fijos if p not in disponibles]
    disponibles_marcados = [f'✅ {p}' for p in disponibles_en_rango]
    lista_final = disponibles_marcados + no_disponibles

    seleccion_actual = combobox_com.get().replace("✅ ", "")
    combobox_com['values'] = lista_final

    if seleccion_actual in puertos_fijos:
        if seleccion_actual in disponibles_en_rango:
            combobox_com.set(f'✅ {seleccion_actual}')
        else:
            combobox_com.set(seleccion_actual)
    else:
        combobox_com.set('')

# Cambio manual de COM
def seleccionar_puerto(event):
    if simulando[0]:
        simulando[0] = False
        print("🛑 Deteniendo simulación por cambio de puerto...")
        boton_inicio.config(text="Iniciar Simulación")
        if hilo_simulacion[0] and hilo_simulacion[0].is_alive():
            hilo_simulacion[0].join(timeout=3)
            print("✅ Hilo de simulación detenido correctamente.")

    seleccion = combobox_com.get().replace("✅ ", "")
    puerto_simulado[0] = seleccion
    print(f">>> COM cambiado a: {seleccion}")
    guardar_com_actual()

# Interfaz gráfica
root = tk.Tk()
root.title("Simulador de Báscula Prometalicos")
tk.Label(root, text="Simulador de báscula - US vs ST real").pack(pady=10)

frame_com = tk.Frame(root)
frame_com.pack(pady=5)
tk.Label(frame_com, text="Puerto COM:").pack(side="left")
combobox_com = ttk.Combobox(frame_com, state="readonly", width=10)
combobox_com.pack(side="left", padx=5)
combobox_com.bind("<<ComboboxSelected>>", seleccionar_puerto)
tk.Button(frame_com, text="Actualizar", command=actualizar_lista_com).pack(side="left")

cargar_com_guardado()
actualizar_lista_com()

boton_inicio = tk.Button(root, text="Iniciar Simulación", command=al_presionar_boton_simulacion)
boton_inicio.pack(pady=10)

tk.Label(root, text="Selecciona el peso simulado:").pack(pady=5)
frame_botones = tk.Frame(root)
frame_botones.pack(pady=5)
tk.Button(frame_botones, text="0 kg", width=10, command=lambda: cambiar_peso(0)).grid(row=0, column=0, padx=5)
tk.Button(frame_botones, text="500 kg", width=10, command=lambda: cambiar_peso(500)).grid(row=0, column=1, padx=5)
tk.Button(frame_botones, text="2700 kg", width=10, command=lambda: cambiar_peso(2700)).grid(row=0, column=2, padx=5)
tk.Button(frame_botones, text="10000 kg", width=10, command=lambda: cambiar_peso(10000)).grid(row=0, column=3, padx=5)

tk.Label(root, text="O escribe un peso personalizado (kg):").pack(pady=5)
frame_manual = tk.Frame(root)
frame_manual.pack(pady=5)
entrada_peso = tk.Entry(frame_manual, width=10)
entrada_peso.pack(side="left", padx=5)
tk.Button(frame_manual, text="Aplicar", command=aplicar_peso_manual).pack(side="left", padx=5)

tk.Label(root, text="Formato: US/ST según estado | Cambio exacto en 6s").pack(pady=10)
root.mainloop()
