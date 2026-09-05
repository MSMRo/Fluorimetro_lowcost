#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>
#include <Adafruit_AS7341.h>

//================== CONFIGURACIÓN PANTALLA NOKIA 5110 ==================
const int pin_DC  = 5;
const int pin_CE  = 4;
const int pin_RST = 3;

// CONSTRUCTOR PARA HARDWARE SPI (Velocidad máxima de refresco)
Adafruit_PCD8544 display = Adafruit_PCD8544(pin_DC, pin_CE, pin_RST);

//================== CONFIGURACIÓN SENSOR AS7341 ==================
Adafruit_AS7341 as7341;

struct Canal {
  const char* nombre;
  uint16_t valor;
};

//================== CONFIGURACIÓN LED Y ADC ==================
const int pinDAC = 11;                // Pin 11 (Timer 1) para el LED en el Mega
const int pinPotenciometro = A0;      // Pin de lectura analógica para el potenciómetro
const int valorMaximoDigital = 1023;  // Resolución de 10 bits
const float voltajeMaximoArduino = 5.0;

// Variables de control de brillo
float voltajeExcitacion = 0.0;
int lecturaAnterior = 0;
const int umbralRuido = 5;            // Filtro para evitar que el ruido del potenciómetro haga oscilar el LED

void setup() {
  Serial.begin(115200);
  pinMode(pinDAC, OUTPUT);

  // Configuración del Timer 1 en el Arduino Mega (~15.6 kHz para evitar parpadeos)
  TCCR1A = _BV(COM1A1) | _BV(WGM11) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10); 

  // Inicializar pantalla Nokia 5110
  display.begin();
  display.setContrast(55); 
  display.setRotation(2);  
  display.clearDisplay();
  display.display();

  // Inicializar sensor AS7341
  if (!as7341.begin()) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("ERROR");
    display.println("AS7341");
    display.println("No detectado");
    display.display();
    while (1) { delay(10); }
  }

  // Configuración de integración rápida (~100ms) para respuesta en tiempo real
  as7341.setATIME(29);  
  as7341.setASTEP(599); 
  as7341.setGain(AS7341_GAIN_256X);

  Serial.println("Fluorímetro con Control de Brillo Continuo por ADC Listo.");
}

void loop() {
  // 1. Leer el potenciómetro y aplicar filtro de ruido
  int lecturaActual = analogRead(pinPotenciometro);
  
  if (abs(lecturaActual - lecturaAnterior) > umbralRuido) {
    lecturaAnterior = lecturaActual;
    // Mapeamos la lectura analógica de 0-1023 al voltaje de excitación deseado (0V a 5V)
    voltajeExcitacion = (lecturaActual * voltajeMaximoArduino) / 1023.0;
  }

  // 2. Ajustar el brillo del LED (Se queda encendido de forma continua, sin apagarse)
  fijarVoltajeDAC(voltajeExcitacion);

  // 3. Leer todos los canales del sensor espectral
  if (!as7341.readAllChannels()) {
    Serial.println("Error leyendo AS7341");
    return;
  }

  // 4. Procesar, ordenar y mostrar únicamente los 4 canales con mayor señal
  actualizarPantallaYProcesar();

  // Pequeña pausa para que el bucle fluya con suavidad y permita lecturas dinámicas
  delay(100); 
}

// Control analógico lineal mediante PWM por hardware
void fijarVoltajeDAC(float voltios) {
  if (voltios < 0.0) voltios = 0.0;
  if (voltios > voltajeMaximoArduino) voltios = voltajeMaximoArduino;
  int valorPWM = (voltios * valorMaximoDigital) / voltajeMaximoArduino;
  OCR1A = valorPWM; 
}

void actualizarPantallaYProcesar() {
  Canal canales[8] = {
    {"F1 415", as7341.getChannel(AS7341_CHANNEL_415nm_F1)},
    {"F2 445", as7341.getChannel(AS7341_CHANNEL_445nm_F2)},
    {"F3 480", as7341.getChannel(AS7341_CHANNEL_480nm_F3)},
    {"F4 515", as7341.getChannel(AS7341_CHANNEL_515nm_F4)},
    {"F5 555", as7341.getChannel(AS7341_CHANNEL_555nm_F5)},
    {"F6 590", as7341.getChannel(AS7341_CHANNEL_590nm_F6)},
    {"F7 630", as7341.getChannel(AS7341_CHANNEL_630nm_F7)},
    {"F8 680", as7341.getChannel(AS7341_CHANNEL_680nm_F8)}
  };

  // Imprimir espectro completo por Serial para monitoreo del sistema
  Serial.print("Vset: "); Serial.print(voltajeExcitacion); Serial.println(" V");
  Serial.println("--- Espectro de Emisión ---");
  for (int i = 0; i < 8; i++) {
    Serial.print(canales[i].nombre);
    Serial.print("nm: ");
    Serial.println(canales[i].valor);
  }
  Serial.println("");

  // Algoritmo de ordenamiento (Bubble Sort) de mayor a menor
  for (int i = 0; i < 7; i++) {
    for (int j = i + 1; j < 8; j++) {
      if (canales[j].valor > canales[i].valor) {
        Canal temp = canales[i];
        canales[i] = canales[j];
        canales[j] = temp;
      }
    }
  }

  // --- ACTUALIZAR PANTALLA NOKIA 5110 (Muestra estrictamente SOLO el Top 4) ---
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);

  // Cabecera estática que muestra el Vset actual fijado por tu potenciómetro
  display.setCursor(0,0);
  display.print("Vset: ");
  display.print(voltajeExcitacion, 2);
  display.println("V");
  display.drawFastHLine(0, 8, 84, BLACK);

  // Imprimir los 4 canales con mayor señal en tiempo real
  for (int i = 0; i < 4; i++) {
    display.setCursor(0, 10 + i * 9);
    display.print(canales[i].nombre);
    display.print(":");

    display.setCursor(50, 10 + i * 9);
    
    uint16_t v = canales[i].valor;
    if (v >= 10000) {
      //display.print(v / 1000);
      //display.print("k");
      display.print(v);
    } else {
      display.print(v);
    }
  }

  display.display();
}