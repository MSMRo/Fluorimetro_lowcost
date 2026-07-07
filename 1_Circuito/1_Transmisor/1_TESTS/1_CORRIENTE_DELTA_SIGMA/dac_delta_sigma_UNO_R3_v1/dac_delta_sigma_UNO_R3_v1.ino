/*
  Demo: DAC por PWM de Alta Velocidad (Filtro RC) adaptado para Arduino Uno R3
  Plataforma: Arduino Uno R3 (ATmega328P)
*/

// En el Arduino Uno, modificaremos el Timer 1, por lo que debemos usar fijamente el Pin 9
const int pinDAC = 9; 

// El Timer 1 en modo "Fast PWM" configurado sin pre-escaler nos otorga:
// Frecuencia = 16 MHz / 1024 pasos = 15.625 kHz (Suficientemente alta para el filtro RC)
const int valorMaximoDigital = 1023; // 10 bits de resolución (0 a 1023)
const float voltajeMaximoArduino = 5.0; // El Arduino Uno opera nativamente a 5.0V

// Variable para definir la tensión analógica que deseas a la salida del filtro RC
float voltajeDeseado = 2.0; 

void setup() {
  Serial.begin(115200);
  pinMode(pinDAC, OUTPUT);

  // --- CONFIGURACIÓN AVANZADA DE REGISTROS (Timer 1) ---
  // Configuramos el Timer 1 para Fast PWM de 10 bits (Frecuencia ~15.6 kHz)
  // Esto reemplaza las funciones específicas que usamos en la Pico.
  TCCR1A = _BV(COM1A1) | _BV(WGM11) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10); // Sin pre-escaler (frecuencia máxima disponible)
}

void loop() {
  // --- Ejemplo 1: Mantener un voltaje analógico constante ---
  voltajeDeseado = analogRead(A3)*(5/1023.0);
  fijarVoltajeDAC(voltajeDeseado);
  
  Serial.print("Voltaje de salida constante fijado en: ");
  Serial.print(voltajeDeseado);
  Serial.println(" V");
  
  //delay(4000); 

  // --- Ejemplo 2: Rampa dinámica interactiva ---
  Serial.println("Iniciando rampa dinamica basada en Voltios...");
  //for (float v = 1.0; v <= 3.0; v += 0.05) { 
  //  fijarVoltajeDAC(v);
  //  delay(30); 
  //}
  //delay(1000);
}

/*
  Función matemática adaptada para el hardware del Arduino Uno (5V y 10 bits)
*/
void fijarVoltajeDAC(float voltios) {
  // Limitamos por seguridad según el rango real del pin del Arduino
  if (voltios < 0.0) voltios = 0.0;
  if (voltios > voltajeMaximoArduino) voltios = voltajeMaximoArduino;

  // Regla de tres directa adaptada a 5V y resolución de 1023:
  int valorPWM = (voltios * valorMaximoDigital) / voltajeMaximoArduino;

  // Actualizamos directamente el registro de comparación del Timer 1 (Pin 9)
  OCR1A = valorPWM; 
}