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
    
    #funcion para seleccionar fechas en calendario
    def seleccionar_fecha(self, entry_widget):
        top = tk.Toplevel(self.root)
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
        
        self.db_password = "bascula2025"  # guardo la contraseña de MySQL dentro de la clase para ser usada
        
        self.root = root
        self.root.title("Consulta y Reportes - Báscula")
        self.root.geometry("1100x650")  # Tamaño inicial de ventana
        #desde aqui hubico la ventana en la mitad de la pantalla
        # Tamaño inicial
        ancho_ventana = 1100
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

        # === Botones de exportación de resultados===
        #btn_frame = ttk.Frame(root)
        #btn_frame.pack(pady=5)
        
        
        #ttk.Button(btn_frame, text="Exportar a Excel", command=self.exportar_excel).pack(side="left", padx=5)
        #ttk.Button(btn_frame, text="Exportar a Access", command=self.exportar_access).pack(side="left", padx=5)
        #ttk.Button(btn_frame, text="Exportar a PDF", command=self.exportar_pdf).pack(side="left", padx=5)
        
        
        # === Botones de exportación y respaldo ===
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", pady=5)  # aquí solo colocamos el frame con pack

        # Exportar
        ttk.Button(btn_frame, text="Exportar a Excel", command=self.exportar_excel).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Exportar a Access", command=self.exportar_access).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=2, padx=5, pady=5)

        # Espacio vacío para empujar los de respaldo
        btn_frame.grid_columnconfigure(3, weight=1)
        
        # Botones de copia de seguridad y restauracion
        

        #ttk.Button(btn_frame, text="Copia de seguridad", command=self.backup_base_datos).pack(side="right", padx=5)
        #ttk.Button(btn_frame, text="Restaurar Copia Seguridad", command=self.restaurar_base_datos).pack(side="right", padx=5)
        
        # Botón copia de seguridad (misma columna que Consultar, fila siguiente)
        ttk.Button(btn_frame, text="Copia de seguridad", command=self.backup_base_datos).grid(row=0, column=3, padx=5, pady=5)

        # Botón restaurar copia (misma columna que Consultar, fila siguiente)
        ttk.Button(btn_frame, text="Restaurar Copia Seguridad", command=self.restaurar_base_datos).grid(row=0, column=5, padx=5, pady=5, sticky="ew")


        #ttk.Button(btn_frame, text="Copia de seguridad", command=self.backup_base_datos).grid(row=0, column=5, padx=5)
        #ttk.Button(btn_frame, text="Restaurar Copia Seguridad", command=self.restaurar_base_datos).grid(row=0, column=6, padx=5)


        self.datos_actuales = []  # Aquí se guardan los datos cargados


     
    
    #funcion para ajustar las columnas
    def autoajustar_columnas(self):
        for col in self.tree["columns"]:
            max_len = max([len(str(self.tree.set(k, col))) for k in self.tree.get_children()] + [len(col)])
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

        # Conexión a MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="bascula2025",
            database="bascula_silvotecnia"
        )
        cursor = conn.cursor(dictionary=True)

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
                    SELECT p.id_pesaje, t.id_ingresado, p.fecha_hora, p.tipo_cliente, p.peso_bruto,
                        p.peso_tara, p.peso_neto, p.placa,
                        t.nombre, t.cedula_nit, t.correo_remision
                    FROM pesajes p
                    LEFT JOIN cliente_tercero t ON p.id_cliente = t.id_cliente
                    WHERE p.fecha_hora BETWEEN %s AND %s
                """
            # Si el filtro es "mensual" -> hacemos JOIN con cliente_mensual
            elif tipo_cliente == "mensual":
                # Seleccionamos los campos del pesaje y de la tabla cliente_mensual.
                # Alias m.nit AS cedula_nit se usa para normalizar el nombre de columna (para que el resto del código lo vea igual).
                consulta = """
                    SELECT p.id_pesaje, m.id_ingresado, p.fecha_hora, p.tipo_cliente, p.peso_bruto,
                        p.peso_tara, p.peso_neto, p.placa,
                        m.nombre, m.nit AS cedula_nit, NULL AS correo_remision
                    FROM pesajes p
                    LEFT JOIN cliente_mensual m ON p.id_cliente = m.id_cliente
                    WHERE p.fecha_hora BETWEEN %s AND %s
                """
            # Si el filtro es "interno" -> hacemos JOIN con cliente_interno
            elif tipo_cliente == "interno":
                # Seleccionamos los campos del pesaje y de cliente_interno.
                # Como cliente_interno no tiene campo 'correo_remision', devolvemos NULL AS correo_remision
                # y renombramos i.nit como cedula_nit para coherencia con la interfaz.
                consulta = """
                    SELECT p.id_pesaje, i.id_ingresado, p.fecha_hora, i.tipo AS tipo_cliente, p.peso_bruto,
                        p.peso_tara, p.peso_neto, p.placa,
                        i.nombre, i.nit AS cedula_nit, NULL AS correo_remision
                    FROM pesajes p
                    LEFT JOIN cliente_interno i ON p.id_cliente = i.id_cliente
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
                        COALESCE(
                            CASE WHEN p.tipo_cliente = 'interno' THEN i.tipo ELSE NULL END,
                            p.tipo_cliente
                        ) AS tipo_cliente,
                        p.peso_bruto, p.peso_tara, p.peso_neto, p.placa,
                        COALESCE(t.nombre, m.nombre, i.nombre) AS nombre,
                        COALESCE(t.cedula_nit, m.nit, i.nit) AS cedula_nit,
                        COALESCE(t.correo_remision, NULL, NULL) AS correo_remision
                    FROM pesajes p
                    LEFT JOIN cliente_tercero t ON (p.tipo_cliente = 'tercero' AND p.id_cliente = t.id_cliente)
                    LEFT JOIN cliente_mensual m ON (p.tipo_cliente = 'mensual' AND p.id_cliente = m.id_cliente)
                    LEFT JOIN cliente_interno i ON (p.tipo_cliente = 'interno' AND p.id_cliente = i.id_cliente)
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
                    # Cuando es "Todos" debemos comparar contra el NIT que puede venir de cualquiera de las tres tablas,
                    # por eso usamos COALESCE(t.cedula_nit, m.nit, i.nit) que devuelve el primero no NULL.
                    # También permitimos filtrar por p.tipo_cliente.
                    consulta += " AND (p.placa LIKE %s OR COALESCE(t.cedula_nit, m.nit, i.nit) LIKE %s OR p.tipo_cliente LIKE %s)"
                    # Añadimos 3 parámetros en el mismo orden de los %s del string.
                    valores.extend([f"%{filtro_valor}%"] * 3)

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

        try:
            # Crear nueva conexión para insertar datos
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()

            columnas = ", ".join([f"[{col}] TEXT" for col in df.columns])
            cursor.execute(f"CREATE TABLE {tabla} ({columnas})")

            for _, row in df.iterrows():
                placeholders = ", ".join(["?" for _ in row])
                cursor.execute(f"INSERT INTO {tabla} VALUES ({placeholders})", tuple(str(v) for v in row))

            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Exportado a Access: {archivo}")

        except pyodbc.Error as e:
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
            pdf.set_font("Arial", size=7)    
            
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