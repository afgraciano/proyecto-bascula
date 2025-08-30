# === Importación de módulos necesarios ===
import tkinter as tk  # Para la interfaz gráfica
from tkinter import ttk, messagebox, filedialog  # Widgets y mensajes de Tkinter
from datetime import datetime  # Para manejar fechas
from datetime import timedelta #para tomar reportes del ultimo dia
from tkcalendar import Calendar #para usar calendario
import mysql.connector  # Conexión a MySQL
import pandas as pd  # Manipulación de datos y exportación a Excel
import os  # Operaciones con archivos y deteccion de ejecutables
import tkinter.font as tkFont #para autoajustar las columnas
import subprocess #importo subprocesos para realizar copias de seguridad de Mysql
import win32print, win32ui # 🆕 Para impresión
import win32com.client
import pyodbc
import shutil


def crear_base_access(ruta):
    # Crea archivo .accdb vacío
    engine = win32com.client.Dispatch("DAO.DBEngine.120")  # Para Access 2007+
    db = engine.CreateDatabase(ruta, ";LANGID=0x0409;CP=1252;COUNTRY=0", 64)  
    db.Close()


# Funcion para centrar la ventana principal
def centrar_ventana(ventana, ancho, alto, margen_superior=50):
    ventana.update_idletasks()  # Asegura que se puedan obtener dimensiones actualizadas
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (pantalla_ancho - ancho) // 2
    y = margen_superior  # Espacio desde la parte superior
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")



# === Encabezado único para impresión y preview ===
ENCABEZADO_TIQUETE = (
    "Reforestadora El Guásimo S.A.S\n"
    "con NIT: 890940852-0\n"
    "Presta servicio de bascula a:\n\n"
)


# === Función para imprimir directamente en impresora ===
def imprimir_tiquete(texto, impresora=None):
    if impresora is None:
        impresora = win32print.GetDefaultPrinter()

    if not impresora:
        messagebox.showerror("Error impresión", "No hay impresora predeterminada configurada.")
        return

    hprinter = win32print.OpenPrinter(impresora)
    try:
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(impresora)

        dpi = hdc.GetDeviceCaps(88)       # LOGPIXELSX
        width_px = hdc.GetDeviceCaps(110) # HORZRES
        height_px = hdc.GetDeviceCaps(111)# VERTRES

        chars_per_line = max(len(line) for line in texto.split("\n")) or 1
        font_size = max(24, int(width_px / (chars_per_line + 2)))

        hdc.StartDoc("Tiquete Báscula")
        hdc.StartPage()

        fuente = win32ui.CreateFont({"name": "Consolas", "height": font_size, "weight": 700})
        hdc.SelectObject(fuente)

        y = 50
        line_spacing = int(font_size * 1.5)

        # Encabezado
        fuente_titulo = win32ui.CreateFont({"name": "Consolas", "height": font_size + 8, "weight": 900})
        hdc.SelectObject(fuente_titulo)
        for linea_titulo in ENCABEZADO_TIQUETE.strip().split("\n"):
            hdc.TextOut(50, y, linea_titulo)
            y += line_spacing

        y += line_spacing
        fuente_normal = win32ui.CreateFont({"name": "Consolas", "height": font_size, "weight": 700})
        hdc.SelectObject(fuente_normal)
        for linea in texto.split("\n"):
            hdc.TextOut(50, y, linea)
            y += line_spacing

        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
    finally:
        win32print.ClosePrinter(hprinter)
        
        
# === Gestión de archivo puntero para impresión ===
# proceso_impresion_activo_reportes() -> Verifica si hay impresión activa
# cerrar_proceso_impresion() -> Elimina el puntero cuando ya no hay ventanas abiertas
# mostrar_tiquete_con_impresion() -> Crea el puntero y abre la ventana del tiquete

ARCHIVO_PUNTERO_IMPRESION = ".proceso_impresion_activo_reportes"

 # === funcion Devuelve True si hay un tiquete de impresión abierto (archivo puntero existe) ===
def proceso_impresion_activo():
    return os.path.exists(ARCHIVO_PUNTERO_IMPRESION)

# === Función que elimina archivo puntero cuando no hay impresión activa ===
def cerrar_proceso_impresion():
    try:
        os.remove(ARCHIVO_PUNTERO_IMPRESION)
    except FileNotFoundError:
        pass


# === Función para mostrar preview de tiquete e imprimir ===
# Lista global de ventanas activas
ventanas_tiquete_abiertas = []

# === Ventana preview de tiquete (con puntero activo) ===
def mostrar_tiquete_con_impresion(titulo, contenido):
    """
    Muestra un tiquete en ventana de preview e imprime.
    Solo permite un tiquete activo a la vez.
    Resetea puntero si existe de sesiones anteriores.
    """
    # Verificar si hay un tiquete abierto
    if proceso_impresion_activo():
        try:
            # Intentar abrir ventana anterior (si existe) o alertar
            messagebox.showwarning(
                "Impresión en curso",
                "Ya hay un tiquete abierto. Ciérrelo antes de abrir otro."
            )
            return
        except Exception:
            # Si el puntero existe pero la ventana anterior se cerró de forma inesperada
            cerrar_proceso_impresion()  # elimina el puntero residual


    # Crear archivo puntero cuando se abre el tiquete
    with open(ARCHIVO_PUNTERO_IMPRESION, "w") as f:
        f.write("Proceso de impresión activo")

    # Crear ventana del tiquete
    ventana = tk.Toplevel()
    ventana.title(titulo)
    centrar_ventana(ventana, 410, 500, margen_superior=50)
    ventana.resizable(False, False)
    ventana.attributes("-topmost", True)

    ventanas_tiquete_abiertas.append(ventana)

    # Área de texto
    text_area = tk.Text(ventana, wrap="word", font=("Consolas", 10))
    text_area.pack(expand=True, fill="both", padx=10, pady=10)

    texto_completo = ENCABEZADO_TIQUETE + contenido
    text_area.insert("1.0", texto_completo)
    text_area.config(state="disabled")

    # Frame de botones
    frame_botones = tk.Frame(ventana)
    frame_botones.pack(pady=10)

    # --- Botón imprimir en impresora predeterminada ---
    def imprimir_default():
        try:
            imprimir_tiquete(texto_completo)
        except Exception as e:
            messagebox.showerror("Error de impresión", f"No se pudo imprimir.\n{e}")
        
    # --- Botón seleccionar impresora ---
    def seleccionar_e_imprimir():
        sub = tk.Toplevel()
        sub.title("Seleccionar impresora")
        sub.geometry("400x150")
        sub.resizable(False, False)
        sub.attributes("-topmost", True)

        sub.grab_set()
        sub.focus_set()

        tk.Label(sub, text="Seleccione una impresora instalada:", font=("Consolas", 11)).pack(pady=10)

        impresoras = win32print.EnumPrinters(2)
        nombres = [p[2] for p in impresoras]
        
        if not nombres:
            messagebox.showerror("Error", "No se encontraron impresoras instaladas.")
            sub.destroy()
            return
                
        seleccion = tk.StringVar(value=nombres[0] if nombres else "")

        lista = tk.OptionMenu(sub, seleccion, *nombres)
        lista.config(width=40)
        lista.pack(pady=5)

  
        def imprimir_seleccionada():
            impresora = seleccion.get()

            if not impresora:
                messagebox.showwarning("Impresora", "No se seleccionó ninguna impresora.")
                return

            try:
                imprimir_tiquete(texto_completo, impresora)
            except Exception as e:
                messagebox.showerror("Error de impresión", f"No se pudo imprimir en {impresora}.\n\n{e}")
            sub.destroy()

        tk.Button(sub, text="🖨 Imprimir", command=imprimir_seleccionada).pack(pady=10)

    # --- Botón cerrar ventana ---
    def cerrar_ventana():
        if ventana in ventanas_tiquete_abiertas:
            ventanas_tiquete_abiertas.remove(ventana)
        if not ventanas_tiquete_abiertas:
            cerrar_proceso_impresion()
        ventana.destroy()

    # --- Botones principales en la ventana ---
    tk.Button(frame_botones, text="🖨 Imprimir (predeterminada)", command=imprimir_default).pack(side="left", padx=5)
    tk.Button(frame_botones, text="🖨 Seleccionar impresora...", command=seleccionar_e_imprimir).pack(side="left", padx=5)
    tk.Button(frame_botones, text="❌ Cerrar", command=cerrar_ventana).pack(side="left", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", cerrar_ventana)
    


# Importa pyodbc si está disponible, para exportar a Access
try:
    import pyodbc
except ImportError:
    pyodbc = None

# Importa FPDF si está disponible, para exportar a PDF
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None
    


# === Clase principal para la interfaz de reportes ===
class ReportesBasculaApp:
    
    # ==========================================================
    # 📌 MÉTODO DE IMPRESIÓN DE REGISTROS SELECCIONADOS EN TABLA
    # ==========================================================
    def imprimir_seleccionado(self):
        # ✅ Bloquear si ya hay un tiquete abierto
        if proceso_impresion_activo():
            messagebox.showinfo(
                "Impresión en curso",
                "Ya hay un tiquete abierto.\n\nCierre la ventana actual antes de abrir otro."
            )
            return
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sin selección", "Seleccione un registro para imprimir.")
            return

        index = self.tree.index(selected[0])
        datos = self.datos_actuales[index]

        id_ingresado = datos.get("id_ingresado") or datos.get("id_pesaje")
        tipo_cliente = datos.get("tipo_cliente", "desconocido")
        nombre = datos.get("nombre", "N/A")
        nit = datos.get("cedula_nit", "N/A")
        fecha = datos.get("fecha_hora", "")
        bruto = datos.get("peso_bruto", 0)
        tara = datos.get("peso_tara", 0)
        neto = datos.get("peso_neto", 0)
        placa = datos.get("placa", "")

        # --- Detectar empresa según tipo_cliente ---
        if tipo_cliente == "interno":
            if "RG" in str(id_ingresado):
                nombre = "Reforestadora El Guásimo S.A.S"
                nit = "8909408520"
            elif "MS" in str(id_ingresado):
                nombre = "MS Timberland Holdings Limited"
                nit = "9004023313"

        contenido = (
            f"Cliente: {nombre}\n"
            f"NIT: {nit}\n"
            f"ID: {id_ingresado}\n"
            f"Placa: {placa}\n"
            f"Peso Bruto: {bruto} kg\n"
            f"Peso Tara: {tara} kg\n"
            f"Peso Neto: {neto} kg\n"
            f"Fecha final: {fecha}"
        )
        # mostramos el tiquete (crea el puntero)
        mostrar_tiquete_con_impresion("Reporte de Báscula", contenido)
    
    # Funcion para seleccionar fechas en calendario
    def seleccionar_fecha(self, entry_widget):
        top = tk.Toplevel(self.root)
        top.title("Seleccionar fecha")
        top.transient(self.root)   # Asociar a ventana principal
        top.grab_set()             # Bloquear interacción con root
        top.focus_set()            # Dar foco inmediato al calendario

        cal = Calendar(top, date_pattern="yyyy-mm-dd")
        cal.pack(pady=10)


        def confirmar():
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, cal.get_date())
            top.destroy()

        ttk.Button(top, text="OK", command=confirmar).pack()
    
    # Constructor de clase ReportesBasculaApp.
    """
    - Inicializa la ventana principal y todos los elementos de la interfaz gráfica:
    - Configuración inicial de la ventana (título, tamaño).
    - Creación de filtros de búsqueda (tipo de reporte, fechas, cliente, etc.).
    - Configuración de botones de consulta y exportación (Excel, Access, PDF).
    - Creación de la tabla Treeview con scrollbars para mostrar resultados.
    - Definición de variables internas para manejo de datos.
    """
    def __init__(self, root):
        
        #if os.path.exists(ARCHIVO_PUNTERO_IMPRESION):
            #os.remove(ARCHIVO_PUNTERO_IMPRESION)
        
        self.db_password = "bascula2025"  # guardo la contraseña de MySQL dentro de la clase para ser usada
        
        self.root = root
        self.root.title("Consulta y Reportes - Báscula")
        self.root.geometry("1300x650")  # Tamaño inicial de ventana
        #desde aqui hubico la ventana en la mitad de la pantalla
        # Tamaño inicial
        ancho_ventana = 1300
        alto_ventana = 650

        # Obtener dimensiones de la pantalla
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()

        # Calcular posición x, y para centrar
        pos_x = int((ancho_pantalla / 2) - (ancho_ventana / 2))
        pos_y = int((alto_pantalla / 2) - (alto_ventana / 2))

        # Establecer tamaño y posición centrada
        self.root.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")
        
        #hasta aqui es para centrar el programa en la pantalla al iniciar
        

        self.tipo_reporte = tk.StringVar(value="pesajes")  # Valor predeterminado

        # ==== Frame o seleccion de filtros ====
        filtro_frame = ttk.LabelFrame(root, text="Filtros")
        filtro_frame.pack(fill="x", padx=10, pady=5)

        # Selector de tipo de reporte
        ttk.Label(filtro_frame, text="Tipo de reporte:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_tipo = ttk.Combobox(filtro_frame, textvariable=self.tipo_reporte, values=["pesajes", "desconexiones"], state="readonly")
        self.combo_tipo.grid(row=0, column=1, padx=5, pady=5)

        # Fechas de búsqueda
        # Filtro: Fecha inicial
        ttk.Label(filtro_frame, text="Fecha inicial (YYYY-MM-DD):").grid(row=0, column=2, padx=5) #label trasparente indicar formato fecha
        #self.fecha_inicio = ttk.Entry(filtro_frame)
        #self.fecha_inicio.grid(row=0, column=3, padx=5)

        frame_fecha_inicio = ttk.Frame(filtro_frame)  # Contenedor para campo + botón
        frame_fecha_inicio.grid(row=0, column=3, padx=5, pady=5)
        self.fecha_inicio = ttk.Entry(frame_fecha_inicio, width=12)
        self.fecha_inicio.pack(side="left", fill="x", expand=True)

        # Botón calendario inicio
        #ttk.Button(filtro_frame, text="📅", width=3, command=lambda: self.seleccionar_fecha(self.fecha_inicio)).grid(row=0, column=4, padx=2)
        ttk.Button(frame_fecha_inicio, text="📅", width=2, command=lambda: self.seleccionar_fecha(self.fecha_inicio)).pack(side="right")
        
        # Filtro: Fecha final
        ttk.Label(filtro_frame, text="Fecha final (YYYY-MM-DD):").grid(row=0, column=4, padx=5)#label trasparente indicar formato fecha
        #self.fecha_fin = ttk.Entry(filtro_frame)
        #self.fecha_fin.grid(row=0, column=5, padx=5)
        frame_fecha_fin = ttk.Frame(filtro_frame)  # Contenedor para campo + botón
        frame_fecha_fin.grid(row=0, column=5, padx=5, pady=5)
        self.fecha_fin = ttk.Entry(frame_fecha_fin, width=12)
        self.fecha_fin.pack(side="left", fill="x", expand=True)
        
        # Botón calendario final
        #ttk.Button(filtro_frame, text="📅", width=3, command=lambda: self.seleccionar_fecha(self.fecha_fin)).grid(row=0, column=7, padx=2)
        ttk.Button(frame_fecha_fin, text="📅", width=2, command=lambda: self.seleccionar_fecha(self.fecha_fin)).pack(side="right")
        
        #ingreso fecha actual por defecto al abrir programa
        hoy = datetime.now().strftime("%Y-%m-%d")
        self.fecha_inicio.insert(0, hoy)
        self.fecha_fin.insert(0, hoy)
        
        # Pasar foco con Enter
        self.fecha_inicio.bind("<Return>", lambda e: self.fecha_fin.focus_set())
        self.fecha_fin.bind("<Return>", lambda e: self.consultar())

        # Filtro por placa o nombre (solo para pesaje)
        ttk.Label(filtro_frame, text="Cliente / Placa / Cedula o Nit:").grid(row=1, column=0, padx=5, pady=5)
        self.valor_filtro = ttk.Entry(filtro_frame, width=30)
        self.valor_filtro.grid(row=1, column=1, padx=5, pady=5)

        # Filtro por tipo_cliente (tercero, mensual, interno) (solo para pesaje)
        ttk.Label(filtro_frame, text="Tipo cliente:").grid(row=1, column=2, padx=5, pady=5)
        self.filtro_tipo_cliente = ttk.Combobox(filtro_frame, values=["Todos", "tercero", "mensual", "interno"], state="readonly")
        self.filtro_tipo_cliente.grid(row=1, column=3, padx=5, pady=5)
        self.filtro_tipo_cliente.set("Todos")  # Valor por defecto

        # Botón de consulta
        ttk.Button(filtro_frame, text="Consultar", command=self.consultar).grid(row=1, column=5, padx=5, pady=5, sticky="ew")

        # === Tabla para mostrar resultados con scroll (Treeview + Scrollbars) ===
        tree_frame = ttk.Frame(root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview con scrollbars
        self.tree = ttk.Treeview(
            tree_frame,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Configuración de scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Ajustar expansión del Treeview dentro del frame
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)


        # === Botones de exportación y respaldo ===
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", pady=5)  # aquí solo colocamos el frame con pack

        # Exportar
        ttk.Button(btn_frame, text="Exportar a Excel", command=self.exportar_excel).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Exportar a Access", command=self.exportar_access).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=2, padx=5, pady=5)

        # Espacio vacío para empujar los de respaldo
        btn_frame.grid_columnconfigure(3, weight=1)
        
        # Botones de copia de seguridad, impresion y restauracion
        
        # Botón copia de seguridad (misma columna que Consultar, fila siguiente)
        ttk.Button(btn_frame, text="Copia de seguridad", command=self.backup_base_datos).grid(row=0, column=3, padx=5, pady=5)

        #Boton imprimir seleccionado de la tabla de datos
        ttk.Button(btn_frame, text="🖨 Imprimir seleccionado", command=self.imprimir_seleccionado).grid(row=0, column=6, padx=5, pady=5)

        # Botón restaurar copia (misma columna que Consultar, fila siguiente)
        ttk.Button(btn_frame, text="Restaurar Copia Seguridad", command=self.restaurar_base_datos).grid(row=0, column=5, padx=5, pady=5, sticky="ew")


        #ttk.Button(btn_frame, text="Copia de seguridad", command=self.backup_base_datos).grid(row=0, column=5, padx=5)
        #ttk.Button(btn_frame, text="Restaurar Copia Seguridad", command=self.restaurar_base_datos).grid(row=0, column=6, padx=5)


        self.datos_actuales = []  # Aquí se guardan los datos cargados


     
    
    #funcion para ajustar las columnas
    def autoajustar_columnas(self, max_filas=200):
        filas = self.tree.get_children()[:max_filas]  # solo primeras 200 filas
        
        for col in self.tree["columns"]:
            longitudes = [len(str(self.tree.set(k, col))) for k in filas]
            longitudes.append(len(col))  # también medir el nombre de la columna
            max_len = max(longitudes, default=10)
            self.tree.column(col, width=(max_len * 7))

    # === CONSULTA MYSQL ===
    def consultar(self):
        tipo = self.tipo_reporte.get()
        fi = self.fecha_inicio.get()
        ff = self.fecha_fin.get()
        filtro_valor = self.valor_filtro.get().strip()
        tipo_cliente = self.filtro_tipo_cliente.get().strip()

        if tipo_cliente == "Todos":
            tipo_cliente = ""  # sin filtro especifico

        # Validación de fechas
        try:
            fecha_inicio = datetime.strptime(fi, "%Y-%m-%d")
            fecha_fin = datetime.strptime(ff, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1) #adelanto 1 dia y le resto 1 segundo para que tome registros del ultimo dia indicado
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Usa YYYY-MM-DD.")
            return


        # Conexión a MySQL (con manejo de errores)
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="bascula2025",
                database="bascula_silvotecnia"
            )
            cursor = conn.cursor(dictionary=True)
        except mysql.connector.Error as err:
            messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos.\n\nDetalles: {err}")
            return
        

        if tipo == "pesajes":
            # Iniciamos la lista de parámetros para la consulta SQL.
            # Los primeros dos parámetros siempre serán fecha_inicio y fecha_fin (corresponden a los primeros %s).
            valores = [fecha_inicio, fecha_fin]

            # Si el filtro de tipo_cliente es exactamente "tercero" -> hacemos JOIN con cliente_tercero
            if tipo_cliente == "tercero":
                # Construimos la consulta SQL específica para clientes terceros.
                # Seleccionamos campos del pesaje (p.*) y los datos del cliente tercero (t.nombre, t.cedula_nit, t.correo_remision).
                # LEFT JOIN asegura que aunque no exista fila en cliente_tercero, el pesaje se devuelva (con campos NULL).
                # WHERE p.fecha_hora BETWEEN %s AND %s usa los dos primeros parámetros en `valores`.
                consulta = """
                    SELECT p.id_pesaje, 
                        t.id_ingresado, 
                        p.fecha_hora, 
                        p.tipo_cliente,
                        p.peso_bruto, p.peso_tara, p.peso_neto, p.placa,
                        t.nombre, t.cedula_nit, t.correo_remision,
                        SUBSTRING_INDEX(pa.nombre, ' ', 1) AS nombre_autorizado
                    FROM pesajes p
                    LEFT JOIN cliente_tercero t ON p.id_cliente = t.id_cliente
                    LEFT JOIN personal_autorizado pa ON p.id_autorizado = pa.id_autorizado
                    WHERE p.fecha_hora BETWEEN %s AND %s
                """
            # Si el filtro es "mensual" -> hacemos JOIN con cliente_mensual
            elif tipo_cliente == "mensual":
                # Seleccionamos los campos del pesaje y de la tabla cliente_mensual.
                # Alias m.nit AS cedula_nit se usa para normalizar el nombre de columna (para que el resto del código lo vea igual).
                consulta = """
                    SELECT p.id_pesaje,
                        m.id_ingresado, 
                        p.fecha_hora, 
                        p.tipo_cliente,
                        p.peso_bruto, p.peso_tara, p.peso_neto, p.placa,
                        m.nombre, m.nit, NULL AS correo_remision,
                        SUBSTRING_INDEX(pa.nombre, ' ', 1) AS nombre_autorizado
                    FROM pesajes p
                    LEFT JOIN cliente_mensual m ON p.id_cliente = m.id_cliente
                    LEFT JOIN personal_autorizado pa ON p.id_autorizado = pa.id_autorizado
                    WHERE p.fecha_hora BETWEEN %s AND %s
                """
            # Si el filtro es "interno" -> hacemos JOIN con cliente_interno
            elif tipo_cliente == "interno":
                # Seleccionamos los campos del pesaje y de cliente_interno.
                # Como cliente_interno no tiene campo 'correo_remision', devolvemos NULL AS correo_remision
                # y renombramos i.nit como cedula_nit para coherencia con la interfaz.
                consulta = """
                    SELECT p.id_pesaje,
                        i.id_ingresado, p.fecha_hora, i.tipo AS tipo_cliente,
                        p.peso_bruto, p.peso_tara, p.peso_neto, p.placa,
                        i.nombre, i.nit, NULL AS correo_remision,
                        SUBSTRING_INDEX(pa.nombre, ' ', 1) AS nombre_autorizado
                    FROM pesajes p
                    LEFT JOIN cliente_interno i ON p.id_cliente = i.id_cliente
                    LEFT JOIN personal_autorizado pa ON p.id_autorizado = pa.id_autorizado
                    WHERE p.fecha_hora BETWEEN %s AND %s
                """
            else:  # Si no se pidió un tipo específico -> "Todos"
                # Para la vista "Todos" hacemos LEFT JOIN a las tres tablas, pero filtrando cada JOIN
                # para que el id_cliente se relacione solo con la tabla correspondiente según p.tipo_cliente.
                # Además usamos COALESCE para obtener el primer nombre/nit no NULL entre las tres tablas.
                consulta = """               
                    SELECT p.id_pesaje,
                        COALESCE(t.id_ingresado, m.id_ingresado, i.id_ingresado) AS id_ingresado,
                        p.fecha_hora, 
                        COALESCE(i.tipo, p.tipo_cliente) AS tipo_cliente,  
                        p.peso_bruto, p.peso_tara, p.peso_neto, p.placa,
                        COALESCE(t.nombre, m.nombre, i.nombre) AS nombre,
                        COALESCE(t.cedula_nit, m.nit, i.nit) AS cedula_nit,
                        COALESCE(t.correo_remision, '') AS correo_remision,
                        SUBSTRING_INDEX(pa.nombre, ' ', 1) AS nombre_autorizado
                    FROM pesajes p
                    LEFT JOIN cliente_tercero t ON (p.tipo_cliente = 'tercero' AND p.id_cliente = t.id_cliente)
                    LEFT JOIN cliente_mensual m ON (p.tipo_cliente = 'mensual' AND p.id_cliente = m.id_cliente)
                    LEFT JOIN cliente_interno i ON (p.tipo_cliente = 'interno' AND p.id_cliente = i.id_cliente)
                    LEFT JOIN personal_autorizado pa ON p.id_autorizado = pa.id_autorizado
                    WHERE p.fecha_hora BETWEEN %s AND %s
                """
               
            # ---- A partir de aquí agregamos filtros dinámicos según lo que el usuario haya puesto ----

            # Si se especificó un tipo_cliente (no vacío), añadimos una condición para filtrar por tipo_cliente.
            # IMPORTANTE: el orden de los parámetros en `valores` debe coincidir con los %s en la consulta SQL.
            if tipo_cliente:
                consulta += " AND p.tipo_cliente = %s"
                valores.append(tipo_cliente)   # este valor será usado en el siguiente %s encontrado en la consulta

            # Si el usuario escribió algo en el filtro libre (placa / cedula / nombre), añadimos condiciones LIKE.
            if filtro_valor:
                # Si ya estamos filtrando por un tipo específico (tercero/mensual/interno),
                # entonces en la SELECT ya existe la columna `nombre` y `cedula_nit` (por el JOIN específico).
                # Podemos comparar p.placa, nombre y cedula_nit.
                if tipo_cliente in ("tercero", "mensual", "interno"):
                    consulta += " AND (p.placa LIKE %s OR nombre LIKE %s OR cedula_nit LIKE %s)"
                    # Extendemos `valores` con la misma máscara tres veces (para cada %s añadido).
                    valores.extend([f"%{filtro_valor}%"] * 3)
                else:  # Si es "Todos"
                    # En "Todos" podemos buscar por placa, NIT, nombre o tipo_cliente.
                    consulta += """ 
                        AND (
                            p.placa LIKE %s OR 
                            COALESCE(t.cedula_nit, m.nit, i.nit) LIKE %s OR 
                            COALESCE(t.nombre, m.nombre, i.nombre) LIKE %s OR 
                            p.tipo_cliente LIKE %s
                        )
                    """
                    # Añadimos 4 parámetros en el mismo orden que los %s de la consulta
                    valores.extend([f"%{filtro_valor}%"] * 4)

            # Orden final por fecha (descendente)
            consulta += " ORDER BY p.fecha_hora DESC"

            # Ejecutamos la consulta con parámetros. `valores` contiene exactamente tantos elementos como %s en la consulta.
            cursor.execute(consulta, valores)


        else:
            # Consulta de desconexiones
            cursor.execute("""
                SELECT * FROM desconexiones
                WHERE fecha_hora BETWEEN %s AND %s
                ORDER BY fecha_hora DESC
            """, (fecha_inicio, fecha_fin))

        resultados = cursor.fetchall()
        conn.close()


        # Mostrar resultados en la tabla
        # Limpiar Treeview
        self.tree.delete(*self.tree.get_children())

        if resultados:
            # Convertimos resultados a lista de dicts para manipular columnas
            datos_modificados = []

            for fila in resultados:
                fila_mod = dict(fila)  # copia para no modificar original
                # Si existe id_pesaje e id_ingresado, ponemos id_ingresado con el valor de id_ingresado
                # y eliminamos id_pesaje para no mostrarla en la tabla.
                if "id_pesaje" in fila_mod and "id_ingresado" in fila_mod:
                    # Reemplazar id_pesaje por id_ingresado en la fila para la vista
                    fila_mod["id_pesaje"] = fila_mod["id_ingresado"]
                    # También puedes eliminar la columna id_ingresado para no duplicar (opcional)
                    del fila_mod["id_ingresado"]
                datos_modificados.append(fila_mod)

            columnas = list(datos_modificados[0].keys())
            self.tree.config(columns=columnas, show="headings")

            for col in columnas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=130, anchor="center")

            for row in datos_modificados:
                self.tree.insert("", "end", values=list(row.values()))

            # === Ajustar ancho de columnas automáticamente ===
            self.autoajustar_columnas()
            self.datos_actuales = resultados  # aquí guardamos el original sin modificaciones para uso interno

        else:
            messagebox.showinfo("Sin datos", "No se encontraron registros en ese rango de fechas.")
            self.datos_actuales = []

    # Función para preparar datos antes de exportar cambiando id pesaje por id ingresado
    def _preparar_datos_exportacion(self):
        datos_modificados = []
        for fila in self.datos_actuales:
            fila_mod = dict(fila)
            if "id_pesaje" in fila_mod and "id_ingresado" in fila_mod:
                fila_mod["id_pesaje"] = fila_mod["id_ingresado"]
                del fila_mod["id_ingresado"]
            datos_modificados.append(fila_mod)
        return datos_modificados


    # === Exportación a EXCEL ===
    def exportar_excel(self):
        if not self.datos_actuales:
            messagebox.showerror("Error", "Primero consulta los datos.")
            return

        archivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if archivo:
            datos_export = self._preparar_datos_exportacion()
            df = pd.DataFrame(datos_export)
            #excepcion si el archivo que se va a sobre escribir esta abierto
            try:
                df.to_excel(archivo, index=False)
                messagebox.showinfo("Éxito", f"Exportado a Excel: {archivo}")
            except PermissionError:
                messagebox.showerror("Error", f"No se puede sobrescribir el archivo.\nAsegúrate de cerrarlo primero:\n{archivo}")


   
    # === Exportación a ACCESS ===
    def exportar_access(self):
        if not self.datos_actuales:
            messagebox.showerror("Error", "Primero consulta los datos.")
            return
        if not pyodbc:
            messagebox.showerror("Error", "pyodbc no está instalado.")
            return

        archivo = filedialog.asksaveasfilename(defaultextension=".accdb", filetypes=[("Access", "*.accdb")])
        if not archivo:
            return  # Cancelado por el usuario

        # Crear archivo vacío si no existe
        if not os.path.exists(archivo):
            # Opción 1: copiar una base vacía de Access como plantilla
            plantilla = r"C:\Windows\SysWOW64\msaccess.accdb"  # ejemplo
            if os.path.exists(plantilla):
                shutil.copy(plantilla, archivo)
            else:
                # Opción 2: crear un archivo vacío (el driver lo acepta igual)
                #open(archivo, "w").close()
                if not os.path.exists(archivo):
                    crear_base_access(archivo)

        datos_export = self._preparar_datos_exportacion()
        df = pd.DataFrame(datos_export)

        tabla = "reporte"
        conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={archivo};"

        try:
            # Intentar conexión inicial para borrar tabla si ya existe
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {tabla}")
            conn.close()
        except pyodbc.Error as e:
            if "Permission denied" in str(e) or "being used by another process" in str(e):
                messagebox.showerror("Error", f"No se puede sobrescribir el archivo:\n{archivo}\nCierre el archivo si está abierto y vuelva a intentarlo.")
                return
            # Si no era ese error, se continúa sin eliminar la tabla

        
            # Crear nueva conexión para insertar datos
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Si la tabla no existe, crearla con las columnas del DataFrame
            columnas = df.columns
            columnas_def = ", ".join([f"[{col}] TEXT" for col in columnas])
            cursor.execute(f"CREATE TABLE {tabla} ({columnas_def})")

            # Insertar filas
            for _, fila in df.iterrows():
                placeholders = ", ".join(["?"] * len(fila))
                cursor.execute(
                    f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({placeholders})",
                    tuple(str(x) for x in fila.values)
                )

            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Éxito", f"Exportado a Access: {archivo}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a Access.\n\nDetalles: {e}")


    # === Exportación a PDF con ajuste de ancho ===
    def exportar_pdf(self):
        if not self.datos_actuales:
            messagebox.showerror("Error", "Primero consulta los datos.")
            return
        if not FPDF:
            messagebox.showerror("Error", "fpdf no está instalado.")
            return

        archivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if archivo:
            pdf = FPDF(orientation="L", unit="mm", format="A4")  # Horizontal
            pdf.add_page()
            pdf.set_font("Consolas", size=7)    
            
            datos_export = self._preparar_datos_exportacion()
            df = pd.DataFrame(datos_export)
            columnas = df.columns.tolist()
            
            
            # Reorganizamos columnas para que correo quede más al final
            if "correo_remision" in columnas:
                columnas.remove("correo_remision")
                columnas.append("correo_remision")

            # Anchos personalizados (en mm) para cada columna si existe para no sobrepasar 270mm(margen incluido)
            ancho_personalizado = {
                "id_pesaje": 30,
                "id_ingresado": 30,
                "nombre": 50,
                "cedula_nit": 25,
                "fecha_hora": 35,
                "tipo_cliente": 20,
                "peso_bruto": 22,
                "peso_tara": 22,
                "peso_neto": 25,
                "placa": 15,
                "correo_remision": 48
            }
            ancho_total = sum(ancho_personalizado.get(col, 30) for col in columnas)
            row_height = 6
            
            # Encabezados
            for col in columnas:
                ancho = ancho_personalizado.get(col, 30)
                pdf.cell(ancho, row_height, str(col)[:25], border=1) #recortar titulos largos
            pdf.ln(row_height)

            # Filas de contenido
            for _, row in df.iterrows():
                for col in columnas:
                    texto = str(row[col])
                    ancho = ancho_personalizado.get(col, 30)
                    if len(texto) > 40:
                        texto = texto[:37] + "..."  #recortar textos muy largos
                    pdf.cell(ancho, row_height, texto, border=1)
                pdf.ln(row_height)
            #excepcion si el archivo que se va a sobre escribir esta abierto
            try:
                pdf.output(archivo)
                messagebox.showinfo("Éxito", f"Exportado a PDF: {archivo}")
            except PermissionError:
                messagebox.showerror("Error", f"No se puede sobrescribir el PDF.\nCierra el archivo primero:\n{archivo}")

    
    # Funcion del boton de copia de seguridad de la base de datos            
    def backup_base_datos(self):
        archivo = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL", "*.sql")])
        if not archivo:
            return
        
        mysqldump_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"  # Ruta completa para evitar modificar path
        
        # Verificar si el ejecutable existe
        if not os.path.isfile(mysqldump_path):
            messagebox.showerror("Error", f"No se encontró el ejecutable:\n{mysqldump_path}")
            return  
        
        try:
            comando = [
                mysqldump_path,
                "-h", "localhost",
                "-u", "root",
                f"-p{self.db_password}", # contraseña
                "bascula_silvotecnia"
            ]
            with open(archivo, "w", encoding="utf-8") as f:
                subprocess.run(comando, stdout=f, check=True)
            messagebox.showinfo("Éxito", f"Copia de seguridad creada:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la copia de seguridad.\n{e}")

    
    # Funcion del boton de Restauracion copia de seguridad de la base de datos
    def restaurar_base_datos(self):
        archivo = filedialog.askopenfilename(defaultextension=".sql", filetypes=[("SQL", "*.sql")])
        if not archivo:
            return
        
        mysql_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"  # Ruta completa para evitar modificar path
        
            
        # Verificar si el ejecutable existe
        if not os.path.isfile(mysql_path):
            messagebox.showerror("Error", f"No se encontró el ejecutable:\n{mysql_path}")
            return
                
        confirmacion = messagebox.askyesno(
            "Confirmar restauración",
            "⚠ Esto borrará todos los datos actuales y restaurará la copia.\n¿Continuar?"
        )
        if not confirmacion:
            return
        try:
            comando = [
                mysql_path,
                "-h", "localhost",
                "-u", "root",
                f"-p{self.db_password}",
                "bascula_silvotecnia"
            ]
            with open(archivo, "r", encoding="utf-8") as f:
                subprocess.run(comando, stdin=f, check=True)
            messagebox.showinfo("Éxito", "Base de datos restaurada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar la base de datos.\n{e}")
            



# === Punto de entrada principal, Ejecutar interfaz si se corre el script directamente ===
if __name__ == "__main__":
    root = tk.Tk()
    app = ReportesBasculaApp(root)
    root.mainloop()
