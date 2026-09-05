#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>
#include <Adafruit_AS7341.h>

// --- Configuración de la Pantalla Nokia 5110 ---
// Pines de datos conectados mediante resistencias de 10k para protección de 3.3V
const int pin_DC  = 5;
const int pin_CE  = 4;
const int pin_RST = 3;
// Constructor Software SPI: (CLK/SCK, DIN/MOSI, DC, CE, RST)
Adafruit_PCD8544 display = Adafruit_PCD8544(52, 51, pin_DC, pin_CE, pin_RST);

// --- Configuración del Sensor AS7341 ---
Adafruit_AS7341 as7341;

// --- Variables para el control de páginas ---
unsigned long tiempoAnterior = 0;
const unsigned long intervaloPagina = 3000; // Tiempo de rotación: 3 segundos
int paginaActual = 1;

void setup() {
  Serial.begin(115200);

  // Inicialización de la pantalla Nokia 5110
  display.begin();
  display.setContrast(55); // Ajusta según el contraste de tu pantalla
  display.clearDisplay();
  display.setRotation(2); // Ajusta la orientación física de tu pantalla
  display.display();

  // Inicialización del sensor AS7341
  if (!as7341.begin()) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("ERROR:");
    display.println("No se detecta");
    display.println("sensor AS7341");
    display.display();
    while (1) { delay(10); }
  }

  // Configuración del sensor para alta sensibilidad (ideal para fluorescencia)
  as7341.setATIME(100);
  as7341.setASTEP(999);
  as7341.setGain(AS7341_GAIN_256X);
}

void loop() {
  // Lectura en segundo plano del sensor espectral
  if (!as7341.readAllChannels()) {
    Serial.println("Error al leer canales!");
    return;
  }

  // Control de tiempo para cambiar de página sin congelar el programa
  unsigned long tiempoActual = millis();
  if (tiempoActual - tiempoAnterior >= intervaloPagina) {
    tiempoAnterior = tiempoActual;
    paginaActual++;
    if (paginaActual > 3) {
      paginaActual = 1; // Reinicia el carrusel
    }
  }

  // Actualizar el contenido de la pantalla
  actualizarPantalla();
  delay(100); // Pequeña pausa para estabilizar lecturas
}

void actualizarPantalla() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);

  // Encabezado común para todas las páginas
  display.setCursor(0, 0);
  display.print("SPECTRA [P");
  display.print(paginaActual);
  display.println("/3]");
  display.drawFastHLine(0, 7, 84, BLACK); // Línea divisoria

  // Renderizado dinámico de datos según la página activa
  switch (paginaActual) {
    case 1: // --- PÁGINA 1: Canales de Onda Corta ---
      display.setCursor(0, 10);
      display.print("F1(415):"); display.println(as7341.getChannel(AS7341_CHANNEL_415nm_F1));
      display.print("F2(445):"); display.println(as7341.getChannel(AS7341_CHANNEL_445nm_F2));
      display.print("F3(480):"); display.println(as7341.getChannel(AS7341_CHANNEL_480nm_F3));
      display.print("F4(515):"); display.println(as7341.getChannel(AS7341_CHANNEL_515nm_F4));
      break;

    case 2: // --- PÁGINA 2: Canales de Onda Larga ---
      display.setCursor(0, 10);
      display.print("F5(555):"); display.println(as7341.getChannel(AS7341_CHANNEL_555nm_F5));
      display.print("F6(590):"); display.println(as7341.getChannel(AS7341_CHANNEL_590nm_F6));
      display.print("F7(630):"); display.println(as7341.getChannel(AS7341_CHANNEL_630nm_F7));
      display.print("F8(680):"); display.println(as7341.getChannel(AS7341_CHANNEL_680nm_F8));
      break;

    case 3: // --- PÁGINA 3: Canales Especiales ---
      display.setCursor(0, 10);
      display.print("Clear:"); display.println(as7341.getChannel(AS7341_CHANNEL_CLEAR));
      display.print("NearIR:"); display.println(as7341.getChannel(AS7341_CHANNEL_NIR));
      
      // Añadimos una barra decorativa de estado del sistema
      display.setCursor(0, 34);
      display.print("SYS Status: OK");
      break;
  }

  // Envía el contenido del buffer a la pantalla física
  display.display();
}