# test_com0com.py
import serial
import time
import threading

# Escribe datos de prueba en COM6
def escribir_en_com6():
    try:
        with serial.Serial('COM6', 9600, timeout=1) as ser_out:
            for i in range(5):
                mensaje = f"Prueba {i+1}"
                print(f"[COM6 -> COM7] Enviando: {mensaje}")
                ser_out.write((mensaje + '\r\n').encode('utf-8'))
                time.sleep(1)
    except Exception as e:
        print(f"Error al escribir en COM6: {e}")

# Lee datos desde COM7
def leer_en_com7():
    try:
        with serial.Serial('COM7', 9600, timeout=2) as ser_in:
            for _ in range(5):
                recibido = ser_in.readline().decode('utf-8').strip()
                if recibido:
                    print(f"[COM7] Recibido: {recibido}")
    except Exception as e:
        print(f"Error al leer en COM7: {e}")

# Ejecutar ambas funciones en paralelo
t1 = threading.Thread(target=escribir_en_com6)
t2 = threading.Thread(target=leer_en_com7)

t1.start()
t2.start()

t1.join()
t2.join()
