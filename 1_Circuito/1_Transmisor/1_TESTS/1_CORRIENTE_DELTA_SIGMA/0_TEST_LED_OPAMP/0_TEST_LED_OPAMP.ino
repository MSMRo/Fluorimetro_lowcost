#include <Adafruit_AS7341.h>
#include <Wire.h>

Adafruit_AS7341 as7341;

// Configuración de la fuente de corriente constante (Timer 1 - Pin 11)
const int pinDAC = 11; 
const int valorMaximoDigital = 1023; // 10 bits de resolución
const float voltajeMaximoArduino = 5.0;

// Variables de calibración del ensayo
float voltajeExcitacion; // = 1.5; // Ajusta aquí el voltaje Vset analógico deseado (~4.68 mA en el LED)

void setup() {
  Serial.begin(115200);
  pinMode(pinDAC, OUTPUT);

  // --- CONFIGURACIÓN DE REGISTROS (Timer 1 en Arduino Mega) ---
  TCCR1A = _BV(COM1A1) | _BV(WGM11) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10); // Fast PWM a ~15.6 kHz (sin parpadeos para el sensor)

  
  Serial.println("Sistema de Fluorometría Listo.");
}

void loop() {
  Serial.println("\n--- Iniciando Medición de Muestra ---");
  voltajeExcitacion = analogRead(A0)*5/1023.0;
  // 1. Encendemos el LED de excitación de forma analógica y continua (DC puro)
  fijarVoltajeDAC(voltajeExcitacion);
  Serial.print("LED encendido de forma estable. Vset = "); 
  Serial.print(voltajeExcitacion); 
  Serial.println(" V");
  
  delay(500); // Pausa corta para estabilización térmica del diodo antes de leer

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