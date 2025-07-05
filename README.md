
# Sistema Automatizado de Pesaje para Vehículos en Silvotecnia S.A.S.

**Autor**: Andrés Felipe Graciano Monsalve  
**Práctica empresarial – Universidad de Antioquia, 2025-1**

---

## 📌 Descripción general

Este repositorio contiene el desarrollo de un sistema automatizado para el registro y control de pesajes industriales de vehículos transportadores de madera, implementado en la empresa **Silvotecnia S.A.S.**, especializada en silvicultura y manejo forestal sostenible.

El sistema permite capturar el peso inicial y final de los vehículos conectando una báscula industrial al computador mediante el puerto serial (COM), con soporte para simulación de hardware, autenticación de usuarios, trazabilidad y almacenamiento seguro de la información.

---

## ⚙️ Componentes del sistema

### 1. 🧪 Simulador de Báscula (`simulador_bascula.py`)
- Simula el comportamiento de una báscula industrial, enviando datos de peso de forma continua por un puerto COM virtual.
- Útil para pruebas sin necesidad de hardware físico.
- Compatible con **com0com** y herramientas de desarrollo serial.

### 2. 🔍 Sensor / Lector de Báscula (`serialbascula.py`)
- Lee continuamente los datos desde un puerto COM.
- Incluye validaciones, formateo de datos y alertas ante desconexiones o errores de lectura.
- Soporta múltiples formatos de salida (pantalla, archivo, etc.).

### 3. 🖥️ Sistema de Pesaje con Interfaz Gráfica (`modulo3_servicio_unificado.py`)
- Interfaz construida en Tkinter.
- Permite registrar datos del pesaje (peso inicial y final), seleccionar tipo de servicio, generar e imprimir tiquetes automáticamente.
- Integra autenticación de usuarios, almacenamiento en JSON y conexión a bases de datos Access y/o MySQL.
- Incluye control de sesiones.

---

## 🧱 Tecnologías utilizadas

- **Python 3.9**
- **Tkinter** – Interfaz gráfica
- **PySerial** – Comunicación con puertos COM
- **PyODBC / PyMySQL** – Conexión con bases de datos Access y/o MySQL
- **com0com** – Simulación de puertos seriales
- **VS Code** – Entorno de desarrollo
- **Zebra / impresoras térmicas** – Generación de tiquetes físicos

---

## 🔒 Seguridad y control de acceso

- Autenticación por credenciales de usuario
- Registro de acciones realizadas por cada usuario (trazabilidad)

---

## 🧪 Estado actual del proyecto

✅ Simulador funcional  
✅ Lector de puerto COM validado con datos reales y simulados  
✅ Interfaz gráfica con impresión de tiquetes  
✅ Registro de pesajes en JSON y Access  
🔄 En proceso: integración estable con **MySQL** y módulo completo de autenticación de usuarios

---

## 📁 Estructura del repositorio (sugerida)

```
/proyecto-bascula
│
├── simulador_bascula.py
├── serialbascula.py
├── modulo3_servicio_unificado.py
├── estado_pesajes.py
├── config.py
├── modulo1_lector_unificado.py
├── modulo2_config.py
├── README.md
├── test_com0com.py
├── config_com.txt
├── estado_actual_pesajes.json
└── docs/
    └── PropuestaProyectoPractica_AndresGracianoGit.pdf
```

---

## 📈 Futuras mejoras

- Visualización de pesajes abiertos en una tabla dentro de la interfaz
- Registro completo en MySQL con respaldo automatizado
- Exportación de reportes para contabilidad y nómina
- Dashboard administrativo para análisis de pesajes

---

## 🧾 Licencia

Este proyecto fue desarrollado como parte de la práctica empresarial del programa de Ingeniería de Sistemas de la Universidad de Antioquia. Su uso está limitado a fines académicos y de mejora continua dentro de la empresa Silvotecnia S.A.S.

---

## 🤝 Contacto

- **Correo institucional**: felipe.graciano@udea.edu.co  
- **GitHub (autor)**: [Andrés Graciano](https://github.com/afgraciano)
