# Registro de cambios

## 2026-09-14 - Escala Y automática opcional

- Se añadió el botón Auto junto al límite Y. Está desactivado al abrir la GUI; se conserva el máximo fijo inicial de 2000 cuentas.
- Auto ajusta el máximo a F1-F8 con un margen del 10 % y redondeo hacia arriba. Excluye NIR, Clear y lecturas OVFL; el límite no supera 65535 cuentas.
- El estado activo se distingue por texto y color. Al desactivarlo, el último máximo queda disponible para ajuste manual. Pausar la gráfica también congela su escala automática.
- Se evita interpolar entradas y salidas de saturación para no generar valores visuales falsos. La animación entre lecturas válidas conserva su comportamiento.
- No se cambiaron ganancia, integración, PWM, datos raw, grabación ni firmware. No hace falta volver a cargar el Mega.

## 2026-09-12 - Experimentos, resultados y calidad

- Se ampliaron Experimentos y calibración con ID de muestra, exposición, capturas de blanco y señal, intensidad corregida y blancos A/B explícitos para ambos modos de cociente.
- La curva permite intensidad raw, intensidad con blanco o cociente. Cada punto conserva concentración, unidad, método y evidencia; la compatibilidad incluye ganancia, integración, PWM, canales y protocolo/exposiciones declarados.
- Se añadió Resultados y calidad: componentes raw y restas, estadísticas de ensayos completos, advertencias, inversión de curva compatible sin extrapolación, residuos y exportación de derivados a CSV.
- Se conservan las restas negativas y se distinguen lecturas de captura de réplicas completas. No se presentan LOD/LOQ, eficiencia cuántica ni incertidumbre certificada.
- Se documentaron las fórmulas, su adaptación al AS7341 y las referencias verificadas en SCIENTIFIC_NOTES.md y en la GUI.
- El JSON versión 3 conserva blancos e intensidades derivadas; los archivos versión 2 se recuperan sin inventar una firma de calibración ausente. La carga valida datos derivados contra las lecturas originales y conserva la sesión actual si el archivo es inválido.
- No se cambiaron firmware, Nokia, adquisición en vivo, curva espectral, escala, animación, ganancia, integración ni PWM.

Validación física pendiente: blancos, estándares y réplicas con el montaje real. Las pruebas de software no validan respuesta óptica, matriz ni precisión experimental.

## 2026-09-12 - Puntuación de la interfaz

- Se sustituyeron los puntos medios decorativos por comas, dos puntos o paréntesis.
- El subtítulo describe el equipo sin barras: Caracterización óptica con Arduino Mega, AS7341 y Nokia 5110.
- Se conservaron los cocientes, unidades, rutas y toda la configuración de adquisición y gráfica.

## 2026-09-11 - PWM regulable, firmware 2.3.0

Estado de partida confirmado:

- La lectura AS7341, las ganancias, los tiempos de integración, la gráfica espectral y su escala quedan congelados sin cambios.
- La salida efectiva del firmware actual es D11 con `analogWrite(64)`, equivalente a 25 %.

Cambios realizados:

- Se añadió el comando serial `set_pwm` con rango entero 0-100 %.
- La conversión usa todo el rango de Arduino: 0 % = 0, 25 % = 64 y 100 % = 255.
- La GUI incorpora **PWM LED D11** debajo de Integración y comienza en 25 %.
- `state`, telemetría y CSV incorporan `pwm_percent` y `pwm_raw` para mantener trazabilidad experimental.
- Un cambio PWM cancela una captura experimental pendiente, igual que cambiar ganancia o integración, para no mezclar condiciones ópticas.
- Cada captura registra el PWM y las curvas exigen mantener la misma configuración. En cocientes A/B se conserva por separado el PWM usado en A y en B.
- La GUI exige que el firmware anuncie la capacidad `pwm_control`; así no presenta como compatible una versión anterior que no entienda el comando.

Pendiente:

- Cargar firmware 2.3.0 en el Mega y confirmar físicamente D11 a 0 %, 25 %, 50 % y 100 %.

## 2026-09-11 - Identidad visual del encabezado

- Se reemplazó el texto `UPCH / Spectral Lab` por el logotipo institucional proporcionado y el nombre **Spectral Lab**.
- Se aplicó una tipografía serif académica, un separador discreto y márgenes compactos.
- No se modificaron la gráfica, la adquisición, el firmware ni los controles validados.
