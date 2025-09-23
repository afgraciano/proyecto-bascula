# Contenido del archivo con funciones de integración
import mysql.connector
from datetime import datetime


def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="bascula2025",
        database="bascula_silvotecnia"
    )


# =======================
#  GESTIÓN DE USUARIOS
# =======================

def registrar_personal(nombre, login, password, cedula):
    
    """
    Registra un nuevo usuario autorizado en la tabla personal_autorizado.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO personal_autorizado (nombre, login, password, cedula)
        VALUES (%s, %s, %s, %s)
    """, (nombre, login, password, cedula))
    conexion.commit()
    conexion.close()
    #print(f" Usuario {nombre} registrado con éxito.")


def autenticar_usuario(login, password):
    
    """
    Valida login y contraseña. Retorna diccionario con datos del usuario si existe.
    """
    
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM personal_autorizado
        WHERE login=%s AND password=%s
    """, (login, password))
    usuario = cursor.fetchone()
    conexion.close()
    if usuario:
        #print(f" Usuario {usuario['nombre']} autenticado.")
        pass
    else:
        #print(" Login o contraseña incorrectos.")
        pass
    return usuario
   

# =======================
#  GESTIÓN DE EVENTOS
# =======================
def guardar_evento_desconexion(tipo, tiempo_desconexion=0, id_autorizado=None):
    
    """
    Guarda un evento de desconexión en la tabla 'desconexiones', incluyendo el tiempo de desconexión en segundos.
    """
    
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO desconexiones (fecha_hora, tipo_desconexion, descripcion, tiempo_desconexion, id_autorizado)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            tipo,
            f"Evento de desconexión detectado: {tipo}",
            tiempo_desconexion,
            id_autorizado
        ))
        conexion.commit()
        conexion.close()
        #print(" Evento de desconexión guardado con {tiempo_desconexion} segundos.")
    except Exception as e:
        #print(f" Error guardando desconexión: {e}")
        pass
        
        
# =======================
# GESTIÓN DE CLIENTES Y PESAJE
# =======================

def guardar_cliente_y_pesaje(tipo_cliente, datos_cliente, datos_pesaje, id_autorizado):
    
    """
    Guarda un cliente (según tipo) y un pesaje relacionado, ligado al usuario autorizado.
    """
    
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        if tipo_cliente == "tercero":
            cursor.execute("""
                INSERT INTO cliente_tercero (nombre, cedula_nit, correo_remision, id_ingresado)
                VALUES (%s, %s, %s, %s)
            """, (
                datos_cliente.get("nombre"),
                datos_cliente.get("cedula_nit"),
                datos_cliente.get("correo_remision"),
                datos_cliente.get("id_ingresado")
            ))
        elif tipo_cliente == "mensual":
            cursor.execute("""
                INSERT INTO cliente_mensual (tipo, nombre, nit, id_ingresado)
                VALUES (%s, %s, %s, %s)
            """, (
                datos_cliente.get("tipo"),
                datos_cliente.get("nombre"),
                datos_cliente.get("nit"),
                datos_cliente.get("id_ingresado")
            ))
        elif tipo_cliente == "interno":
            cursor.execute("""
                INSERT INTO cliente_interno (tipo, codigo_empresa, nombre, nit, id_ingresado)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                datos_cliente.get("tipo"),
                datos_cliente.get("codigo_empresa"),
                datos_cliente.get("nombre"),
                datos_cliente.get("nit"),
                datos_cliente.get("id_ingresado")
            ))
        else:
            raise ValueError("Tipo de cliente desconocido")

        id_cliente = cursor.lastrowid


        peso_bruto = datos_pesaje.get("peso_bruto")
        peso_tara = datos_pesaje.get("peso_tara")
        peso_neto = datos_pesaje.get("peso_neto")  # intenta usar el valor si ya existe

        if peso_neto is None and peso_bruto is not None and peso_tara is not None:
            peso_neto = abs(peso_bruto - peso_tara)
            

        cursor.execute("""
            INSERT INTO pesajes (
                fecha_hora, tipo_cliente, peso_bruto, peso_tara, peso_neto, placa, id_cliente, id_autorizado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            tipo_cliente,
            peso_bruto,
            peso_tara,
            peso_neto,
            datos_pesaje.get("placa"),
            id_cliente,
            id_autorizado
        ))

        conexion.commit()
        conexion.close()
        #print(" Cliente y pesaje guardados con peso_neto.")
    except Exception as e:
        #print(f" Error guardando cliente y pesaje: {e}")
        pass
