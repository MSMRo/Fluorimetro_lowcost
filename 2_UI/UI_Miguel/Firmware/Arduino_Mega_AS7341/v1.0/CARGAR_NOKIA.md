# Firmware Mega + AS7341 + Nokia 5110 - 2.3.0

El programa se sube al **Arduino Mega 2560**, no directamente a la Nokia.

1. Cierra la conexión de la GUI y el monitor serie del IDE.
2. Abre `firmware/mega_as7341_multichannel/mega_as7341_multichannel.ino` en Arduino IDE. Mantén `firmware.cpp` en la misma carpeta: contiene la implementación y el IDE lo compila junto al sketch.
3. Selecciona Arduino Mega or Mega 2560, procesador ATmega2560 y el puerto USB del equipo.
4. Pulsa Subir. Espera «Done uploading».
5. Reinicia la GUI actualizada y conecta el mismo puerto a 115200 baudios.
6. En **Adquisición en vivo**, verifica Ganancia, Integración y **PWM LED D11**. El valor inicial debe indicar 25 %.

La versión 2.3.0 conserva sin cambios la adquisición validada con la API pública de Adafruit, el orden F1-F8/CLEAR/NIR, 128x/300ms al iniciar y el watchdog. El único cambio funcional del firmware es que el PWM de D11 ahora puede ajustarse desde la GUI entre 0 y 100 %.

Cableado actual: AS7341 SDA→20, SCL→21. Nokia CLK→52, DIN→51, DC→5, CE→4, RST→3. La salida PWM del LED externo es D11 y comienza en 25 % (`analogWrite(64)`). GND común. La alimentación y adaptación de niveles dependen del módulo: no conectes señales de 5 V directamente a una Nokia o sensor que no las tolere.

**Iniciar grabación** y **Detener y guardar CSV** controlan el registro. **Pausar gráfica** no detiene la recepción ni el CSV. Cada fila conserva las diez bandas, fecha UTC, secuencia, tiempo del Mega, ganancia, integración, porcentaje PWM y valor PWM raw.

La escala vertical es manual y fija. La gráfica no inventa muestras intermedias: la frecuencia real depende de la integración y lectura del sensor. La validación física de la Nokia y sus niveles eléctricos queda pendiente de la prueba en el equipo.
