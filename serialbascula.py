import serial
import pyodbc
from datetime import datetime

# Configura el puerto serial según tu sistema
ser = serial.Serial('COM3', 9600, timeout=1)

# Ruta completa a tu archivo Access .accdb
access_db_path = r"C:\ruta\a\tu_base.accdb"

# Cadena de conexión ODBC para Access
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={access_db_path};'
)

# Conectarse a Access
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("Leyendo datos del puerto serial y guardando en Access...")

try:
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            peso = line
            fecha_hora = datetime.now()

            print(f"Peso leído: {peso} kg")

            # Inserta en la tabla Access
            cursor.execute("INSERT INTO Pesajes (peso, fecha_hora) VALUES (?, ?)", peso, fecha_hora)
            conn.commit()

except KeyboardInterrupt:
    print("Programa detenido por el usuario.")

finally:
    cursor.close()
    conn.close()
    ser.close()
