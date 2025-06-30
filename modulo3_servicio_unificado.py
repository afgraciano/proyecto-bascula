# Importación de módulos necesarios
import tkinter as tk  # Módulo principal para la GUI Para interfaces gráficas
from tkinter import simpledialog, messagebox  # Para cuadros de diálogo simples y mensajes emergentes
import socket  # Para la comunicación con el módulo que lee el peso (modulo1) Comunicación por red local (localhost)
import json  # Para interpretar los datos recibidos en formato JSON
from datetime import datetime  # Para Obtener y registrar fecha y hora
import re  # Validaciones con expresiones regulares
import unicodedata  # para permitir caracteres o validación de nombres acentuados

# Diccionario para almacenar pesos temporales de pesajes parciales (por ID)

# Se importan los diccionarios globales que almacenan pesajes abiertos y cerrados del archivo estado_pesajes.py
# para permitir el acceso y actualización compartida entre módulos (como módulo1 y módulo3)
from estado_pesajes import pesajes_temporales, pesajes_confirmados
import json
import os

#definio funcion para actualizar el estado del pesaje que se comparte con el modulo 1 y lo indico cada que agrego o elimino pesaje en pesajes_temporales
# 🔄 Guardar estado actual de pesajes en archivo JSON
def actualizar_estado_pesajes():
    ruta = os.path.join(os.path.dirname(__file__), 'estado_actual_pesajes.json')
    try:
        with open(ruta, 'w') as f:
            json.dump(pesajes_temporales, f, indent=2)
    except Exception as e:
        print(f"❌ Error al guardar estado de pesajes: {e}")

# 🔁 Cargar estado anterior desde archivo JSON (al iniciar)
def cargar_estado_pesajes():
    ruta = os.path.join(os.path.dirname(__file__), 'estado_actual_pesajes.json')
    try:
        with open(ruta, 'r') as f:
            datos = json.load(f)
            pesajes_temporales.update(datos)
    except Exception as e:
        print(f"⚠️ No se pudo restaurar estado de pesajes: {e}")

# 🟢 Llamar esta función cargar_estado_pesajes inmediatamente después de definirla
cargar_estado_pesajes()

# Función que se conecta al socket o modulo1 para obtener el peso actual y la hora desde modulo1
def obtener_datos_peso():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5000))  # Conecta al servidor en localhost, puerto 5000
            data = s.recv(1024)  # Recibe los datos (máx 1024 bytes)
            resultado = json.loads(data.decode())  # Decodifica el JSON recibido
            return resultado.get("peso", 0), resultado.get("timestamp", "")
    except:
        return 0, "" 
    
# Función para confirmar o permitir ingreso manual si el peso es bajo
def confirmar_o_pedir_peso(peso, ventana):
    if peso <= 10:
        decision = messagebox.askyesno(
            "Cierre con peso bajo",
            f"El peso actual es {peso:.2f} kg.\n¿Desea cerrar con este peso presione Si o ingresar un peso manual presione no?",
            parent=ventana
        )
        if not decision:
            # Permitir ingreso manual
            peso_manual = simpledialog.askstring("Peso cierre manual", "Ingrese el peso final (kg):", parent=ventana)
            if peso_manual and peso_manual.strip().isdigit():
                return int(peso_manual.strip())
            else:
                messagebox.showwarning("Cancelado", "No se ingresó peso válido. Operación cancelada.", parent=ventana)
                return None
    return peso
 # Si falla la conexión o algo sale mal, retorna 0 y cadena vacía

# Función principal que construye y ejecuta la ventana de servicio del módulo 3
def modulo_servicio():
    
    # Función que se ejecuta al hacer clic en uno de los botones de servicio
    def verificar_servicio(tipo):
        peso, _ = obtener_datos_peso()  # Obtiene el peso actual del socket

        # Si el tipo de servicio es externo con subtipos
        if tipo == "Externo":
            # Submenú para distinguir tipo de externo
            subtipos = {
                "Tercero (pago inmediato)": "Pago inmediato",
                "Cipreses de Colombia": "Pago mensual",
                "Núcleos de Madera": "Pago mensual",
                "Construinmuniza": "Pago mensual"
            }

            cliente = tk.StringVar(value="")

            # Selección del cliente externo
            subventana = tk.Toplevel(ventana)
            subventana.title("Seleccione Cliente Externo")
            subventana.geometry("300x200")
            subventana.attributes("-topmost", True)
            subventana.resizable(False, False)
            subventana.protocol("WM_DELETE_WINDOW", lambda: None)
            subventana.overrideredirect(True)

            marco = tk.Frame(subventana, bd=2, relief="ridge")
            marco.pack(expand=True, fill="both", padx=5, pady=5)

            tk.Label(marco, text="Seleccione el cliente externo:", font=("Arial", 11)).pack(pady=10)

            def seleccionar_cliente(nombre):
                cliente.set(nombre)
                subventana.destroy()

            for nombre in subtipos:
                tk.Button(marco, text=nombre, width=30, command=lambda n=nombre: seleccionar_cliente(n)).pack(pady=3)

            ventana.wait_window(subventana)
            if not cliente.get():
                return
            
            tipo_pago = subtipos[cliente.get()]  # Obtiene tipo de pago según cliente
            # comportamiento para Tercero (pago inmediato)
            if cliente.get() == "Tercero (pago inmediato)":

                # Paso 1:Solicita placa del vehículo (formato LLL111)
                while True:
                    placa = simpledialog.askstring("Placa", "Ingrese la placa del vehículo (Ej: ABC123):", parent=ventana)
                    if placa is None:
                        return
                    placa = placa.strip().upper()
                    if re.fullmatch(r'[A-Z]{3}\d{3}', placa):
                        break
                    messagebox.showerror("Inválido", "Formato de placa incorrecto. Ejemplo válido: ABC123", parent=ventana)
                
                # Paso 2: Remisión (opcional)
                remision = simpledialog.askstring("Remisión", "Ingrese remisión (opcional):", parent=ventana)
                remision = remision.strip().upper() if remision else ""
                # aqui concateno placa espacio remision en un id final
                id_final = f"{placa} {remision}".strip()
                # ingreso en variable clave el tipo y id final
                clave = f"{tipo}:{cliente.get()}:{id_final}"
                
                

                # 🔁 Si ya hay un pesaje iniciado, hacemos el cierre automáticamente
                if clave in pesajes_temporales:
                    peso_ini, fecha_ini, razon, nit, correo = pesajes_temporales[clave]
                    #hago llamada de la funcion confirmar o pedir peso
                    peso_confirmado = confirmar_o_pedir_peso(peso, ventana)
                    if peso_confirmado is None:
                        return
                    peso = peso_confirmado
                    # agrego fecha actual con hora, minutos y segundos del momento de inserccion del peso
                    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    peso_neto = abs(peso - peso_ini) #resta de los pesos y resultado simpre positivo
                    # Mensaje tiquete y resultado en pantalla
                    messagebox.showinfo("Pesaje cerrado",
                        f"Cliente: {razon}\n"
                        f"NIT: {nit}\n"
                        f"Correo: {correo}\n"
                        f"ID: {id_final}\n"
                        f"Peso Inicial: {peso_ini:.2f} kg — {fecha_ini}\n"
                        f"Peso Final: {peso:.2f} kg — {fecha_actual}\n"
                        f"Peso Neto: {peso_neto:.2f} kg", parent=ventana)
                    pesajes_confirmados.append((tipo, id_final, peso_ini, peso, fecha_ini, fecha_actual))
                    del pesajes_temporales[clave]
                    actualizar_estado_pesajes()  # actualiza pesaje eliminado de pesajes abiertos
                    return  # Salimos porque ya hicimos el cierre

                # 🔁 Si no hay pesaje previo, solicitamos los demás datos


                # Paso 3: funcion de Nombre o razón social (obligatorio y con validación)
                def es_valido_nombre_razon(texto):
                    # Permite letras (con o sin tilde), números, espacios y puntuación básica
                    return bool(re.fullmatch(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9 .,'&-]+", texto))

                while True:
                    razon = simpledialog.askstring("Nombre o Razón social", "Ingrese nombre completo o razón social:", parent=ventana)
                    if razon and razon.strip():
                        razon = razon.strip()
                        if not es_valido_nombre_razon(razon):
                            messagebox.showerror("Inválido", "El nombre solo debe contener letras, espacios, puntos, comas, apóstrofes o guiones.", parent=ventana)
                            continue
                        if razon.isupper():
                            break  # No tocamos, asumimos que es razón social en siglas
                        else:
                            # Capitaliza cada palabra (permite nombres con mayúsculas iniciales)
                            razon = ' '.join(p.capitalize() for p in razon.split())
                            break
                    else:
                        messagebox.showerror("Campo obligatorio", "Debe ingresar la razón social o nombre válido.", parent=ventana)

                # Paso 4: Cédula o NIT (solo números)
                while True:
                    nit = simpledialog.askstring("NIT o Cédula", "Ingrese NIT o Cédula (solo números):", parent=ventana)
                    if nit and nit.strip():
                        nit = nit.strip()
                        if nit.isdigit():
                            break
                        else:
                            messagebox.showerror("Inválido", "Solo se permiten números en la cédula o NIT.", parent=ventana)
                    else:
                        messagebox.showerror("Campo obligatorio", "Debe ingresar la cédula o NIT.", parent=ventana)

                # Paso 5: Correo electrónico (opcional y validado)
                def es_correo_valido(email):
                    return re.fullmatch(r"[\w\.-]+@[\w\.-]+\.(com|co|net|org|gov|edu(\.[a-z]{2})?|es|info|io|biz|us|mx|ar|cl|ec)", email, re.IGNORECASE)

                while True:
                    correo = simpledialog.askstring("Correo", "Ingrese correo electrónico (opcional):", parent=ventana)
                    if correo:
                        correo = correo.strip()
                        if es_correo_valido(correo):
                            break
                        else:
                            messagebox.showwarning("Correo inválido", "Formato de correo no válido. Ejemplo válido: usuario@dominio.com.co", parent=ventana)
                            continue  # volver a pedir
                    else:
                        correo = ""
                        break
                
                # Paso 6: Preguntar si tendrá cierre
                cerrar = messagebox.askyesno("Cierre", "¿Este servicio tendrá cierre de pesaje?", parent=ventana)
                
                if cerrar:
                    # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # 🔁 Se registra como pesaje inicial
                    pesajes_temporales[clave] = (peso, fecha_actual, razon, nit, correo)
                    messagebox.showinfo("Pesaje inicial",
                        f"Peso inicial registrado: {peso:.2f} kg\nID: {id_final}", parent=ventana)
                else:
                    # 🔁 Permitir ingresar peso de cierre manual
                    fecha_peso_inicial = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Toma fecha del peso leído Antes de pedir peso manual
                    peso_manual = simpledialog.askstring("Peso cierre manual", "Ingrese el peso de cierre manual (kg) o deje vacío si no hay peso final:", parent=ventana)

                    # Paso 7: Mensaje tiquete y resultado en pantalla,
                    if peso_manual and peso_manual.strip().isdigit():
                        peso_final = int(peso_manual.strip())
                        fecha_peso_final = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Después de confirmarlo y escribir peso final Toma fecha al cierre
                        peso_neto = abs(peso_final - peso)
                        # Mensaje tiquete y resultado en pantalla
                        messagebox.showinfo("Pesaje manual",
                            f"Cliente: {razon}\n"
                            f"NIT: {nit}\n"
                            f"Correo: {correo}\n"
                            f"ID: {id_final}\n"
                            f"Peso Inicial: {peso:.2f} kg — {fecha_peso_inicial}\n"
                            f"Peso Final: {peso_final:.2f} kg — {fecha_peso_final}\n"
                            f"Peso Neto: {peso_neto:.2f} kg", parent=ventana)
                        pesajes_confirmados.append((tipo, id_final, peso, peso_final, fecha_peso_inicial, fecha_peso_final))
                    else:
                        # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        #Solo muestra el peso actual si no se ingresó cierre manual
                        messagebox.showinfo("Pesaje registrado",
                            f"Cliente: {razon}\n"
                            f"NIT: {nit}\n"
                            f"Correo: {correo}\n"
                            f"ID: {id_final}\n"
                            f"Peso actual: {peso:.2f} kg\n"
                            f"Fecha: {fecha_actual}", parent=ventana)
                return  # Fin del flujo 
              

            # Lógica para externos con pago mensual (Cipreses, Núcleos, Construinmuniza)
            # Solicita placa (formato LLL111) y pregunta si habrá cierre de pesaje
            while True:
                placa = simpledialog.askstring("Placa", "Ingrese la placa del vehículo (Ej: ABC123):", parent=ventana)
                if placa is None:
                    return
                placa = placa.strip().upper()
                if re.fullmatch(r'[A-Z]{3}\d{3}', placa):
                    break
                messagebox.showerror("Inválido", "Formato de placa incorrecto. Ejemplo válido: ABC123", parent=ventana)
            
            # Remisión opcional para externos con pago mensual
            remision = simpledialog.askstring("Remisión", "Ingrese remisión (opcional):", parent=ventana)
            remision = remision.strip().upper() if remision else ""
            if remision:
                id_ingresado = f"{placa} {remision}"
            else:
                id_ingresado = placa

            
            clave = f"{tipo}:{cliente.get()}:{id_ingresado}"
            
            
            # Solo preguntamos si habrá cierre si NO hay un pesaje inicial guardado
            if clave in pesajes_temporales:
                cerrar = True  # Ya hay uno en curso, asumimos que se va a cerrar
            else:
                cerrar = messagebox.askyesno("Cierre", "¿Este servicio tendrá cierre de pesaje?", parent=ventana)

            if cerrar:
                ## agrego fecha actual con hora, minutos y segundos del momento de inserccion del peso
                #fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if clave in pesajes_temporales:
                    peso_ini, fecha_ini = pesajes_temporales[clave]
                    peso_confirmado = confirmar_o_pedir_peso(peso, ventana)
                    if peso_confirmado is None:
                        return
                    peso = peso_confirmado
                    
                    peso_neto = abs(peso - peso_ini)#resta de los pesos y resultado simpre positivo
                    # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Se muestra resultado en pantalla
                    messagebox.showinfo("Resultado",
                        f"Cliente: {cliente.get()}\n"
                        f"Placa: {id_ingresado}\n"
                        f"Peso Inicial: {peso_ini:.2f} kg — {fecha_ini}\n"
                        f"Peso Final: {peso:.2f} kg — {fecha_actual}\n"
                        f"Peso Neto: {peso_neto:.2f} kg\n"
                        f"Tipo de pago: {tipo_pago}", parent=ventana)
                    pesajes_confirmados.append((tipo, id_ingresado, peso_ini, peso, fecha_ini, fecha_actual))
                    del pesajes_temporales[clave]
                    actualizar_estado_pesajes()  # actualiza la eliminacion de pesajes abiertos
                else:
                    # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    pesajes_temporales[clave] = (peso, fecha_actual)
                    actualizar_estado_pesajes()  # actualiza agregar pesajes abiertos
                    messagebox.showinfo("Pesaje inicial",
                        f"Peso inicial registrado: {peso:.2f} kg\nPlaca: {id_ingresado}", parent=ventana)
            else:
                # Permite ingresar peso de cierre manual
                fecha_peso_inicial = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Toma fecha del peso leído
                peso_manual = simpledialog.askstring("Peso cierre manual", "Ingrese el peso de cierre manual (kg) o deje vacío:", parent=ventana)
                if peso_manual and peso_manual.isdigit():
                    fecha_peso_final = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Toma fecha al confirmar el cierre
                    peso_final = int(peso_manual)
                    peso_neto = abs(peso_final - peso)
                    # Mensaje tiquete y resultado en pantalla
                    messagebox.showinfo("Pesaje manual",
                        f"Cliente: {cliente.get()}\n"
                        f"Placa: {id_ingresado}\n"
                        f"Peso Inicial: {peso:.2f} kg — {fecha_peso_inicial}\n"
                        f"Peso Final: {peso_final:.2f} kg — {fecha_peso_final}\n"
                        f"Peso Neto: {peso_neto:.2f} kg\n"
                        f"Tipo de pago: {tipo_pago}", parent=ventana)
                else:
                    # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    messagebox.showinfo("Pesaje registrado",
                        f"Cliente: {cliente.get()}\nPlaca: {id_ingresado}\nPeso actual: {peso:.2f} kg\nFecha: {fecha_actual}\nTipo de pago: {tipo_pago}", parent=ventana)

        # Si es Inmuniza o Aserrio, se necesita un ID y se hace lógica de pesaje doble
        elif tipo in ["Inmuniza", "Aserrio"]:
            # Paso 1: Ingresar placa del vehículo (formato válido: 3 letras + 3 números)
            while True:
                placa = simpledialog.askstring("Placa", "Ingrese la placa del vehículo (Ej: LLL111):", parent=ventana)

                if placa is None:
                    # El usuario presionó "Cancelar" → salir y no continuar con el flujo de este tipo
                    return

                if placa.strip() == "":
                    # El usuario presionó "Aceptar" sin escribir → mostrar advertencia
                    messagebox.showwarning("Campo obligatorio", "Debe ingresar una placa para continuar.", parent=ventana)
                    continue

                placa = placa.upper()
                if re.fullmatch(r'[A-Z]{3}\d{3}', placa):
                    break  # ✅ Formato válido
                else:
                    # ❌ Formato incorrecto: mostrar error
                    messagebox.showerror(
                        "Formato inválido",
                        "La placa debe tener 3 letras seguidas de 3 números.\n"
                        "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n\nEjemplo válido: LLL111",
                        parent=ventana
                    )


            # Paso 2: Seleccionar RG o MS como empresa
            empresa = tk.StringVar(value="")  # No hay valor por defecto aún

            subventana = tk.Toplevel(ventana)
            subventana.title("Seleccione Empresa")
            subventana.geometry("250x130")
            subventana.attributes("-topmost", True)
            subventana.resizable(False, False)
            subventana.focus_force()

            # Eliminar botones del sistema (cierra y minimiza)
            subventana.protocol("WM_DELETE_WINDOW", lambda: None)
            subventana.overrideredirect(True)  # ❌ Oculta bordes y botones (incluyendo minimizar)

            # Fondo con borde simulado (opcional si se usa overrideredirect)
            marco = tk.Frame(subventana, bd=2, relief="ridge")
            marco.pack(expand=True, fill="both", padx=5, pady=5)

            tk.Label(marco, text="Seleccione la empresa:", font=("Arial", 11)).pack(pady=10)

            # Función para selección
            def seleccionar_empresa(valor):
                empresa.set(valor)
                subventana.destroy()

            # Botones
            tk.Button(marco, text="RG", width=10, command=lambda: seleccionar_empresa("RG")).pack(pady=5)
            tk.Button(marco, text="MS", width=10, command=lambda: seleccionar_empresa("MS")).pack(pady=5)

            # Espera hasta selección
            ventana.wait_window(subventana)

            # Cancelar si no se seleccionó nada
            if not empresa.get():
                return



            # Paso 3: Ingresar número de remisión (solo dígitos)
            while True:
                remision = simpledialog.askstring("Remisión", "Ingrese el número de remisión (solo números):", parent=ventana)
                if remision is None:
                    return
                if remision.isdigit():
                    break
                else:
                    messagebox.showerror("Inválido", "La remisión debe contener solo números.", parent=ventana)

            # Construir el ID final
            id_ingresado = f"{placa} {empresa.get()}{remision}".upper()
            clave = f"{tipo}:{id_ingresado}"
            
            
            # Verificamos Si ya hay un pesaje abierto con esta clave, cerrar directamente sin volver a preguntar
            if clave in pesajes_temporales:
                peso_inicial, fecha_inicial = pesajes_temporales[clave]  # Recupera datos
                peso_confirmado = confirmar_o_pedir_peso(peso, ventana)
                if peso_confirmado is None:
                    return
                peso = peso_confirmado
                
                peso_neto = abs(peso - peso_inicial)  # Calcula el peso neto

                # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Mensaje tiquete y resultado en pantalla
                messagebox.showinfo("Resultado",
                    f"Pesaje final registrado.\n"
                    f"{tipo}:\nID: {id_ingresado}\n"
                    f"Peso Inicial: {peso_inicial:.2f} kg — {fecha_inicial}\n"
                    f"Peso Final: {peso:.2f} kg — {fecha_actual}\n"
                    f"Peso Neto: {peso_neto:.2f} kg", parent=ventana)
                pesajes_confirmados.append((tipo, id_ingresado, peso_inicial, peso, fecha_inicial, fecha_actual))
                del pesajes_temporales[clave]  # Elimina de pesajes abiertos
                actualizar_estado_pesajes()  # actualiza la Eliminacion de pesajes abiertos
                return  # Finaliza la ejecución

            # Paso 4: Preguntar si tendrá cierre (solo si no hay pesaje previo abierto)
            cerrar = messagebox.askyesno("Cierre", "¿Este servicio tendrá cierre de pesaje?", parent=ventana)

            # Si el servicio tendrá cierre de pesaje
            if cerrar:
                # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                pesajes_temporales[clave] = (peso, fecha_actual)  # Registra pesaje inicial
                actualizar_estado_pesajes()  # actualizo inicio de pesajes abiertos
                messagebox.showinfo("Pesaje inicial",
                    f"Peso inicial registrado: {peso:.2f} kg\nID: {id_ingresado}", parent=ventana)
            else:
                # Si NO tendrá cierre: se permite cierre manual
                fecha_peso_inicial = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Fecha inicial
                peso_manual = simpledialog.askstring("Peso cierre manual", "Ingrese el peso de cierre manual (kg) o deje vacío si no hay peso final:", parent=ventana)
                if peso_manual and peso_manual.strip().isdigit():
                    peso_final = int(peso_manual.strip())  # Convierte a entero
                    fecha_peso_final = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Fecha final
                    peso_neto = abs(peso_final - peso)  # Calcula neto
                    # Mensaje tiquete y resultado en pantalla
                    messagebox.showinfo("Pesaje manual",
                        f"{tipo}:\nID: {id_ingresado}\n"
                        f"Peso Inicial: {peso:.2f} kg — {fecha_peso_inicial}\n"
                        f"Peso Final: {peso_final:.2f} kg — {fecha_peso_final}\n"
                        f"Peso Neto: {peso_neto:.2f} kg", parent=ventana)
                    pesajes_confirmados.append((tipo, id_ingresado, peso, peso_final, fecha_peso_inicial, fecha_peso_final))
                else:
                    # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
                    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Si no se ingresó peso final manual, solo muestra registro actual
                    messagebox.showinfo("Pesaje registrado",
                        f"{tipo}:\nID: {id_ingresado}\nPeso actual: {peso:.2f} kg\nFecha: {fecha_actual}", parent=ventana)


        # Solicita los mismos datos que Inmuniza/Aserrio, pero solo imprime peso actual para Astillable
        elif tipo == "Astillable":
            # Paso 1: Ingresar placa del vehículo (formato válido: 3 letras + 3 números)
            while True:
                placa = simpledialog.askstring("Placa", "Ingrese la placa del vehículo (Ej: LLL111):", parent=ventana)
                if placa is None:
                    # El usuario presionó "Cancelar" → salir y no continuar con el flujo de este tipo
                    return
                if placa.strip() == "":
                    # El usuario presionó "Aceptar" sin escribir → mostrar advertencia
                    messagebox.showwarning("Campo obligatorio", "Debe ingresar una placa.", parent=ventana)
                    continue
                placa = placa.upper()
                if re.fullmatch(r'[A-Z]{3}\d{3}', placa):
                    break# ✅ Formato válido
                else:
                    # ❌ Formato incorrecto: mostrar error
                    messagebox.showerror(
                        "Formato inválido",
                        "La placa debe tener 3 letras seguidas de 3 números.\n"
                        "No se permiten letras en la parte numérica ni numeros en la parte de letras.\n\nEjemplo válido: LLL111",
                        parent=ventana
                    )
            # Paso 2: Seleccionar RG o MS como empresa      
            empresa = tk.StringVar(value="")  # No hay valor por defecto aún

            subventana = tk.Toplevel(ventana)
            subventana.title("Seleccione Empresa")
            subventana.geometry("250x130")
            subventana.attributes("-topmost", True)
            subventana.resizable(False, False)
            
            # Eliminar botones del sistema (cierra y minimiza)
            subventana.protocol("WM_DELETE_WINDOW", lambda: None)
            subventana.overrideredirect(True)  # ❌ Oculta bordes y botones (incluyendo minimizar)

            # Fondo con borde simulado (opcional si se usa overrideredirect)
            marco = tk.Frame(subventana, bd=2, relief="ridge")
            marco.pack(expand=True, fill="both", padx=5, pady=5)

            tk.Label(marco, text="Seleccione la empresa:", font=("Arial", 11)).pack(pady=10)
            
            # Función para selección
            def seleccionar_empresa(valor):
                empresa.set(valor)
                subventana.destroy()

            # Botones
            tk.Button(marco, text="RG", width=10, command=lambda: seleccionar_empresa("RG")).pack(pady=5)
            tk.Button(marco, text="MS", width=10, command=lambda: seleccionar_empresa("MS")).pack(pady=5)
            
            # Espera hasta selección
            ventana.wait_window(subventana)

            # Cancelar si no se seleccionó nada
            if not empresa.get():
                return

            
            # Paso 3: Ingresar número de remisión (solo dígitos)
            while True:
                remision = simpledialog.askstring("Remisión", "Ingrese el número de remisión (solo números):", parent=ventana)
                if remision is None:
                    return
                if remision.isdigit():
                    break
                else:
                    messagebox.showerror("Inválido", "La remisión debe contener solo números.", parent=ventana)

            
            # Construir el ID final
            id_ingresado = f"{placa} {empresa.get()}{remision}".upper()
            # defino fecha actual con hora, minutos y segundos del momento de inserccion del peso
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Mensaje resultado final impreso en pantalla de astillable
            messagebox.showinfo("Resultado",
                f"Pesaje final registrado.\n"
                f"{tipo}:\n ID: {id_ingresado}\n"
                f"Peso: {peso:.2f} kg\nFecha: {fecha_actual}", parent=ventana)

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

    tipos = ["Externo", "Inmuniza", "Aserrio", "Astillable"]
    for tipo in tipos:
        tk.Button(frame_botones, text=tipo, width=15, font=("Arial", 11),
                  command=lambda t=tipo: verificar_servicio(t)).pack(side="left", padx=5)

    ventana.mainloop()  # Inicia el bucle principal de la ventana (la mantiene abierta)

# Si el archivo se ejecuta directamente, se lanza la función de servicio
if __name__ == "__main__":
    import signal
    import sys

    def cerrar_gracioso(sig, frame):
        print("🔴 Señal de terminación recibida. Cerrando ventana de báscula...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, cerrar_gracioso)
    signal.signal(signal.SIGINT, cerrar_gracioso)  # Ctrl+C, por si acaso

    try:
        modulo_servicio()
    except Exception as e:
        print(f"⛔ módulo3 cerrado por excepción: {e}")
