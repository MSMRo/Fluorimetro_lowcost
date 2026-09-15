# Versión 1.0 del firmware Mega

## Función

Adquiere los diez canales del AS7341 con la biblioteca Adafruit, muestra dos páginas de cinco valores en la Nokia 5110 y transmite telemetría JSON Lines a 115200 baudios. La GUI puede cambiar ganancia, integración, página, alternancia automática y PWM de D11.

## Carga

1. Abre `firmware/mega_as7341_multichannel/mega_as7341_multichannel.ino` en Arduino IDE.
2. Selecciona `Arduino Mega or Mega 2560`.
3. Instala Adafruit AS7341 1.4.1, Adafruit GFX 1.12.6, Adafruit BusIO 1.17.4, Adafruit PCD8544 2.0.3 y ArduinoJson 6.21.5.
4. Mantén `firmware.cpp` junto al `.ino` y carga el sketch.
5. Abre la GUI descrita en
   [`../../../Software/Arduino_Mega_AS7341_GUI/v1.0/README.md`](../../../Software/Arduino_Mega_AS7341_GUI/v1.0/README.md).

La guía [`CARGAR_NOKIA.md`](CARGAR_NOKIA.md) reúne la carga y comprobación de la pantalla Nokia 5110.

## Canales transmitidos

F1 a F8 corresponden a 415, 445, 480, 515, 555, 590, 630 y 680 nm. También se transmiten NIR y Clear. Son cuentas ADC raw. `OVFL` representa una lectura de 65535 y debe tratarse como saturación digital.

## Estado de esta versión

El registro de cambios de la GUI identifica firmware 2.3.0 para el control PWM. Las pruebas host revisan el contrato de software, pero no validan la respuesta física del sensor, el display ni la etapa de potencia.
