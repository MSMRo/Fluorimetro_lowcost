# PCB Shield de Caracterización de LED - Arduino Mega 2560

Este directorio contiene el diseño y la documentación de la placa de circuito impreso (**PCB Shield**) desarrollada en KiCAD para la caracterización y control del LED de excitación en el **Fluorímetro de Bajo Costo**.

![](./shield_arduino/imgs/Captura%20de%20pantalla%202026-08-31%20163016.png)


![](./shield_arduino/imgs/Captura%20de%20pantalla%202026-08-31%20163047.png)

![](./shield_arduino/imgs/Captura%20de%20pantalla%202026-08-31%20163701.png)

---

## 📋 Descripción General

La shield se conecta directamente sobre un **Arduino Mega 2560 R3** y tiene como objetivo principal proporcionar una **fuente de corriente constante regulable y de alta resolución** para alimentar el LED de excitación de la muestra fluorescente.

Al no contar el Arduino Mega con un convertidor digital-analógico (DAC) interno, esta PCB implementa una topología de **DAC Delta-Sigma por Hardware (PWM de alta frecuencia + Filtro Pasa-Bajos)** junto con una etapa de control de corriente basada en un **Amplificador Operacional y Transistor NPN**.

![](../1_TESTS/1_CORRIENTE_DELTA_SIGMA/imgs/prueba_Real.jpeg)

---

## ✨ Características Principales

- **Formato Shield Arduino Mega 2560**: Ensamblado directo mediante headers apilables sin necesidad de cableado externo.
- **Generación de Voltaje Referencia (DAC Delta-Sigma)**:
  - Utiliza el **Timer 1** del ATmega2560 (Pin **D11**) en modo *Fast PWM de 10 bits* (~15.6 kHz).
  - Filtro RC de suavizado pasa-bajos integrado para obtener un voltaje analógico $V_{set}$ continuo y estable ($0\text{V} - 5\text{V}$, resolución mínima ~4.88 mV).
- **Driver de Corriente Constante para LED**:
  - Etapa analógica formada por un **Amplificador Operacional LM358** y un **Transistor BJT NPN (2N3904 / 2N2222)**.
  - Regula de forma lineal la corriente del LED en el rango aprox. de $0\text{ mA}$ a $16\text{ mA}$ (según la resistencia de detección $R_{sense}$).
- **Entrada de Ajuste Manual**:
  - Potenciómetro lineal de $10\text{ k}\Omega$ (**RV1**) conectado a la entrada analógica **A3** para ajuste dinámico o manual de intensidad.
- **Interfaz de Expansión I2C (QWIIC 5V)**:
  - Puerto **QWIIC (J4)** con líneas $5\text{V}$, $\text{GND}$, $\text{SDA}$ y $\text{SCL}$ para acoplar el sensor multiespectral **AS7341** o sensores I2C auxiliares.
- **Conexión para Pantalla Nokia 5110**:
  - Salidas de comunicación SPI (señales `CLK`, `DIN`, `DC`, `CE`, `RST`) asignadas en la placa para conectar una pantalla OLED/LCD gráfica Nokia 5110 ($84\times 48$).
- **Pulsador de Reset Local**:
  - Botón táctil **SW1** acoplado al pin `RESET` del microcontrolador.

---

## 📐 Esquema del Circuito y Principio de Funcionamiento

![](./shield_arduino/imgs/ChatGPT%20Image%2031%20ago%202026,%2004_34_21%20p.m..png)

### Principio Físico/Electrónico
1. **DAC Delta-Sigma**: El software configura el registro `OCR1A` del Timer 1 en el Arduino Mega para emitir un ciclo de trabajo PWM proporcional a la tensión deseada. El filtro pasa-bajos convierte este tren de pulsos en un voltaje DC $V_{set}$.
2. **Lazo de Control de Corriente**: El amplificador operacional LM358 ajusta la base del transistor $Q1$ para igualar la tensión en su entrada inscripta con el voltaje de la resistencia $R_{sense}$. Así, la corriente que atraviesa el LED resulta:
   $$I_{LED} = \frac{V_{set}}{R_{sense}}$$

---

## 🛠️ Listado de Componentes Clave (BOM)

| Referencia | Componente | Descripción / Encapsulado |
| :--- | :--- | :--- |
| **U1** | **LM358** | Amplificador Operacional Doble (DIP-8 / SOIC-8) |
| **Q1** | **2N3904 / 2N2222** | Transistor NPN BJT (TO-92) |
| **D1** | **LED Excitación** | LED indicador/excitación o Bornera de conexión |
| **RV1** | **Potenciómetro 10k** | Ajuste analógico de tensión de referencia |
| **R1, R2, R5, R6, R7, R8, R9, R10** | **Resistencias** | Varias ($1\text{k}\Omega$, $10\text{k}\Omega$, etc. THT / SMD) |
| **C1** | **Capacitor $1\ \mu\text{F}$** | Capacitor de filtrado pasa-bajos |
| **SW1** | **Pulsador Tactil** | Switch de Reset |
| **J4** | **Conector QWIIC 5V** | Conector JST-SH de 4 pines para I2C |
| **Headers SPI** | **Conector 8 Pines** | Conexión para pantalla Nokia 5110 (`CLK`, `DIN`, `DC`, `CE`, `RST`) |
| **Shield Headers** | **Tiras de Pines Male/Female** | Conexión a zócalos de Arduino Mega 2560 |

---

## 📌 Asignación de Pines (Pinout Shield)

| Pin Arduino Mega | Función en la Shield | Descripción |
| :--- | :--- | :--- |
| **D11** | `PWM_DAC` | Salida de Timer 1 para DAC Delta-Sigma |
| **A3** | `POT_IN` | Lectura de voltaje del potenciómetro RV1 |
| **SDA / SCL** | `I2C` | Bus de datos I2C (Conector QWIIC J4 para AS7341) |
| **Pins SPI / GPIO** | `NOKIA_5110` | Señales `CLK`, `DIN`, `DC`, `CE`, `RST` |
| **5V / GND** | `PWR` | Alimentación general del circuito y sensores |
| **RESET** | `RST_BTN` | Pulsador de reinicio SW1 |

---

## 📂 Archivos del Proyecto KiCAD

La carpeta [`shield_arduino/`](./shield_arduino/) contiene los archivos fuente del proyecto en KiCAD:

- 📄 `shield_arduino.kicad_sch`: Esquema eléctrico completo.
- 📇 `shield_arduino.kicad_pcb`: Diseño de la placa de circuito impreso (rutas, planos de GND, capas de cobre).
- ⚙️ `shield_arduino.kicad_pro`: Archivo de proyecto de KiCAD.
- 📦 `shield_arduino-*.gbr` y `shield_arduino.drl`: Archivos **Gerber** y de taladro listos para fabricación (JLCPCB, PCBWay, etc.).
- 📐 `Librerias_step/`: Modelos 3D STEP de componentes (Pantalla Nokia 5110, Potenciómetro, etc.).

---

## 💻 Código de Prueba Rápida (Arduino Mega)

Para verificar el funcionamiento del DAC Delta-Sigma y la salida del LED, se puede cargar el siguiente firmware:

```cpp
/*
  Control de Corriente LED por DAC Delta-Sigma (10 bits)
  Plataforma: Arduino Mega 2560 (Pin D11 - Timer 1)
*/

const int pinDAC = 11; 
const int pinPot = A3;
const float vMax = 5.0;

void setup() {
  Serial.begin(115200);
  pinMode(pinDAC, OUTPUT);

  // Configuración de Timer 1 para Fast PWM de 10 bits (~15.6 kHz)
  TCCR1A = _BV(COM1A1) | _BV(WGM11) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10); // Prescaler 1
}

void fijarVoltajeDAC(float voltios) {
  if (voltios < 0.0) voltios = 0.0;
  if (voltios > vMax) voltios = vMax;
  int valorPWM = (voltios * 1023.0) / vMax;
  OCR1A = valorPWM; 
}

void loop() {
  // Lectura del potenciómetro
  float vRef = analogRead(pinPot) * (vMax / 1023.0);
  fijarVoltajeDAC(vRef);
  
  Serial.print("Voltaje de referencia fijado: ");
  Serial.print(vRef);
  Serial.println(" V");
  delay(100);
}
```

---

## 🔗 Enlaces Relacionados

- 📖 [Documentación de pruebas y simulaciones Delta-Sigma](../1_TESTS/1_CORRIENTE_DELTA_SIGMA/readme.md)
- 🔬 [Receptor y Sensor Espectral AS7341](../../2_Receptor/readme.md)
- 🏠 [Volver al README Principal del Proyecto](../../../README.md)
