# Fluorímetro Low Cost

Proyecto de desarrollo de un fluorímetro de bajo costo basado en Arduino. Este proyecto integra circuitos de transmisión, recepción y diseño 3D para crear un sistema completo de medición de fluorescencia.

## 📋 Descripción General

Un fluorímetro es un instrumento que mide la fluorescencia de sustancias. Este proyecto implementa una solución accesible utilizando:
- **Plataforma de control**: Arduino Mega
- **Sensor espectral**: AS7341 (multiespectrométrico)
- **Excitación**: LED controlado con DAC Delta-Sigma
- **Visualización**: Pantalla OLED Nokia 5110

## 📁 Estructura del Proyecto

```
Fluorimetro_lowcost/
├── 1_Circuito/              # Diseños de circuitos
│   ├── 1_Transmisor/        # Circuito transmisor (LED de excitación)
│   │   └── 1_TESTS/         # Pruebas y códigos
│   │       ├── 1_CORRIENTE_DELTA_SIGMA/  # Pruebas DAC Delta-Sigma
│   │       ├── 2_DAC_LED_UNO_R4/         # Pruebas para UNO R4
│   │       └── 3_TEST_KICAD/             # Diseño del shield en KiCAD
│   └── 2_Receptor/          # Circuito receptor (sensor AS7341)
│       └── 1_TEST_AS7341/   # Códigos y pruebas del sensor
├── 3_Diseño3D/              # Modelos 3D (FreeCAD)
│   ├── 1_CASE_MEGA/         # Case para Arduino Mega v1
│   └── 2_CASE_MEGA_CUBO/    # Case con cubo integrado v2
└── README.md
```

## 🔧 Circuitos

### 1. Transmisor (1_Circuito/1_Transmisor/)

Responsable de generar la luz de excitación para estimular la fluorescencia de la muestra.

**Características principales:**
- Controlador de LED con DAC Delta-Sigma para modulación de intensidad
- Múltiples versiones testeadas:
  - **Delta-Sigma para Arduino Mega**: Conversión analógica de alta resolución
  - **DAC LED UNO R4**: Variante para Arduino UNO R4
  - **Shield KiCAD**: Diseño de PCB personalizado con biblioteca 3D

**Pruebas incluidas:**
- `dac_delta_sigma_MEGA_R3_v1.ino`: Firmware para Mega
- `dac_delta_sigma_UNO_R3_v1.ino`: Firmware para UNO
- Simulaciones en SPICE para validación

### 2. Receptor (1_Circuito/2_Receptor/)

Captura el espectro de luz emitido por la muestra fluorescente.

**Sensor AS7341 (ams OSRAM):**
- **10 canales de medición**:
  - 8 canales visibles (F1-F8): 415 nm a 680 nm
  - 1 canal NIR (infrarrojo cercano): 910 nm
  - 1 canal Clear (luz blanca sin filtro)
- **Comunicación**: I2C (SDA/SCL)
- **Características**:
  - Conversores ADC independientes para cada canal
  - Ganancia ajustable (hasta 512x+)
  - Tiempo de integración configurable
  - Ideal para detectar señales tenues sin saturación

**Códigos de prueba:**
- `firmware2.ino`: Firmware principal funcional (control de LED + lectura de máximos)
- `long_onda_oled.ino`: Visualización en pantalla OLED Nokia
- `maximo_4long_onda.ino`: Muestra los 4 canales con máxima intensidad
- Librería: **Adafruit AS7341** (IDE Arduino)

**Visualización:**
- Pantalla OLED Nokia 5110 con comunicación SPI
- Display de 84x48 píxeles con limitación visual (se muestran 4 máximos canales)

## 🎨 Diseño 3D

Modelos CAD para encapsulamiento y estructura mecánica del dispositivo.

### CASE_MEGA (1_CASE_MEGA/)
- **Prototipo v1** del case para Arduino Mega
- Adaptación de diseño de terceros para incluir compartimento de cuveta
- Software: FreeCAD v1.1.1
- Basado en: [Arduino Mega 2560 Case](https://www.printables.com/model/523194-arduino-mega-2560-case/files)

### CASE_MEGA_CUBO (2_CASE_MEGA_CUBO/)
- **Prototipo v2** con integración del cubo de excitación
- Combina case del Arduino Mega + estructura para fluoróforo
- Diseño consolidado en un solo componente

## 🛠️ Herramientas y Tecnologías

| Componente | Herramienta/Tecnología |
|-----------|----------------------|
| Placa de control | Arduino Mega 2560 |
| Sensor | AS7341 (ams OSRAM) |
| Prototipado electrónico | KiCAD |
| Modelado 3D | FreeCAD v1.1.1 |
| Simulación de circuitos | SPICE |
| Programación | Arduino IDE, C/C++ |

## 📚 Bibliotecas Requeridas

- **Adafruit AS7341**: Control del sensor espectral
- **Adafruit GFX**: Gráficos para pantallas
- **Adafruit PCD8544**: Control de pantalla Nokia 5110
- **Wire**: Protocolo I2C
- **SPI**: Protocolo SPI

## 🚀 Estado del Proyecto

- ✅ Sensor AS7341 funcionando correctamente
- ✅ Control de LED con DAC Delta-Sigma
- ✅ Visualización en OLED Nokia
- ✅ Diseños 3D de prototipos
- 🔄 Optimización y validación del sistema completo

## 📝 Notas

- El firmware2 es la versión principal estable
- Se han testeado múltiples configuraciones de hardware
- Los diseños 3D están listos para impresión 3D
- Documentación con imágenes disponible en cada subdirectorio

---

*Proyecto en desarrollo - Low Cost Fluorimeter*