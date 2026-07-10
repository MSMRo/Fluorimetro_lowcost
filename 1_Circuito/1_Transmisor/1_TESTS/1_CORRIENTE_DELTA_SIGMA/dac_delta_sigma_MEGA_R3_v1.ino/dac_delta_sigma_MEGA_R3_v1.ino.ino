/*
  Fluorímetro de Bajo Costo: Control de Excitación (Pin 11) + Lectura Espectral (AS7341)
  Plataforma: Arduino Mega (ATmega2560)
*/

#include <Adafruit_AS7341.h>
#include <Wire.h>

Adafruit_AS7341 as7341;

// Configuración de la fuente de corriente constante (Timer 1 - Pin 11)
const int pinDAC = 11; 
const int valorMaximoDigital = 1023; // 10 bits de resolución
const float voltajeMaximoArduino = 5.0;

// Variables de calibración del ensayo
float voltajeExcitacion = 1.5; // Ajusta aquí el voltaje Vset analógico deseado (~4.68 mA en el LED)

void setup() {
  Serial.begin(115200);
  pinMode(pinDAC, OUTPUT);

  // --- CONFIGURACIÓN DE REGISTROS (Timer 1 en Arduino Mega) ---
  TCCR1A = _BV(COM1A1) | _BV(WGM11) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10); // Fast PWM a ~15.6 kHz (sin parpadeos para el sensor)

  // Inicializar comunicación I2C y el sensor AS7341
  if (!as7341.begin()) {
    Serial.println("¡Error! No se pudo encontrar el sensor AS7341. Verifica el cableado I2C.");
    while (1) { delay(10); }
  }
  
  // Configurar parámetros ópticos del sensor para máxima precisión en laboratorio
  as7341.setATIME(100); // Tiempo de integración básico
  as7341.setASTEP(999); // Pasos de integración (Aumenta la sensibilidad frente a fluorescencia tenue)
  as7341.setGain(AS7341_GAIN_256X); // Ganancia alta (256x) ideal para captar emisiones débiles
  
  Serial.println("Sistema de Fluorometría Listo.");
}

void loop() {
  Serial.println("\n--- Iniciando Medición de Muestra ---");

  // 1. Encendemos el LED de excitación de forma analógica y continua (DC puro)
  fijarVoltajeDAC(voltajeExcitacion);
  Serial.print("LED encendido de forma estable. Vset = "); 
  Serial.print(voltajeExcitacion); 
  Serial.println(" V");
  
  delay(500); // Pausa corta para estabilización térmica del diodo antes de leer

  // 2. Realizamos la lectura de los canales espectrales del sensor
  if (!as7341.readAllChannels()){
    Serial.println("Error al leer los datos del sensor.");
    return;
  }

  // 3. Imprimimos los resultados en el monitor serial (enfocados en el espectro de emisión)
  Serial.println("[Lecturas de Fotones por Canal]");
  Serial.print("F1 (Violeta - 415nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_415nm));
  Serial.print("F2 (Indigo  - 445nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_445nm));
  Serial.print("F3 (Azul    - 480nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_480nm));
  Serial.print("F4 (Cian    - 515nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_515nm));
  Serial.print("F5 (Verde   - 555nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_555nm));
  Serial.print("F6 (Amarillo- 590nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_590nm));
  Serial.print("F7 (Naranja - 630nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_630nm));
  Serial.print("F8 (Rojo    - 680nm): "); Serial.println(as7341.getChannel(AS7341_CHANNEL_680nm));

  // 4. Apagamos el LED de excitación entre muestras para evitar el fotoblanqueo (photobleaching)
  fijarVoltajeDAC(0.0);
  Serial.println("LED apagado. Esperando siguiente ciclo...");
  
  delay(5000); // Espera 5 segundos para la siguiente lectura de muestra
}

/*
  Control lineal del voltaje analógico para la fuente de corriente
*/
void fijarVoltajeDAC(float voltios) {
  if (voltios < 0.0) voltios = 0.0;
  if (voltios > voltajeMaximoArduino) voltios = voltajeMaximoArduino;
  int valorPWM = (voltios * valorMaximoDigital) / voltajeMaximoArduino;
  OCR1A = valorPWM; 
}