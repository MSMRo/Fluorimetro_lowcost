# Datos registrados

`records/` contiene CSV generados por la grabación de telemetría. `sessions/` conserva autoguardados de experimentos y, cuando existe, telemetría progresiva.

Antes de analizar estos archivos:

1. Comprueba que la sesión tenga identificador de muestra y configuración.
2. Separa lecturas sucesivas de réplicas experimentales completas.
3. Verifica ganancia, integración, PWM y canales.
4. Identifica blancos y exposiciones A/B cuando se use un cociente.
5. No interpoles lecturas `OVFL` ni extrapoles una curva de calibración.

Algunas sesiones son registros parciales de desarrollo. La presencia de un archivo no implica que el ensayo haya terminado o que cumpla un protocolo validado.

