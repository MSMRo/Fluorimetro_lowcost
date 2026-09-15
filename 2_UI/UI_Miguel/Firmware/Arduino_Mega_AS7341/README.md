# Firmware para Arduino Mega y AS7341

La versión actual está en [`v1.0/`](v1.0/). El sketch usa un Arduino Mega 2560, un AS7341 y una pantalla Nokia 5110. La salida D11 controla la iluminación externa mediante PWM.

## Archivos principales

- `v1.0/firmware/mega_as7341_multichannel/mega_as7341_multichannel.ino`: entrada del sketch para Arduino IDE.
- `v1.0/firmware/mega_as7341_multichannel/firmware.cpp`: implementación del firmware.
- `v1.0/tests/firmware_host/`: dobles de las bibliotecas Arduino y prueba host.

## Cableado conservado en el firmware

| Señal | Arduino Mega 2560 |
| --- | --- |
| AS7341 SDA | D20 / SDA |
| AS7341 SCL | D21 / SCL |
| Nokia SCLK | D52 |
| Nokia DIN / MOSI | D51 |
| Nokia DC | D5 |
| Nokia CE | D4 |
| Nokia RST | D3 |
| PWM LED | D11 |

Verifica el voltaje admitido por cada módulo antes de conectarlo. La asignación de pines no certifica compatibilidad con lógica de 5 V.

