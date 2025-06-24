# Importación de módulos necesarios
import tkinter as tk  # Módulo principal para la GUI
from tkinter import simpledialog, messagebox  # Para cuadros de diálogo simples y mensajes emergentes
import socket  # Para la comunicación con el módulo que lee el peso (modulo1)
import json  # Para interpretar los datos recibidos en formato JSON
from datetime import datetime  # Para registrar fecha y hora

# Diccionario para almacenar pesos temporales de pesajes parciales (por ID)
pesajes_temporales = {}  # Guarda pesajes en curso por tipo:ID
pesajes_confirmados = []  # Guarda pesajes finalizados como tuplas (tipo, ID, peso_inicial, peso_final, fecha_ini, fecha_fin)

# Función que se conecta al socket para obtener el peso actual y la hora desde modulo1
def obtener_datos_peso():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5000))  # Conecta al servidor en localhost, puerto 5000
            data = s.recv(1024)  # Recibe los datos (máx 1024 bytes)
            resultado = json.loads(data.decode())  # Decodifica el JSON recibido
            return resultado.get("peso", 0), resultado.get("timestamp", "")
    except:
        return 0, ""  # Si falla la conexión o algo sale mal, retorna 0 y cadena vacía

# Función principal que construye y ejecuta la ventana de servicio
def modulo_servicio():
    
    # Función que se ejecuta al hacer clic en uno de los botones de servicio
    def verificar_servicio(tipo):
        peso, _ = obtener_datos_peso()  # Obtiene el peso actual del socket

        # Si el tipo de servicio es externo, solo se muestra un mensaje
        if tipo == "Externo":
            messagebox.showinfo("Servicio", f"Pesaje externo detectado: {peso:.2f} kg", parent=ventana)

        # Si es Inmuniza o Aserrio, se necesita un ID y se hace lógica de pesaje doble
        elif tipo in ["Inmuniza", "Aserrio"]:
            id_ingresado = simpledialog.askstring("ID", "Ingrese el ID del pesaje:", parent=ventana)  # Pide el ID
            if not id_ingresado:
                return  # Si no se ingresa nada, se cancela la operación
            id_ingresado = id_ingresado.upper()  # convierte todo a mayúsculas
            clave = f"{tipo}:{id_ingresado}"  #  necesario para poder usar clave correctamente
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Fecha y hora actual

            if clave in pesajes_temporales:
                # Si ya hay un peso inicial registrado para ese ID
                peso_inicial, fecha_inicial = pesajes_temporales[clave]
                peso_neto = abs(peso - peso_inicial)  # Se calcula el peso neto y Asegura que el peso neto sea siempre positivo
                messagebox.showinfo("Resultado",
                    f"Pesaje final registrado.\nID: {id_ingresado}\nPeso Neto: {peso_neto:.2f} kg\nInicio: {fecha_inicial}\nFin: {fecha_actual}")
                pesajes_confirmados.append((tipo, id_ingresado, peso_inicial, peso, fecha_inicial, fecha_actual))
                del pesajes_temporales[clave]  # Elimina el registro temporal
            else:
                # Si es el primer pesaje de ese ID, lo guarda
                pesajes_temporales[clave] = (peso, fecha_actual)
                messagebox.showinfo("Pesaje inicial",
                    f"Peso inicial registrado: {peso:.2f} kg\nID: {id_ingresado}")

        else:
            # Si es "Astillero", simplemente muestra el peso actual
            messagebox.showinfo("Astillero", f"Peso actual mostrado: {peso:.2f} kg", parent=ventana)

    # Función que actualiza constantemente el peso en la GUI
    def actualizar_peso_gui():
        peso, hora = obtener_datos_peso()  # Obtiene los datos actuales
        peso_label.config(text=f"{peso:.2f} kg")  # Actualiza la etiqueta del peso
        hora_label.config(text=hora)  # Actualiza la hora debajo
        ventana.after(500, actualizar_peso_gui)  # Repite cada 500 ms (0.5 s)

    # Creación de la ventana principal
    ventana = tk.Tk()

    # Función que se ejecuta al cerrar la ventana principal
    def al_cerrar():
        print("📌 Sesión de pesajes confirmados:")
        for tipo, id_, p_ini, p_fin, f_ini, f_fin in pesajes_confirmados:
            print(f"→ Tipo: {tipo}, ID: {id_}, Peso Neto: {p_fin - p_ini:.2f} kg, De: {f_ini} a {f_fin}")
        ventana.destroy()  # Cierra la ventana completamente

    ventana.protocol("WM_DELETE_WINDOW", al_cerrar)  # Asocia el cierre de ventana al manejo manual
    ventana.title("Servicio de Báscula")  # Título de la ventana
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

    frame_botones = tk.Frame(ventana)  # Contenedor horizontal de botones
    frame_botones.pack(pady=5)

    tipos = ["Externo", "Inmuniza", "Aserrio", "Astillero"]
    for tipo in tipos:
        tk.Button(frame_botones, text=tipo, width=15, font=("Arial", 11),
                  command=lambda t=tipo: verificar_servicio(t)).pack(side="left", padx=5)

    ventana.mainloop()  # Inicia el bucle principal de la ventana (la mantiene abierta)

# Si el archivo se ejecuta directamente, se lanza la función de servicio
if __name__ == "__main__":
    modulo_servicio()
