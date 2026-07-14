#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>
#include <Adafruit_AS7341.h>

//================== CONFIGURACIÓN PANTALLA NOKIA 5110 ==================
const int pin_DC  = 5;
const int pin_CE  = 4;
const int pin_RST = 3;

// CONSTRUCTOR PARA HARDWARE SPI (¡Mucho más rápido!)
// Al omitir los pines 52 (CLK) y 51 (DIN), el Arduino Mega usa su hardware nativo SPI.
Adafruit_PCD8544 display = Adafruit_PCD8544(pin_DC, pin_CE, pin_RST);

//================== CONFIGURACIÓN SENSOR AS7341 ==================
Adafruit_AS7341 as7341;

struct Canal {
  const char* nombre;
  uint16_t valor;
};

//================== CONFIGURACIÓN LED EXCITACIÓN ==================
const int pinDAC = 11; 
const int valorMaximoDigital = 1023; 
const float voltajeMaximoArduino = 5.0;
float voltajeExcitacion = 1.5; 

void setup() {
  Serial.begin(115200);
  pinMode(pinDAC, OUTPUT);

  // Configuración del Timer 1 en Arduino Mega (~15.6 kHz)
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

  // CONFIGURACIÓN DE INTEGRACIÓN RÁPIDA (Lectura total en ~100ms)
  as7341.setATIME(29);  
  as7341.setASTEP(599); 
  as7341.setGain(AS7341_GAIN_256X);

  Serial.println("Fluorímetro Optimizado de Alta Velocidad OK.");
}

void loop() {
  // 1. Encendemos el LED de excitación
  fijarVoltajeDAC(voltajeExcitacion);
  
  // Reducimos el tiempo de espera térmica a 100ms (suficiente para estabilidad óptica)
  delay(100); 

  // 2. Leer todos los canales del sensor espectral (Ahora toma ~100ms)
  if (!as7341.readAllChannels()) {
    Serial.println("Error leyendo AS7341");
    fijarVoltajeDAC(0.0); 
    delay(100);
    return;
  }

  // 3. Procesar, ordenar y mostrar los 4 canales máximos
  actualizarPantallaYProcesar();

  // 4. Apagar el LED de excitación inmediatamente para evitar el fotoblanqueo (photobleaching)
  fijarVoltajeDAC(0.0);

  // 5. Ciclo de espera reducido para un refresco rápido del sistema
  delay(300); // 300 ms de pausa para permitir lecturas dinámicas continuas y fluidas
}

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

  // Ordenamiento rápido (Bubble Sort)
  for (int i = 0; i < 7; i++) {
    for (int j = i + 1; j < 8; j++) {
      if (canales[j].valor > canales[i].valor) {
        Canal temp = canales[i];
        canales[i] = canales[j];
        canales[j] = temp;
      }
    }
  }

  // --- ACTUALIZAR PANTALLA NOKIA 5110 ---
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);

  display.setCursor(0,0);
  display.println("MAXIMOS (4):");
  display.drawFastHLine(0, 8, 84, BLACK);

  for (int i = 0; i < 4; i++) {
    display.setCursor(0, 10 + i * 9);
    display.print(canales[i].nombre);
    display.print(":");

    display.setCursor(50, 10 + i * 9);
    
    uint16_t v = canales[i].valor;
    if (v >= 10000) {
      display.print(v / 1000);
      display.print("k");
    } else {
      display.print(v);
    }
  }
  display.display();
}