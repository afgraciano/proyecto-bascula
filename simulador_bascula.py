# simulador_bascula.py
import serial
import time
import random

# Puerto COM virtual que emula la báscula
puerto_salida = 'COM3'  # Debe ser uno del par creado con com0com

ser = serial.Serial(puerto_salida, 9600)

try:
    while True:
        peso = round(random.uniform(10.0, 100.0), 2)
        ser.write(f"{peso}\r\n".encode('utf-8'))
        time.sleep(0.25)  # Cada 250 ms, como la báscula real
except KeyboardInterrupt:
    ser.close()



# simulador_bascula.py
import serial
import time
import random

# Abre el puerto COM6 (emisor virtual)
ser = serial.Serial('COM6', 9600)

try:
    while True:
        peso = round(random.uniform(10.0, 100.0), 2)  # Simula peso entre 10 y 100 kg
        ser.write(f"{peso}\n".encode('utf-8'))        # Envía como si fuera la báscula
        print(f"Enviado: {peso}")
        time.sleep(0.25)  # Enviar 4 veces por segundo
except KeyboardInterrupt:
    ser.close()
    print("Simulación terminada.")
