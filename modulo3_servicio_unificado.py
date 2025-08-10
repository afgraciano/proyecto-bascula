# Importación de módulos necesarios
import tkinter as tk  # Módulo principal para la GUI Para interfaces gráficas
from tkinter import ttk  # Módulo para widgets avanzados (Treeview, Combobox, etc.)
from tkinter import simpledialog, messagebox  # Para cuadros de diálogo simples y mensajes emergentes
import socket  # Para la comunicación con el módulo que lee el peso (modulo1) Comunicación por red local (localhost)
import json  # Para interpretar los datos recibidos en formato JSON
from datetime import datetime  # 🗓️ Usado Para Obtener y registrar fecha y hora exacta del pesaje
import re  # Validaciones con expresiones regulares
import unicodedata  # para permitir caracteres o validación de nombres acentuados

#importamos librerias para manejo de impresoras en windows
import win32print
import win32ui

# Diccionario para almacenar pesos temporales de pesajes parciales (por ID)
# Se importan los diccionarios globales que almacenan pesajes abiertos y cerrados del archivo estado_pesajes.py
# para permitir el acceso y actualización compartida entre módulos (como módulo1 y módulo3)
from estado_pesajes import pesajes_temporales, pesajes_confirmados
import json
import os #realizar operaciones sobre sistema operativo (comprueba archivo existe, elimina archivos, crea carpetas, accede path del sistema, etc.)

from integracion_mysql import guardar_cliente_y_pesaje # importacion para la base de datos

# Lista global para rastrear si hay ventanas de impresión abiertas
ventanas_tiquete_abiertas = []


#defino funcion para imprimir tiquete
def imprimir_tiquete(texto, impresora=None):
    if impresora is None:
        impresora = win32print.GetDefaultPrinter()

    hprinter = win32print.OpenPrinter(impresora)
    try:
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(impresora)

        # Obtener dimensiones del área imprimible para medir el ancho de impresion
        dpi = hdc.GetDeviceCaps(88)  # LOGPIXELSX 	Píxeles por pulgada horizontal (DPI) 88 es el codigo
        width_px = hdc.GetDeviceCaps(110)  # HORZRES 	Ancho imprimible en píxeles 110 es el codigo
        height_px = hdc.GetDeviceCaps(111)  # VERTRES 	Alto imprimible en píxeles 111 es el codigo

        # Calcular tamaño de fuente ideal en función del ancho del papel
        chars_per_line = max(len(line) for line in texto.split("\n"))
        font_size = max(24, int(width_px / (chars_per_line + 2)))  # tamaño relativo al ancho disponible

        hdc.StartDoc("Tiquete Báscula")
        hdc.StartPage()

        fuente = win32ui.CreateFont({
            "name": "Consolas",
            "height": font_size,
            "weight": 700  # Negrita
        })
        hdc.SelectObject(fuente)

        y = 50
        line_spacing = int(font_size * 1.5)
        for linea in texto.split("\n"):
            hdc.TextOut(50, y, linea)
            y += line_spacing

        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
    finally:
        win32print.ClosePrinter(hprinter)


#defino funcion para mostrar tiquete con impresion para que salga el mensaje a imprimir
def mostrar_tiquete_con_impresion(titulo, contenido):
    ventana = tk.Toplevel()
    ventana.title(titulo)
    #ventana.geometry("410x500")
    centrar_ventana(ventana, 410, 500, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original
    ventana.resizable(False, False)
    ventana.attributes("-topmost", True)
    
    # Registrar la ventana activa en la lista global
    ventanas_tiquete_abiertas.append(ventana)

    
    
    # Cuerpo del tiquete
    # Área de texto con el contenido del tiquete
    text_area = tk.Text(ventana, wrap="word", font=("Consolas", 10))
    text_area.pack(expand=True, fill="both", padx=10, pady=10)
    text_area.insert("1.0", contenido)
    text_area.config(state="disabled")

    frame_botones = tk.Frame(ventana)
    frame_botones.pack(pady=10)

    def imprimir_default():
        imprimir_tiquete(contenido)

    def seleccionar_e_imprimir():
        sub = tk.Toplevel()
        sub.title("Seleccionar impresora")
        sub.geometry("400x150")
        sub.resizable(False, False)
        sub.attributes("-topmost", True)

        tk.Label(sub, text="Seleccione una impresora instalada:", font=("Arial", 11)).pack(pady=10)

        impresoras = win32print.EnumPrinters(2)
        nombres = [p[2] for p in impresoras]

        seleccion = tk.StringVar(value=nombres[0] if nombres else "")

        lista = tk.OptionMenu(sub, seleccion, *nombres)
        lista.config(width=40)
        lista.pack(pady=5)

        def imprimir_seleccionada():
            impresora = seleccion.get()
            if impresora:
                imprimir_tiquete(contenido, impresora)
            sub.destroy()

        tk.Button(sub, text="🖨 Imprimir", command=imprimir_seleccionada).pack(pady=10)
    
    def cerrar_ventana():
        if ventana in ventanas_tiquete_abiertas:
            ventanas_tiquete_abiertas.remove(ventana)
        if not ventanas_tiquete_abiertas:
            cerrar_proceso_impresion()  # ✅ se elimina .proceso_impresion_activo
        ventana.destroy()


    # Botones principales
    tk.Button(frame_botones, text="🖨 Imprimir (predeterminada)", command=imprimir_default).pack(side="left", padx=5)
    tk.Button(frame_botones, text="🖨 Seleccionar impresora...", command=seleccionar_e_imprimir).pack(side="left", padx=5)
    tk.Button(frame_botones, text="❌ Cerrar", command=cerrar_ventana).pack(side="left", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", cerrar_ventana)



#definio funcion para actualizar el estado del pesaje que se comparte con el modulo 1 y lo indico cada que agrego o elimino pesaje en pesajes_temporales
# 🔄 Guardar estado actual de pesajes en archivo JSON
# 🔁 Carga todos los pesajes abiertos desde el JSON y los lleva a pesajes_temporales
def actualizar_estado_pesajes():
    global pesajes_temporales
    pesajes_temporales = {}

    try:
        with open("estado_actual_pesajes.json", "r") as file:
            estado = json.load(file)
    except FileNotFoundError:
        return

    for clave, valor in estado.items():
        if isinstance(valor, list) and len(valor) == 5:
            # Externos - Tercero
            pesajes_temporales[clave] = tuple(valor)
        elif isinstance(valor, dict):
            if "peso_entrada" in valor and "fecha_hora_entrada" in valor:
                peso = valor["peso_entrada"]
                fecha = valor["fecha_hora_entrada"]
                pesajes_temporales[clave] = (peso, fecha)
                

# 🔁 Cargar estado anterior desde archivo JSON (al iniciar)
def cargar_estado_pesajes():
    ruta = os.path.join(os.path.dirname(__file__), 'estado_actual_pesajes.json')
    try:
        with open(ruta, 'r') as f:
            datos = json.load(f)
            pesajes_temporales.update(datos)
    except Exception as e:
        print(f"⚠️ No se pudo restaurar estado de pesajes: {e}")


# 🟢 Llamar esta función cargar_estado_pesajes inmediatamente después de definirla
cargar_estado_pesajes()

# Función que se conecta al socket o modulo1 para obtener el peso actual y la hora desde modulo1
def obtener_datos_peso():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5000))
            data = s.recv(1024)
            resultado = json.loads(data.decode())
            peso = resultado.get("peso", 0)
            if peso is None:
                peso = 0
            return peso, resultado.get("timestamp", "")
    except:
        return 0, ""
 

# variable global para captura de peso
peso_capturado_global = None

    
# Función para confirmar o permitir ingreso manual si el peso es bajo
def confirmar_o_pedir_peso(peso, ventana):
    if peso <= 10:
        decision = messagebox.askyesno(
            "Cierre con peso bajo",
            f"El peso actual es {peso:.2f} kg.\n¿Desea cerrar con este peso presione Si o ingresar un peso manual presione no?",
            parent=ventana
        )
        if not decision:
            # Permitir ingreso manual
            peso_manual = simpledialog.askstring("Peso cierre manual", "Ingrese el peso final (kg):", parent=ventana)
            if peso_manual and peso_manual.strip().isdigit():
                return int(peso_manual.strip())
            else:
                messagebox.showwarning("Cancelado", "No se ingresó peso válido. Operación cancelada.", parent=ventana)
                return None
    return peso
 # Si falla la conexión o algo sale mal, retorna 0 y cadena vacía
 
 
 
 # Funcion que Devuelve True si el archivo puntero existe
def proceso_impresion_activo():
    return os.path.exists(".proceso_impresion_activo")


# Función para cerrar el proceso activo de ingreso de datos
def cerrar_proceso_impresion():
    try:
        os.remove(".proceso_impresion_activo") # Elimina el archivo puntero cuando se cierra el proceso
    except FileNotFoundError:
        pass
    frame_subclientes.pack_forget()  # Oculta el submenú si está visible

# Funcion para centrar la ventana principal
def centrar_ventana(ventana, ancho, alto, margen_superior=50):
    ventana.update_idletasks()  # Asegura que se puedan obtener dimensiones actualizadas
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (pantalla_ancho - ancho) // 2
    y = margen_superior  # Espacio desde la parte superior
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# --------------------------------------------------------------------
# FORMULARIO EMBEBIDO PARA INGRESO DE DATOS - INMUNIZA, ASERRIO, ASTILLABLE
# Esta función genera un formulario visual directamente en la ventana
# principal, solicitando los datos obligatorios para servicios internos:
#   - Placa (validación formato LLL111)
#   - Empresa (RG o MS con botones)
#   - Número de remisión (solo dígitos)
# Al confirmar, se construye el ID y se llama a `continuar_flujo_pesaje_interno(...)`.
# También permite cancelar el ingreso, limpiando el formulario y cerrando el proceso activo.
# --------------------------------------------------------------------


# 🔁 Función que crea y muestra el formulario visual estándar para Inmuniza, Aserrio, Astillable

def mostrar_formulario_interno(tipo, ventana, frame_formulario, refrescar_tabla_pesajes, limpiar_formulario_unicamente):
    
    #ventana.geometry("722x668")  # 👈 abre la ventana principal servicio bascula al abrir el formulario
    centrar_ventana(ventana, 722, 668, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario
    
    # 🔁 Asegura que el frame esté visible incluso si fue ocultado con .pack_forget()
    frame_formulario.pack(pady=10, fill="x")
       
    # Limpiar formulario anterior
    for widget in frame_formulario.winfo_children():
        widget.destroy()

    # Título del formulario
    tk.Label(frame_formulario, text=f"Formulario para {tipo}", font=("Arial", 12, "bold")).pack(pady=(0, 10))

    # Frame de línea horizontal para los 3 campos con etiquetas arriba
    fila_formulario = tk.Frame(frame_formulario)
    fila_formulario.pack(fill="x", pady=5)
    
    # Placa del vehículo (formato ABC123)
    tk.Label(fila_formulario, text="Placa del vehículo (Ej: ABC123):", anchor="center").grid(row=0, column=0, padx=10)
    entry_placa = tk.Entry(fila_formulario, width=10, font=("Arial", 10))
    entry_placa.grid(row=1, column=0, padx=10)


    #  Empresa (RG o MS) 
    tk.Label(fila_formulario, text="Seleccione la empresa:", anchor="center").grid(row=0, column=1, padx=10)
    empresa = tk.StringVar(value="__nulo__")  # ← valor que no coincide con ninguna opción sin seleccion inicial osea inicializamos variable con valor invalido
    frame_empresa = tk.Frame(fila_formulario)
    frame_empresa.grid(row=1, column=1, padx=10)

    
    rb_rg = tk.Radiobutton(frame_empresa, text="RG", variable=empresa, value="RG")
    rb_ms = tk.Radiobutton(frame_empresa, text="MS", variable=empresa, value="MS")
    rb_rg.pack(side="left", padx=5)
    rb_ms.pack(side="left", padx=5)

 
    # Remisión solo numero
    tk.Label(fila_formulario, text="Número de remisión (solo números):", anchor="center").grid(row=0, column=2, padx=10)
    entry_remision = tk.Entry(fila_formulario, width=10, font=("Arial", 10))
    entry_remision.grid(row=1, column=2, padx=10)


    # 🔁 NUEVO BLOQUE - Manejo de navegación por ENTER entre campos con validación parcial

    # Al presionar Enter en placa → validar formato y mover al grupo RG/MS
    def validar_placa_y_mover(event=None):
        placa = entry_placa.get().strip().upper()
        if not re.fullmatch(r"[A-Z]{3}\d{3}", placa):
            messagebox.showerror(
                "Error, Formato de placa inválido",
                "La placa debe tener 3 letras seguidas de 3 números.\n"
                "Ejemplo válido: ABC123\n"
                "No se permiten símbolos, ni espacios.\n"
                "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n",
                parent=ventana
            )
            entry_placa.focus_set()
            return
        # Mover foco al primer botón de empresa
        for btn in frame_empresa.winfo_children():
            if isinstance(btn, tk.Radiobutton):
                btn.focus_set()
                break
    
    
    # Al presionar Enter en RG/MS → mover a remisión
    def mover_a_remision(event=None):
        if empresa.get() not in ["RG", "MS"]:
            messagebox.showerror("Empresa no seleccionada", "Debe seleccionar la empresa (RG o MS).", parent=ventana)
            # 🔁 Devolver el foco al botón RG
            for btn in frame_empresa.winfo_children():
                if isinstance(btn, tk.Radiobutton) and btn.cget("text") == "RG":
                    btn.focus_set()
                    break
            return
        entry_remision.focus_set()


    # Al presionar Enter en remisión → validar que no esté vacío y confirmar
    def validar_remision_y_confirmar(event=None):
        remision = entry_remision.get().strip()
        if not remision:
            messagebox.showerror("Campo obligatorio", "Debe ingresar el número de remisión.", parent=ventana)
            entry_remision.focus_set()
            return
        confirmar_datos()

    # Asociar las funciones anteriores a teclas Enter
    entry_placa.bind("<Return>", validar_placa_y_mover)
    rb_rg.bind("<Return>", mover_a_remision)
    rb_ms.bind("<Return>", mover_a_remision)
    entry_remision.bind("<Return>", validar_remision_y_confirmar)


    # 🔘 Función crea boton para confirmar los datos y continuar el flujo de pesaje
    def confirmar_datos():
        placa = entry_placa.get().strip().upper() # 🔁 Convierte a mayúsculas automáticamente con upper      
        remision = entry_remision.get().strip()
        empresa_sel = empresa.get()

        # Validación de placa
        if not re.fullmatch(r"[A-Z]{3}\d{3}", placa):
            messagebox.showerror(
                "Error, Formato de placa inválido",
                "La placa debe tener 3 letras seguidas de 3 números.\n"
                "Ejemplo válido: ABC123\n"
                "No se permiten símbolos, ni espacios.\n"
                "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n",
                parent=ventana
            )
            entry_placa.focus_set()
            return
        
        # Validación de empresa
        if empresa_sel not in ["RG", "MS"]:
            messagebox.showerror("Error", "Debe seleccionar la empresa (RG o MS).", parent=ventana)
            return

        # Validación de remisión
        if not remision.isdigit():
            messagebox.showerror("Error", "La remisión debe contener solo números.", parent=ventana)
            entry_remision.focus_set()
            return
        
        # Asignar nombre y NIT de la empresa
        if empresa_sel == "RG":
            nombre_empresa = "Reforestadora El Guásimo S.A.S"
            nit_empresa = "8909408520"
        else:
            nombre_empresa = "MS Timberland Holdings Limited"
            nit_empresa = "9004023313"

        #clave_placa_remision = f"{placa} {empresa_sel} {remision}"
        
        
        
        # 🔁 Construimos el ID y clave si todo esta bien
        id_ingresado = f"{placa} {empresa_sel}{remision}".strip().upper()
        clave = f"{tipo}:{id_ingresado}".strip()
        
        
        #adquiero de la variable global el peso antes capturado
        global peso_capturado_global
        print(f"[DEBUG] peso_capturado_global al confirmar formulario: {peso_capturado_global}")
        peso = peso_capturado_global



        # Continuar con el flujo de lógica normal como si fuera un ingreso valido
        # Llama a función unificada que maneja apertura o cierre manual
        continuar_flujo_pesaje_interno(
            tipo=tipo,
            clave=clave,
            id_ingresado=id_ingresado,
            peso=peso,
            ventana=ventana,
            refrescar_tabla_pesajes=refrescar_tabla_pesajes,
            limpiar_formulario_unicamente=limpiar_formulario_unicamente,
            #definimos los datos de la empresa que van a ir en mysql
            datos_empresa={
                "tipo": tipo,
                "codigo_empresa": empresa_sel,
                "nombre": nombre_empresa,
                "nit": nit_empresa,
                "id_ingresado": id_ingresado
            }
        )
        
     
     # 🔴 Función para boton cancelar del formulario

    def cancelar():
        limpiar_formulario_unicamente()
        cerrar_proceso_impresion()
        #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
        centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario


    # Botones de acción
    frame_botones = tk.Frame(frame_formulario)
    frame_botones.pack(pady=10)

    tk.Button(frame_botones, text="✅ Confirmar", font=("Arial", 10, "bold"), command=confirmar_datos).pack(side="left", padx=10)
    tk.Button(frame_botones, text="❌ Cancelar", font=("Arial", 10), command=cancelar).pack(side="left", padx=10)

# 🔄 Esta función guarda el pesaje en el archivo JSON (estado_pesajes.json).
# Si ya existe, muestra el tiquete directamente. Si no, crea uno nuevo,
# lo guarda, y muestra el tiquete. También limpia el formulario al finalizar.
def continuar_flujo_pesaje_interno(tipo, clave, id_ingresado, peso, ventana, refrescar_tabla_pesajes=None, limpiar_formulario_unicamente=None, datos_empresa=None):
  
    # Cargar archivo de estado
    archivo_estado = "estado_actual_pesajes.json"

    try:
        with open(archivo_estado, "r") as file:
            estado = json.load(file)
    except FileNotFoundError:
        estado = {}

    # Si ya existe un pesaje abierto (osea la clave ya existe), mostrar tiquete
      
    # 📌 Si el pesaje ya fue iniciado → es un cierre manual
    if clave in estado and tipo in ["Inmuniza", "Aserrio"]:
        def cerrar_con_peso(peso_final):
            fecha_inicial = estado[clave]["fecha_hora_entrada"]
            peso_inicial = estado[clave]["peso_entrada"]
            peso_neto = abs(peso_final - peso_inicial)
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 🔽 INICIO BLOQUE GUARDADO EN MYSQL
            peso_bruto = max(peso_inicial, peso_final)
            peso_tara = min(peso_inicial, peso_final)

            from integracion_mysql import guardar_cliente_y_pesaje
            guardar_cliente_y_pesaje(
                tipo_cliente="interno",
                datos_cliente=datos_empresa,
                datos_pesaje={
                    "peso_bruto": peso_bruto,
                    "peso_tara": peso_tara,
                    "peso_neto": peso_neto,
                    "placa": id_ingresado.split(" ")[0]# ← Asume que la placa es la primera parte del ID
                }
            )
            # 🔼 FIN BLOQUE GUARDADO EN MYSQL
            
            
            # Actualizar y eliminar el pesaje
            estado[clave]["peso_salida"] = peso_final
            estado[clave]["fecha_hora_salida"] = fecha_actual
            del estado[clave]# ✅ Elimina el pesaje cerrado
            
            with open(archivo_estado, "w") as file:
                json.dump(estado, file, indent=4)

            encabezado = f"{datos_empresa['nombre']}\nNIT: {datos_empresa['nit']}\n"
            contenido = (
                f"{encabezado}"
                f"Pesaje final registrado.\n"
                f"{tipo}:\n"
                f"ID: {id_ingresado}\n"
                f"Peso Inicial: {peso_inicial:.2f} kg — {fecha_inicial}\n"
                f"Peso Final: {peso_final:.2f} kg — {fecha_actual}\n"
                f"Peso Neto: {peso_neto:.2f} kg"
            )
            mostrar_tiquete_con_impresion("Resultado", contenido)
            
            #cerrar_proceso_impresion()
            actualizar_estado_pesajes() # ✅ actualiza JSON en memoria
            
            if refrescar_tabla_pesajes:
                refrescar_tabla_pesajes() # ✅ actualiza tabla en pantalla
                
            if limpiar_formulario_unicamente:
                limpiar_formulario_unicamente()

        # Preguntar si desea usar el peso actual o ingresar manual para cerrar
        # ✅ Aquí usamos confirmar_o_pedir_peso
        peso_confirmado = confirmar_o_pedir_peso(peso, ventana)
        if peso_confirmado is None:
            return

        cerrar_con_peso(peso_confirmado)
        return

    # 🟢 NUEVO REGISTRO de pesaje de entrada PARA INMUNIZA / ASERRIO
    if tipo in ["Inmuniza", "Aserrio"]:
        fecha_entrada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado[clave] = {
            "tipo": tipo,
            "id": id_ingresado,
            "peso_entrada": peso,
            "fecha_hora_entrada": fecha_entrada
        }

        with open(archivo_estado, "w") as file:
            json.dump(estado, file, indent=4)
            
        encabezado = f"{datos_empresa['nombre']}\nNIT: {datos_empresa['nit']}\n"
        contenido = (
            f"{encabezado}"
            f"Pesaje inicial registrado.\n"
            f"{tipo}:\n"
            f"ID: {id_ingresado}\n"
            f"Peso Inicial: {peso:.2f} kg — {fecha_entrada}"
        )
        mostrar_tiquete_con_impresion("Tiquete de Entrada", contenido)
        
        actualizar_estado_pesajes()
        if refrescar_tabla_pesajes:
            refrescar_tabla_pesajes()

    # 🟣 ASTILLABLE (solo imprime, no guarda)
    elif tipo == "Astillable":
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 🔽 INICIO BLOQUE GUARDADO EN MYSQL
        from integracion_mysql import guardar_cliente_y_pesaje
        guardar_cliente_y_pesaje(
            tipo_cliente="interno",
            
            datos_cliente=datos_empresa,
            datos_pesaje={
                "peso_bruto": peso,
                "peso_tara": 0,
                "placa": id_ingresado.split(" ")[0], # ← Asume que la placa es la primera parte del ID
                "peso_neto": peso # neto = bruto si no hay tara
            }
        )
        # 🔼 FIN BLOQUE GUARDADO EN MYSQL
        
        encabezado = f"{datos_empresa['nombre']}\nNIT: {datos_empresa['nit']}\n"
        contenido = (
            f"{encabezado}"
            f"Pesaje único registrado.\n"
            f"{tipo}:\n"
            f"ID: {id_ingresado}\n"
            f"Peso: {peso:.2f} kg — {fecha_actual}"
        )
        mostrar_tiquete_con_impresion("Tiquete de Pesaje", contenido)

    #cerrar_proceso_impresion()

    # ✅ Limpieza visual del formulario después de completar (usando función dedicada)
    if limpiar_formulario_unicamente:
        limpiar_formulario_unicamente()
        #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
        centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario



# --------------------------------------------------------------------
# FORMULARIO EMBEBIDO PARA CLIENTES EXTERNOS DE PAGO MENSUAL
# Esta función muestra un formulario para los clientes:
#   - Cipreses de Colombia
#   - Núcleos de Madera
#   - Construinmuniza
# Permite registrar un pesaje inicial o hacer el cierre (manual o automático).
# Se genera un tiquete al finalizar, y el estado se guarda o actualiza en el JSON.
# --------------------------------------------------------------------

# 🔁 Función que crea y muestra el formulario visual estándar para Externos (Cipreses de Colombia, Núcleos de Madera, Construinmuniza )
def mostrar_formulario_externo_pago_mensual(cliente_nombre, tipo, ventana, frame_formulario, refrescar_tabla_pesajes=None, limpiar_formulario_unicamente=None):
    
    #ventana.geometry("722x668")  # 👈 abre la ventana principal servicio bascula al abrir el formulario
    centrar_ventana(ventana, 722, 668, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario
    
    # 🔁 Asegura que el frame esté visible incluso si fue ocultado
    frame_formulario.pack(pady=10, fill="x")
    
    # 🔁 Limpia el contenido anterior, Limpiar formulario anterior
    for widget in frame_formulario.winfo_children():
        widget.destroy()
    
    
    # ASIGNACIÓN DE NOMBRE Y NIT
    # Se determina qué empresa mensual fue seleccionada (cliente_nombre)
    # y se asigna el NIT correspondiente.
    
    if cliente_nombre == "Cipreses de Colombia":
        nombre = cliente_nombre
        nit = "890903541"
    elif cliente_nombre == "Núcleos de Madera":
        # _norm() quita acentos, así que "núcleos" y "nucleos" dan igual
        nombre = cliente_nombre
        nit = "811016049"
    elif cliente_nombre == "Construinmuniza":
        nombre = cliente_nombre
        nit = "900297110"
  
    
    # Título del formulario
    tk.Label(frame_formulario, text=f"{cliente_nombre} — Formulario de Pesaje", font=("Arial", 12, "bold")).pack(pady=(0, 10))

    # Frame de línea horizontal para los campos con etiquetas arriba
    fila_formulario = tk.Frame(frame_formulario)
    fila_formulario.pack(fill="x", pady=5)

    # Placa
    tk.Label(fila_formulario, text="Placa del vehículo (Ej: ABC123):", anchor="center").grid(row=0, column=0, padx=10)
    entry_placa = tk.Entry(fila_formulario, width=10, font=("Arial", 10))
    entry_placa.grid(row=1, column=0, padx=10)

    # Remisión (opcional)
    tk.Label(fila_formulario, text="Remisión:").grid(row=0, column=1, padx=10)
    entry_remision = tk.Entry(fila_formulario, width=12, font=("Arial", 10))
    entry_remision.grid(row=1, column=1, padx=10)
    
    # 🔁 Mover foco de placa → remisión al presionar Enter
    #entry_placa.bind("<Return>", lambda event: entry_remision.focus_set())
    def validar_placa_y_mover_a_remision(event=None):
        placa = entry_placa.get().strip().upper()
        if not re.fullmatch(r"[A-Z]{3}\d{3}", placa):
            messagebox.showerror(
                "Error, Formato de placa inválido",
                "La placa debe tener 3 letras seguidas de 3 números.\n"
                "Ejemplo válido: ABC123\n"
                "No se permiten símbolos, ni espacios.\n"
                "No se permiten letras en la parte numérica ni números en la parte de letras.\n",
                parent=ventana
            )
            entry_placa.focus_set()
            return
        entry_remision.focus_set()

    entry_placa.bind("<Return>", validar_placa_y_mover_a_remision)

    

    # 🧩 Manejo de Enter en remisión con validación si está vacía
    #al presiona enter en remision llama a validar la remision y confirmar
    entry_remision.bind("<Return>", lambda event: confirmar_datos())


    
    # 🔘 Función crea boton para confirmar los datos y continuar el flujo de pesaje
    def confirmar_datos():        
        placa = entry_placa.get().strip().upper()# 🔁 Convierte a mayúsculas automáticamente con upper 
        remision = entry_remision.get().strip().upper()# 🔁 Convierte a mayúsculas automáticamente con upper 
        
        
        # 🧪 Validación de placa
        if not re.fullmatch(r"[A-Z]{3}\d{3}", placa):
            messagebox.showerror(
                "Error, Formato de placa inválido\n",
                "La placa debe tener 3 letras seguidas de 3 números.\n"
                "Ejemplo válido: ABC123\n"
                "No se permiten símbolos, ni espacios.\n"
                "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n",
                parent=ventana
            )
            entry_placa.focus_set()
            return
        entry_remision.focus_set()#######AQUI VOY EN EL PROGRAMA MODIFICANDO FOCO DE CURSOR SEGUN ENTER O BOTON CONTINUAR
        # 🧪 Validación de remisión 1 (si se ingresó)
        # Validación de remisión (si se ingresó, debe tener letras/números/espacios)
        if remision and not re.fullmatch(r"[A-Z0-9 ]+", remision):
            messagebox.showerror("Error", "La remisión solo puede contener letras, números y espacios.", parent=ventana)
            return
        #validacion de remision2
        # ✅ Si NO hay remisión, preguntar si desea continuar sin ella
        if not remision:
            continuar = messagebox.askyesno("¿Sin remisión?", "No se ingresó remisión.\n¿Desea continuar sin ella?", parent=ventana)
            if not continuar:
                entry_remision.focus_set()  # ← Regresa el foco al campo remisión
                return
        
        
        # 🔁 Construimos el ID y clave si todo esta bien
        id_ingresado = f"{placa} {remision}".strip()# ← Si no hay remisión, queda solo la placa
        clave = f"{tipo}:{cliente_nombre}:{id_ingresado}".strip()
        
        #adquiero de la variable global el peso antes capturado
        global peso_capturado_global
        print(f"[DEBUG] peso_capturado_global al confirmar formulario: {peso_capturado_global}")
        peso = peso_capturado_global
        print(f"[DEBUG] peso_capturado_global al confirmar formulario igualando peso: {peso_capturado_global}")


        # Continuar con el flujo de lógica normal como si fuera un ingreso valido
        # Llama a función unificada que maneja apertura o cierre manual
        continuar_flujo_pesaje_externo( 
                       
            tipo=tipo,
            clave=clave,
            id_ingresado=id_ingresado,
            peso=peso,
            ventana=ventana,
            refrescar_tabla_pesajes=refrescar_tabla_pesajes,
            limpiar_formulario_unicamente=limpiar_formulario_unicamente,
            #definimos los datos de la empresa que van a ir en mysql
            datos_empresa={
                "tipo": tipo,
                "nombre": nombre,
                "nit": nit,
                "id_ingresado": id_ingresado
            }
            )
   
            
            
    # 🔴 Función para boton cancelar del formulario
    def cancelar():
        frame_formulario.pack_forget()
        cerrar_proceso_impresion()
        #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
        centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario

    # Botones de acción
    frame_botones = tk.Frame(frame_formulario)
    frame_botones.pack(pady=10)

    tk.Button(frame_botones, text="✅ Confirmar", font=("Arial", 10, "bold"), command=confirmar_datos).pack(side="left", padx=10)
    tk.Button(frame_botones, text="❌ Cancelar", font=("Arial", 10), command=cancelar).pack(side="left", padx=10)
    #entry_remision.bind("<Return>", lambda event: confirmar_datos())
  
  
# 🔄 Esta función guarda el pesaje en el archivo JSON (estado_pesajes.json).
# Si ya existe, muestra el tiquete directamente. Si no, crea uno nuevo,
# lo guarda, y muestra el tiquete. También limpia el formulario al finalizar.   
def continuar_flujo_pesaje_externo(tipo, clave, id_ingresado, peso, ventana, refrescar_tabla_pesajes=None, limpiar_formulario_unicamente=None, datos_empresa=None):
    archivo_estado = "estado_actual_pesajes.json"

    try:
        with open(archivo_estado, "r") as file:
            estado = json.load(file)
    except FileNotFoundError:
        estado = {}

    # 📌 Si ya existe el pesaje → CIERRE
    if clave in estado:
        peso_inicial = estado[clave]["peso_entrada"]
        fecha_inicial = estado[clave]["fecha_hora_entrada"]

        # ✅ Solución a NoneType error
        if peso is None:
            peso = 0  # O lanza advertencia si lo prefieres
            
        # Preguntar si desea cerrar con este peso o ingresar uno manual
        peso_confirmado = confirmar_o_pedir_peso(peso, ventana)
        if peso_confirmado is None:
            return  # Usuario canceló



        peso_final = peso_confirmado
        peso_neto = abs(peso_final - peso_inicial)
        fecha_final = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        

        # 🔽 INICIO BLOQUE DE INTEGRACIÓN MYSQL (pesajes con cierre)
        peso_bruto = max(peso_inicial, peso_final)
        peso_tara = min(peso_inicial, peso_final)

        from integracion_mysql import guardar_cliente_y_pesaje
        guardar_cliente_y_pesaje(
            tipo_cliente="mensual",
            datos_cliente=datos_empresa,
            datos_pesaje={
                "peso_bruto": peso_bruto,
                "peso_tara": peso_tara,
                "peso_neto": peso_neto,
                "placa": id_ingresado.split(" ")[0], # ← Asume que la placa es la primera parte del ID
            }
        )
        # 🔼 FIN BLOQUE DE INTEGRACIÓN MYSQL
               

        del estado[clave]  # 🔁 Elimina el registro cerrado del json

        with open(archivo_estado, "w") as file:
            json.dump(estado, file, indent=4)

        actualizar_estado_pesajes()
        encabezado = f"{datos_empresa['nombre']}\nNIT: {datos_empresa['nit']}\n"
        contenido = (
            f"{encabezado}"
            f"Pesaje cerrado:\n"
            f"{tipo}:\n"
            f"ID: {id_ingresado}\n"
            f"Peso Inicial: {peso_inicial:.2f} kg — {fecha_inicial}\n"
            f"Peso Final: {peso_final:.2f} kg — {fecha_final}\n"
            f"Peso Neto: {peso_neto:.2f} kg"
        )
        mostrar_tiquete_con_impresion("Resultado", contenido)

        if refrescar_tabla_pesajes:
            refrescar_tabla_pesajes()
        if limpiar_formulario_unicamente:
            limpiar_formulario_unicamente()
        return


    # 🔍 Si no existe el pesaje, preguntar si es solo uno (sin cierre) o si tendrá cierre posterior
    cerrar = messagebox.askyesno("¿Tendrá cierre?", "¿Este servicio tendrá cierre de pesaje?", parent=ventana)

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if cerrar:
        # PESAJE INICIAL (con cierre posterior)
        estado[clave] = {
            "tipo": tipo,
            "id": id_ingresado,
            "peso_entrada": peso,
            "fecha_hora_entrada": fecha_actual
        }

        with open(archivo_estado, "w") as file:
            json.dump(estado, file, indent=4)

        actualizar_estado_pesajes()
        encabezado = f"{datos_empresa['nombre']}\nNIT: {datos_empresa['nit']}\n"
        contenido = (
            f"{encabezado}"
            f"Pesaje inicial registrado:\n"
            f"{tipo}:\n"
            f"ID: {id_ingresado}\n"
            f"Peso Inicial: {peso:.2f} kg — {fecha_actual}"
        )
                
        mostrar_tiquete_con_impresion("Tiquete de Entrada", contenido)

    else:
        # PESAJE ÚNICO (sin cierre posterior)
        encabezado = f"{datos_empresa['nombre']}\nNIT: {datos_empresa['nit']}\n"
        contenido = (
            f"{encabezado}"
            f"Pesaje registrado sin cierre:\n"
            f"{tipo}:\n"
            f"ID: {id_ingresado}\n"
            f"Peso: {peso:.2f} kg — {fecha_actual}"
        )
                
        # 🔽 INICIO BLOQUE DE INTEGRACIÓN MYSQL (solo pesajes sin cierre)
        from integracion_mysql import guardar_cliente_y_pesaje
        guardar_cliente_y_pesaje(
            tipo_cliente="mensual",
            datos_cliente=datos_empresa,
            datos_pesaje={
                "peso_bruto": peso,
                "peso_tara": None,
                "peso_neto": peso, # si no hay tara, peso_neto = peso_bruto
                "placa": id_ingresado.split(" ")[0], # ← Asume que la placa es la primera parte del ID
            }
        )
        # 🔼 FIN BLOQUE DE INTEGRACIÓN MYSQL    
        
        mostrar_tiquete_con_impresion("Pesaje único", contenido)

    if refrescar_tabla_pesajes:
        refrescar_tabla_pesajes()
    if limpiar_formulario_unicamente:
        limpiar_formulario_unicamente()
        #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
        centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario
        
        
# --------------------------------------------------------------------
# FORMULARIO EMBEBIDO PARA CLIENTES EXTERNOS DE PAGO INMEDIATO
# Esta función muestra un formulario para el cliente:
#   - Tercero (pago inmediato)
# Permite registrar:
#   - Placa del vehículo (obligatoria)
#   - Remisión (opcional)
#   - Razón social (obligatoria)
#   - NIT o cédula (obligatorio)
#   - Correo electrónico (opcional y validado)
# El sistema pregunta si el servicio tendrá cierre:
#   - Si SÍ, registra un pesaje inicial en el JSON (estado_actual_pesajes.json)
#   - Si NO, permite ingresar peso manual o usar el peso actual como cierre
# Si el ID ya existe, cierra automáticamente el pesaje con confirmación.
# Se genera un tiquete al finalizar (entrada o cierre), y se actualiza el estado.
# --------------------------------------------------------------------

def mostrar_formulario_externo_tercero(cliente_nombre, tipo, ventana, frame_formulario, refrescar_tabla_pesajes=None, limpiar_formulario_unicamente=None):
    
    #ventana.geometry("852x668")  # 👈 abre la ventana principal servicio bascula al abrir el formulario
    centrar_ventana(ventana, 852, 668, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario
    # Asegura visibilidad del frame, Mostrar y limpiar el formulario
    frame_formulario.pack(pady=10, fill="x")
    for widget in frame_formulario.winfo_children():
        widget.destroy()

    # Título
    tk.Label(frame_formulario, text="Tercero — Pago Inmediato", font=("Arial", 12, "bold")).pack(pady=(0, 10))
    fila_formulario = tk.Frame(frame_formulario)
    fila_formulario.pack(fill="x", pady=5)

    # Entradas en campos del formulario
    tk.Label(fila_formulario, text="Placa del vehículo (Ej: ABC123):").grid(row=0, column=0, padx=10)
    entry_placa = tk.Entry(fila_formulario, width=10, font=("Arial", 10))
    entry_placa.grid(row=1, column=0, padx=10)

    tk.Label(fila_formulario, text="Remisión (opcional):").grid(row=0, column=1, padx=10)
    entry_remision = tk.Entry(fila_formulario, width=15, font=("Arial", 10))
    entry_remision.grid(row=1, column=1, padx=10)

    tk.Label(fila_formulario, text="Nombre o Razón social:").grid(row=0, column=2, padx=10)
    entry_nombre = tk.Entry(fila_formulario, width=25, font=("Arial", 10))
    entry_nombre.grid(row=1, column=2, padx=10)

    tk.Label(fila_formulario, text="NIT o Cédula:").grid(row=0, column=3, padx=10)
    entry_nit = tk.Entry(fila_formulario, width=15, font=("Arial", 10))
    entry_nit.grid(row=1, column=3, padx=10)

    tk.Label(fila_formulario, text="Correo electrónico (opcional):").grid(row=0, column=4, padx=10)
    entry_correo = tk.Entry(fila_formulario, width=25, font=("Arial", 10))
    entry_correo.grid(row=1, column=4, padx=10)


    # 🔁 Navegación automática con validaciones parciales al presionar Enter
    def validar_placa_y_mover(event=None):
        placa = entry_placa.get().strip().upper()
        if not re.fullmatch(r"[A-Z]{3}\d{3}", placa):
            messagebox.showerror(
                "Error, Formato de placa inválido\n",
                "La placa debe tener 3 letras seguidas de 3 números.\n"
                "Ejemplo válido: ABC123\n"
                "No se permiten símbolos, ni espacios.\n"
                "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n",
                parent=ventana
                )
            entry_placa.focus_set()
            return
        entry_remision.focus_set()

    def validar_nombre_y_mover(event=None):
        razon = entry_nombre.get().strip()
        if not razon:
            messagebox.showerror("Campo obligatorio", "Debe ingresar el nombre o razón social.", parent=ventana)
            entry_nombre.focus_set()
            return
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9 .,'&-]+", razon):
            messagebox.showerror("Error", "Nombre o razón social contiene caracteres inválidos.", parent=ventana)
            entry_nombre.focus_set()
            return
        entry_nit.focus_set()

    def validar_nit_y_mover(event=None):
        nit = entry_nit.get().strip()
        if not nit.isdigit():
            messagebox.showerror("Error", "El NIT o cédula debe contener solo números.", parent=ventana)
            entry_nit.focus_set()
            return
        entry_correo.focus_set()

    entry_placa.bind("<Return>", validar_placa_y_mover)
    entry_remision.bind("<Return>", lambda e: entry_nombre.focus_set())
    entry_nombre.bind("<Return>", validar_nombre_y_mover)
    entry_nit.bind("<Return>", validar_nit_y_mover)
    entry_correo.bind("<Return>", lambda e: confirmar_datos())


    # Función que se ejecuta al confirmar
    def confirmar_datos():
        placa = entry_placa.get().strip().upper()
        remision = entry_remision.get().strip().upper()
        razon = entry_nombre.get().strip()
        nit = entry_nit.get().strip()
        correo = entry_correo.get().strip()

        # Validaciones
        if not re.fullmatch(r"[A-Z]{3}\d{3}", placa):
            messagebox.showerror(
                "Error, Formato de placa inválido\n",
                "La placa debe tener 3 letras seguidas de 3 números.\n"
                "Ejemplo válido: ABC123\n"
                "No se permiten símbolos, ni espacios.\n"
                "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n",
                parent=ventana
                )
            entry_placa.focus_set()
            return

        if remision and not re.fullmatch(r"[A-Z0-9 ]+", remision):
            messagebox.showerror("Error", "Remisión solo puede contener letras, números y espacios.", parent=ventana)
            entry_remision.focus_set()
            return

        if not razon:
            messagebox.showerror("Error", "Debe ingresar razón social o nombre.", parent=ventana)
            entry_nombre.focus_set()
            return


        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9 .,'&-]+", razon):
            messagebox.showerror("Error", "Razón social contiene caracteres inválidos.", parent=ventana)
            entry_nombre.focus_set()
            return

        # Capitalizar razon si no está en mayúsculas
        if not razon.isupper():
            razon = ' '.join(p.capitalize() for p in razon.split())

        if not nit.isdigit():
            messagebox.showerror("Error", "NIT o cédula solo debe contener números.", parent=ventana)
            entry_nit.focus_set()
            return

        if correo and not re.fullmatch(r"[\w\.-]+@[\w\.-]+\.\w+", correo):
            messagebox.showwarning("Correo inválido", "Formato incorrecto de correo.", parent=ventana)
            entry_correo.focus_set()
            return

        id_ingresado = f"{placa} {remision}".strip()
        # 🔑 Clave completa usada para identificar pesajes únicos
        # Incluye: tipo, cliente, placa, remisión (opcional), razón social y NIT
        # Esto garantiza que no se confundan pesajes con la misma placa pero diferente empresa o persona
        clave = f"{tipo}:{cliente_nombre}:{id_ingresado}:{razon}:{nit}".strip()
       

        global peso_capturado_global
        peso = peso_capturado_global
        print(f"[DEBUG] peso_capturado_global al confirmar formulario TERCERO: {peso}")

        # 🟡 Si ya hay pesaje iniciado → hacer cierre automático sin preguntar por inicio
        try:
            with open("estado_actual_pesajes.json", "r") as file:
                estado = json.load(file)
        except FileNotFoundError:
            estado = {}
            
        # 🔍 Buscar si ya existe un pesaje con misma placa, remisión, razon y nit
        clave_existente = None
        for k, v in estado.items():
            if k.startswith(f"{tipo}:{cliente_nombre}:{id_ingresado}") and v.get("razon") == razon and v.get("nit") == nit:
                clave_existente = k
                break
                
        # ------------------------------------------
        # 🔁 CIERRE AUTOMÁTICO SI YA EXISTE PESAJE
        # ------------------------------------------                
        if clave_existente:
            peso_ini = estado[clave_existente]["peso_entrada"]
            fecha_ini = estado[clave_existente]["fecha_hora_entrada"]
            razon = estado[clave_existente].get("razon", razon)
            nit = estado[clave_existente].get("nit", nit)
            correo = estado[clave_existente].get("correo", correo)

            peso_confirmado = confirmar_o_pedir_peso(peso, ventana)
            if peso_confirmado is None:
                return

            peso_final = peso_confirmado
            peso_neto = abs(peso_final - peso_ini)
            fecha_final = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


            # 🔽 INICIO BLOQUE DE INTEGRACIÓN MYSQL (CIERRE AUTOMÁTICO)
            from integracion_mysql import guardar_cliente_y_pesaje
            peso_bruto = max(peso_ini, peso_final)
            peso_tara = min(peso_ini, peso_final)
            guardar_cliente_y_pesaje(
                tipo_cliente="tercero",
                datos_cliente={
                    "nombre": razon,
                    "cedula_nit": nit,
                    "correo_remision": correo,
                    "id_ingresado": id_ingresado
                },
                datos_pesaje={
                    "peso_bruto": peso_bruto,
                    "peso_tara": peso_tara,
                    "peso_neto": peso_neto,
                    "placa": placa
                }
            )
            # 🔼 FIN BLOQUE DE INTEGRACIÓN MYSQL


            del estado[clave_existente]
            with open("estado_actual_pesajes.json", "w") as file:
                json.dump(estado, file, indent=4)



            actualizar_estado_pesajes()
            contenido = (
                f"Cliente: {razon}\n"
                f"NIT: {nit}\n"
                f"Correo: {correo}\n"
                f"ID: {id_ingresado}\n"
                f"Peso Inicial: {peso_ini:.2f} kg — {fecha_ini}\n"
                f"Peso Final: {peso_final:.2f} kg — {fecha_final}\n"
                f"Peso Neto: {peso_neto:.2f} kg"
            )
            mostrar_tiquete_con_impresion("Pesaje cerrado", contenido)
            if refrescar_tabla_pesajes:
                refrescar_tabla_pesajes()
            if limpiar_formulario_unicamente:
                limpiar_formulario_unicamente()
            return

        # 🔘nuevo pesaje,  Si no existe, preguntamos si tendrá cierre
        cerrar = messagebox.askyesno("¿Tendrá cierre?", "¿Este servicio tendrá cierre de pesaje?", parent=ventana)

        if cerrar:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            estado[clave] = {
                "tipo": tipo,
                "id": id_ingresado,
                "peso_entrada": peso,
                "fecha_hora_entrada": fecha_actual,
                "razon": razon,
                "nit": nit,
                "correo": correo
            }

            with open("estado_actual_pesajes.json", "w") as file:
                json.dump(estado, file, indent=4)

            actualizar_estado_pesajes()
            contenido = (
                f"Cliente: {razon}\n"
                f"NIT: {nit}\n"
                f"Correo: {correo}\n"
                f"ID: {id_ingresado}\n"
                f"Peso inicial registrado: {peso:.2f} kg\n"
                f"Fecha: {fecha_actual}"
            )
            mostrar_tiquete_con_impresion("Pesaje inicial", contenido)
        else:
            # 🟢 Nuevo comportamiento: imprimir directamente el peso actual como único pesaje
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            contenido = (
                f"Cliente: {razon}\n"
                f"NIT: {nit}\n"
                f"Correo: {correo}\n"
                f"ID: {id_ingresado}\n"
                f"Peso registrado: {peso:.2f} kg\n"
                f"Fecha: {fecha_actual}"
            )
            
            # 🔽 INICIO BLOQUE DE INTEGRACIÓN MYSQL
            from integracion_mysql import guardar_cliente_y_pesaje
            guardar_cliente_y_pesaje(
                tipo_cliente="tercero",
                datos_cliente={
                    "nombre": razon,
                    "cedula_nit": nit,
                    "correo_remision": correo,
                    "id_ingresado": id_ingresado
                },
                datos_pesaje={
                    "peso_bruto": peso,
                    "peso_tara": None,
                    "peso_neto": peso,
                    "placa": placa
                }
            )
            # 🔼 FIN BLOQUE DE INTEGRACIÓN MYSQL
            
            mostrar_tiquete_con_impresion("Pesaje único (sin cierre)", contenido)

        if refrescar_tabla_pesajes:
            refrescar_tabla_pesajes()
        if limpiar_formulario_unicamente:
            limpiar_formulario_unicamente()
            #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
            centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario

    # Botones
    frame_botones = tk.Frame(frame_formulario)
    frame_botones.pack(pady=10)
    tk.Button(frame_botones, text="✅ Confirmar", font=("Arial", 10, "bold"), command=confirmar_datos).pack(side="left", padx=10)
    tk.Button(frame_botones, text="❌ Cancelar", font=("Arial", 10), command=lambda: (frame_formulario.pack_forget(), cerrar_proceso_impresion(),
                                                                                     #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
                                                                                     centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original
                                                                                     )).pack(side="left", padx=10)


# --------------------------------------------------------------------
# VENTANA PRINCIPAL DEL MÓDULO 3 – SERVICIO DE BÁSCULA
# Esta función construye y lanza la interfaz principal del sistema de pesajes.
# Aquí se gestionan:
#   - La captura del peso en tiempo real desde el socket
#   - La activación de los formularios embebidos por tipo de servicio
#   - El control de los botones principales (Externo, Aserrio, Inmuniza, Astillable)
#   - La visualización y refresco de pesajes abiertos en una tabla
#   - La impresión de tiquetes y control de estados
# También se asegura que solo se pueda realizar un proceso de pesaje activo a la vez.
# --------------------------------------------------------------------
# Función principal que construye y ejecuta la ventana de servicio del módulo 3, crea la interfaz del módulo
def modulo_servicio():
    
    # 🔁 Si el archivo puntero quedó por error de una sesión anterior, lo eliminamos
    if os.path.exists(".proceso_impresion_activo"):
        os.remove(".proceso_impresion_activo")
    
    
    # Función que se ejecuta al hacer clic en uno de los botones de servicio
    def verificar_servicio(tipo, cliente_seleccionado=None):
        frame_subclientes.pack_forget()  # 🔁 Siempre cerrar sub-botones al iniciar el flujo
        
        # ✅ Siempre capturamos el peso actual al presionar un botón principal en variable global
        global peso_capturado_global
        print(f"[DEBUG] peso_capturado_global al presionar botones principales: {peso_capturado_global}")
        peso_capturado_global, _ = obtener_datos_peso()
        print(f"[DEBUG] peso_capturado_global al obtener datos de peso {peso_capturado_global}")
        if peso_capturado_global is None:
            peso_capturado_global = 0
            print(f"[DEBUG] peso_capturado_global al obtener datos de peso si es none{peso_capturado_global}")
 
 
 
        # Si el tipo de servicio es externo con subtipos
        if tipo == "Externo":
            # Submenú para distinguir tipo de externo
            subtipos = {
                "Tercero (pago inmediato)": "Pago inmediato",
                "Cipreses de Colombia": "Pago mensual",
                "Núcleos de Madera": "Pago mensual",
                "Construinmuniza": "Pago mensual"
            }

            cliente = tk.StringVar(value="")

                
            # Asigna el cliente seleccionado u obteniendo desde el botón del submenu
            if cliente_seleccionado:
                cliente.set(cliente_seleccionado)
            else:
                return  # Seguridad: Si no se pasa cliente externo, se cancela el proceso y salimos
            
            tipo_pago = subtipos[cliente.get()]  # Obtiene tipo de pago según cliente
            # comportamiento para Tercero (pago inmediato)

        # Si es Inmuniza o Aserrio, se necesita un ID y se hace lógica de pesaje doble
        elif tipo in ["Inmuniza", "Aserrio", "Astillable"]:
            mostrar_formulario_interno(tipo, ventana, frame_formulario, refrescar_tabla_pesajes, limpiar_formulario_unicamente)
            return

        
    # Función que actualiza constantemente el peso en la GUI
    def actualizar_peso_gui():
        peso, hora = obtener_datos_peso()  # Obtiene los datos actuales
        peso_label.config(text=f"{peso:.2f} kg")  # Actualiza la etiqueta del peso
        hora_label.config(text=hora)  # Actualiza la hora debajo
        ventana.after(500, actualizar_peso_gui)  # Repite cada 500 ms (0.5 s)

    # Creación de la ventana principal
    ventana = tk.Tk()
    centrar_ventana(ventana, 722, 529, margen_superior=50)  # Ventana original centrada


    # Función que se ejecuta al cerrar la ventana principal
    def al_cerrar():
        if ventanas_tiquete_abiertas:
            messagebox.showinfo("Impresión activa", "Cierra primero todas las ventanas de impresión antes de salir.", parent=ventana)
            return
        print("📌 Sesión de pesajes confirmados:")
        for tipo, id_, p_ini, p_fin, f_ini, f_fin in pesajes_confirmados:
            print(f"→ Tipo: {tipo}, ID: {id_}, Peso Neto: {p_fin - p_ini:.2f} kg, De: {f_ini} a {f_fin}")
        ventana.destroy() # Cierra la ventana completamente
 

    ventana.protocol("WM_DELETE_WINDOW", al_cerrar)  # Asocia el cierre de ventana al manejo manual
    ventana.title("Servicio de Báscula")  # Título de la ventana
    centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Centra la ventana principal al abrirla
    ventana.attributes("-topmost", True)  # Hace que la ventana permanezca siempre por encima de otras

    # Sección que muestra el peso actual
    marco_peso = tk.Frame(ventana, bg="white", relief="sunken", bd=2)  # Marco con borde
    marco_peso.pack(pady=10, fill="x")  # Se posiciona con márgenes y ocupa el ancho

    tk.Label(marco_peso, text="Peso actual (kg):", font=("Arial", 12)).pack()
    peso_label = tk.Label(marco_peso, text="---", font=("Arial", 24, "bold"), fg="blue")
    peso_label.pack()
    hora_label = tk.Label(marco_peso, text="", font=("Arial", 10), fg="gray")
    hora_label.pack(pady=(2, 5))

    actualizar_peso_gui()  # Inicia la actualización en bucle del peso

    # Sección con los botones para elegir el tipo de servicio
    tk.Label(ventana, text="Seleccione el tipo de servicio:", font=("Arial", 12)).pack(pady=10)
    
    # Contenedor superior para agrupar botones principales y subclientes
    frame_superior = tk.Frame(ventana)
    frame_superior.pack(pady=5)

    frame_botones = tk.Frame(frame_superior)
    frame_botones.pack()

    # 🔻 Frame donde aparecerán sub-botones de clientes externos
    global frame_subclientes # declaro la variable como global para que sea visible fuera del metodo 
    frame_subclientes = tk.Frame(frame_superior)
    
    frame_subclientes.pack()
    frame_subclientes.pack_forget()  # Oculta botones por defecto

    
    # 🔳 Frame donde se insertarán formularios dinámicos (placa, remisión, RG/MS, etc.)
    frame_formulario = tk.Frame(ventana)
    frame_formulario.pack(pady=10, fill="x")
    
    # ✅ Función para limpiar únicamente el formulario embebido (sin afectar botones principales)
    def limpiar_formulario_unicamente():
        if frame_formulario:
            for widget in frame_formulario.winfo_children():
                widget.destroy()
            frame_formulario.pack_forget()


    # 🧾 Tabla para mostrar pesajes abiertos (clave, peso inicial, fecha)
    tk.Label(ventana, text="Pesajes Abiertos:", font=("Arial", 12)).pack(pady=(10, 0))

    tree = ttk.Treeview(ventana, columns=("clave", "peso", "fecha"), show="headings", height=8)
    tree.heading("clave", text="Clave")
    tree.heading("peso", text="Peso Inicial")
    tree.heading("fecha", text="Fecha")
    tree.column("clave", width=300)
    tree.column("peso", anchor="center")
    tree.column("fecha", anchor="center")
    tree.pack(expand=True, fill="both", padx=10, pady=5)

    # 🔁 Función para cargar y refrescar la tabla desde el JSON en tiempo real
    def refrescar_tabla_pesajes():
        selected = tree.selection()
        selected_claves = [tree.item(item, "values")[0] for item in selected]

        tree.delete(*tree.get_children())  # Limpia tabla

        for clave, valor in pesajes_temporales.items():
            if isinstance(valor, (list, tuple)) and len(valor) >= 2:
                peso_ini = valor[0]
                fecha = valor[1]
            elif isinstance(valor, dict) and "peso_entrada" in valor and "fecha_hora_entrada" in valor:
                peso_ini = valor["peso_entrada"]
                fecha = valor["fecha_hora_entrada"]
            else:
                continue  # Skip si no cumple formato

            tree.insert("", "end", values=(clave, f"{peso_ini:.2f}", fecha))

        # Restaurar la selección si todavía existe esa clave
        for item in tree.get_children():
            clave = tree.item(item, "values")[0]
            if clave in selected_claves:
                tree.selection_add(item)
                break  # Solo seleccionamos uno


    
    # Ejecutar refresco periódico cada 500ms
    def refresco_automatico_tabla():
        refrescar_tabla_pesajes()
        ventana.after(500, refresco_automatico_tabla)            
    
    #ventana.after(500, refrescar_tabla_pesajes)  # Se refresca automáticamente
    refresco_automatico_tabla()
    
    # 🔘 Botones debajo de la tabla
    frame_botones_tabla = tk.Frame(ventana)
    frame_botones_tabla.pack(pady=(0, 10))

    # Botón imprimir
    def imprimir_seleccionado():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin selección", "Seleccione un pesaje para imprimir.")
            return
        clave = tree.item(selected_items[0], "values")[0]

        if clave in pesajes_temporales:
            datos = pesajes_temporales[clave]
            if len(datos) == 5:  # Externos - Tercero
                peso, fecha, razon, nit, correo = datos
                contenido = (
                    f"Cliente: {razon}\n"
                    f"NIT: {nit}\n"
                    f"Correo: {correo}\n"
                    f"ID: {clave}\n"
                    f"Peso inicial registrado: {peso:.2f} kg\n"
                    f"Fecha: {fecha}"
                )
            elif len(datos) == 2:  # Otros
                peso, fecha = datos
                contenido = (
                    f"ID: {clave}\n"
                    f"Peso inicial registrado: {peso:.2f} kg\n"
                    f"Fecha: {fecha}"
                )
            else:
                contenido = f"Registro: {clave}"
            mostrar_tiquete_con_impresion("Resumen pesaje", contenido)

    # Botón editar
    def editar_datos_pesaje():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin selección", "Seleccione un pesaje para imprimir.")
            return
        clave = tree.item(selected_items[0], "values")[0]

        messagebox.showinfo("Editar", f"Aún no implementado: edición de datos para {clave}")

    tk.Button(frame_botones_tabla, text="🖨 Imprimir", command=imprimir_seleccionado).pack(side="left", padx=10)
    tk.Button(frame_botones_tabla, text="✏️ Editar", command=editar_datos_pesaje).pack(side="left", padx=10)




    # Subclientes de Externo
    clientes_externos = {
        "Tercero (pago inmediato)": "Pago inmediato",
        "Cipreses de Colombia": "Pago mensual",
        "Núcleos de Madera": "Pago mensual",
        "Construinmuniza": "Pago mensual"
    }

    # Función llamada al seleccionar cliente
    
    def seleccionar_cliente_externo(nombre_cliente):
        frame_subclientes.pack_forget()
        
        # 👉 condición para externos Tercero (pago inmediato)
        if nombre_cliente == "Tercero (pago inmediato)":
            mostrar_formulario_externo_tercero(
                nombre_cliente, "Externo", ventana, frame_formulario, refrescar_tabla_pesajes, limpiar_formulario_unicamente
            )
        # 👉 condición para externos (pago mensual)
        elif nombre_cliente in ["Cipreses de Colombia", "Núcleos de Madera", "Construinmuniza"]:
            mostrar_formulario_externo_pago_mensual(
                nombre_cliente, "Externo", ventana, frame_formulario, refrescar_tabla_pesajes, limpiar_formulario_unicamente
            )
        else:
            verificar_servicio("Externo", cliente_seleccionado=nombre_cliente)


    #declaro variable booleanda para controlar estado de visibilidad de botones clientes
    mostrar_clientes = tk.BooleanVar(value=False)  # Estado inicial: oculto

    
    # Función llamada al presionar botón principal
    def manejar_servicio(tipo):
        #verifico si funcion de proceso de impresion esta activa (si archivo puntero esta creado) para bloquear los botones principales
        if proceso_impresion_activo():
            messagebox.showinfo("Proceso activo", "Ya hay un proceso en curso. Finalícelo antes de iniciar otro.")
            return
        
       

        if tipo == "Externo":
            
            # 🔒 Activar archivo que indica proceso de ingreso de datos(creo archivo puntero)
            with open(".proceso_impresion_activo", "w") as f:
                f.write("1")

            verificar_servicio(tipo) #funcion para capturar peso actual en variable global
            
            #ventana.geometry("722x680")  # 👈 Ajusta tamaño al mostrar botones externos
            centrar_ventana(ventana, 722, 680, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario
            
            # Limpiar y mostrar botones de cliente
            for widget in frame_subclientes.winfo_children():
                widget.destroy()

            tk.Label(frame_subclientes, text="Seleccione el cliente externo:",
                    font=("Arial", 10)).pack(pady=(0, 5))

            for nombre_cliente in clientes_externos:
                tk.Button(frame_subclientes, text=nombre_cliente,
                        width=30, font=("Arial", 9),
                        command=lambda n=nombre_cliente: seleccionar_cliente_externo(n)
                        ).pack(pady=2)

            # 🔘 Botón cancelar para cerrar submenú de clientes
            def cancelar_clientes():
                frame_subclientes.pack_forget()
                cerrar_proceso_impresion()  # Elimina archivo puntero
                mostrar_clientes.set(False)
                #ventana.geometry("722x529")  # 👈 Restaura tamaño original al cerrar el formulario
                centrar_ventana(ventana, 722, 529, margen_superior=50)  # 👈 Restaura tamaño original y centrar ventana original al cerrar el formulario

            tk.Button(frame_subclientes, text="❌ Cancelar", font=("Arial", 10),
                    command=cancelar_clientes).pack(pady=(10, 5))

            frame_subclientes.pack()
            mostrar_clientes.set(True)
        else:
            # 🔒 Activar proceso para los otros botones principales
            with open(".proceso_impresion_activo", "w") as f:
                f.write("1")
            
            # Otro tipo de servicio → ocultar subclientes si estaban abiertos
            frame_subclientes.pack_forget()#oculta botones
            mostrar_clientes.set(False)
            
            verificar_servicio(tipo) #funcion para capturar peso actual en variable global
    
    
    
    
    tipos = ["Externo", "Aserrio", "Inmuniza", "Astillable"]
    for tipo in tipos:
        tk.Button(frame_botones, text=tipo, width=10, font=("Arial", 9),
                command=lambda t=tipo: manejar_servicio(t)).pack(side="left", padx=5)
 
    # 🔻 Contenedor reservado para los formularios embebidos
    # Esto asegura que siempre aparezca debajo de los botones principales
    frame_formulario = tk.Frame(ventana)
    frame_formulario.pack(pady=10, fill="x")

    # 🔻 Contenedor para mostrar pesajes abiertos o resultados
    # Esto aparecerá siempre debajo del formulario
    frame_estado_pesajes = tk.Frame(ventana)
    frame_estado_pesajes.pack(pady=10)

      

    ventana.mainloop()  # Inicia el bucle principal de la ventana (la mantiene abierta)


# Si el archivo se ejecuta directamente, se lanza la función de servicio
if __name__ == "__main__":
    import signal
    import sys

    def cerrar_gracioso(sig, frame):
        print("🔴 Señal de terminación recibida. Cerrando ventana de báscula...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, cerrar_gracioso)
    signal.signal(signal.SIGINT, cerrar_gracioso)  # Ctrl+C, por si acaso

    try:
        modulo_servicio()
    except Exception as e:
        print(f"⛔ módulo3 cerrado por excepción: {e}")
