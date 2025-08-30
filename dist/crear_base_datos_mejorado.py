# Contenido del script para crear múltiples tablas
import mysql.connector

conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="bascula2025"
)

cursor = conexion.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS bascula_silvotecnia")
print("✅ Base de datos 'bascula_silvotecnia' creada.")

conexion.database = "bascula_silvotecnia"

# Tabla pesajes
cursor.execute('''
CREATE TABLE IF NOT EXISTS pesajes (
    id_pesaje INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,
    tipo_cliente VARCHAR(20),
    peso_bruto DECIMAL(10,2),
    peso_tara DECIMAL(10,2),
    peso_neto DECIMAL(10,2),
    placa VARCHAR(20),
    id_cliente INT
)
''')

# Tabla cliente externo tercero
cursor.execute('''
CREATE TABLE IF NOT EXISTS cliente_tercero (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    cedula_nit VARCHAR(50),
    correo_remision VARCHAR(100),
    id_ingresado VARCHAR(100) -- placa + espacio + empresa + número de remisión
)
''')

# Tabla cliente mensual
cursor.execute('''
CREATE TABLE IF NOT EXISTS cliente_mensual (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    tipo varchar(100),        -- aqui 
    nombre VARCHAR(100),       -- nombre de la empresa
    nit VARCHAR(50),        -- NIT de la empresa
    id_ingresado VARCHAR(100) -- placa + espacio + empresa + número de remisión
)
''')

# Tabla cliente interno
cursor.execute('''
CREATE TABLE IF NOT EXISTS cliente_interno (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    tipo varchar(100),        -- aqui defino si es aserrio, inmuniza o astillable
    codigo_empresa VARCHAR(5), -- 'RG' o 'MS' para identificar la empresa
    nombre VARCHAR(100),       -- nombre de la empresa (p.ej. Reforestadora El Guásimo S.A.S)
    nit VARCHAR(50),          -- NIT de la empresa
    id_ingresado VARCHAR(100) -- placa + espacio + empresa + número de remisión
)
''')

# Tabla de desconexiones
cursor.execute('''
CREATE TABLE IF NOT EXISTS desconexiones (
    id_desconexion INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,
    tipo_desconexion VARCHAR(50),
    descripcion VARCHAR(100)
    
)
''')


# Tabla personal autorizado
cursor.execute('''
CREATE TABLE IF NOT EXISTS personal_autorizado (
    id_autorizado INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    login VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(20) NOT NULL,
    cedula VARCHAR(20) NOT NULL,
    CHECK (CHAR_LENGTH(password) BETWEEN 4 AND 20)
)
''')

# Verificar si la columna id_autorizado ya existe en pesajes
cursor.execute("SHOW COLUMNS FROM pesajes LIKE 'id_autorizado'")
columna = cursor.fetchone()

if not columna:
    cursor.execute('''
    ALTER TABLE pesajes
    ADD COLUMN id_autorizado INT,
    ADD CONSTRAINT fk_autorizado FOREIGN KEY (id_autorizado) REFERENCES personal_autorizado(id_autorizado)
    ''')
    print("✅ Columna id_autorizado agregada a la tabla pesajes.")
else:
    print("ℹ️ La columna id_autorizado ya existe en pesajes.")
    
    
conexion.commit()
conexion.close()
print("✅ Todas las tablas fueron creadas correctamente.")
