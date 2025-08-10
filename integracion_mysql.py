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

def guardar_evento_desconexion(tipo):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO desconexiones (fecha_hora, tipo_desconexion, descripcion)
            VALUES (%s, %s, %s)
        """, (
            datetime.now(),
            tipo,
            f"Evento de desconexión detectado: {tipo}"
        ))
        conexion.commit()
        conexion.close()
        print("✅ Evento de desconexión guardado.")
    except Exception as e:
        print(f"❌ Error guardando desconexión: {e}")

def guardar_cliente_y_pesaje(tipo_cliente, datos_cliente, datos_pesaje):
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
        #peso_neto = None
        peso_neto = datos_pesaje.get("peso_neto")  # intenta usar el valor si ya existe

        if peso_neto is None and peso_bruto is not None and peso_tara is not None:
        #if peso_bruto is not None and peso_tara is not None:
            peso_neto = abs(peso_bruto - peso_tara)
            

        cursor.execute("""
            INSERT INTO pesajes (
                fecha_hora, tipo_cliente, peso_bruto, peso_tara, peso_neto, placa, id_cliente
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            tipo_cliente,
            peso_bruto,
            peso_tara,
            peso_neto,
            datos_pesaje.get("placa"),
            id_cliente
        ))

        conexion.commit()
        conexion.close()
        print("✅ Cliente y pesaje guardados con peso_neto.")
    except Exception as e:
        print(f"❌ Error guardando cliente y pesaje: {e}")
