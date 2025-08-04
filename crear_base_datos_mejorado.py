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
    cedula_nit VARCHAR(20),
    correo_remision VARCHAR(100)
)
''')

# Tabla cliente mensual
cursor.execute('''
CREATE TABLE IF NOT EXISTS cliente_mensual (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    empresa VARCHAR(100),
    clave_placa_remision VARCHAR(50)
)
''')

# Tabla cliente interno
cursor.execute('''
CREATE TABLE IF NOT EXISTS cliente_interno (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    datos_adicionales TEXT
)
''')

# Tabla de desconexiones
cursor.execute('''
CREATE TABLE IF NOT EXISTS desconexiones (
    id_desconexion INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,
    tipo_desconexion VARCHAR(50),
    descripcion TEXT
)
''')

conexion.commit()
conexion.close()
print("✅ Todas las tablas fueron creadas correctamente.")
