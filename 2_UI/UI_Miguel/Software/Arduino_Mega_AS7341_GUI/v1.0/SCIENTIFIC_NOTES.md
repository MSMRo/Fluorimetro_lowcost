# Base experimental y límites

Documentos locales examinados en `../Papers`, relativos a la carpeta FIRMWARE_IORODEO. La adaptación de software no reproduce ni valida las prestaciones de esos instrumentos.

| PDF | Evidencia consultada | Aplicación en la GUI |
| --- | --- | --- |
| Ratiometric design.pdf | Zhou et al., 2026, DOI 10.1016/j.microc.2026.118982, página PDF 2: cocientes entre emisiones seleccionadas y referencias internas | Selección explícita de canales y orientación A/B. No se asignan automáticamente bandas a un fluoróforo. |
| low_cost_1.pdf | Chen et al., Talanta 269, 125447, páginas PDF 4 y 5: estándares de concentración, promediado, ajuste lineal y mediciones replicadas | Promedio de N lecturas posteriores al clic; desviación estándar guardada; calibración con estándares, R² y RMSE. |
| low_cost_2.pdf | Power et al., DOI 10.1039/d3ay00991b, página PDF 1: fluorómetro con varias fuentes LED y detección multiespectral | Identificación manual de LED y conservación de todos los canales. El cociente de dos excitaciones es una adaptación experimental, no una equivalencia validada con ese artículo. |
| low_cost_3.pdf | Faghir Hagh et al., DOI 10.1109/JSEN.2024.3403416, página PDF 1: distintas excitaciones, calibración con patrones y almacenamiento local | Separación de condiciones de iluminación, puntos trazables y exportación. No se reproducen LoRa, turbidez ni conversiones de pigmentos. |
| Open-JIP.pdf | Bates et al., DOI 10.1007/s11120-019-00673-2, página PDF 1: protocolo OJIP y rendimiento fotoquímico | Define una limitación: no calcular Fv/Fm ni OJIP desde capturas manuales lentas del AS7341. |

## Métodos implementados

- LED sucesivos: colocar LED A, esperar estabilidad, capturar; cambiar manualmente a LED B, esperar y capturar. R = media del canal A bajo LED A / media del canal B bajo LED B. Se pueden elegir el mismo canal o canales diferentes. La deriva entre exposiciones no se cancela automáticamente.
- Referencia óptica: Q = emisión medida / excitación de referencia medida. Ambas son capturas sucesivas del AS7341, conservadas con su configuración. Es un cociente instrumental, no eficiencia cuántica ni irradiancia calibrada. La geometría y la respuesta espectral deben caracterizarse experimentalmente.
- Blanco: no se permite usarlo como denominador. En Blanco y fondo se captura por separado, identificado por exposición. La corrección explícita conserva S = media(señal) - media(blanco), incluso si es negativa. Se exige igualdad de exposición, protocolo, ganancia, integración y PWM. Para corregir un cociente se seleccionan los blancos de A y B: R = (A - blanco A) / (B - blanco B). Señal y referencia corregidas deben ser positivas para informar ese cociente.
- Calibración: y = m c + b por mínimos cuadrados ordinarios, intercepto libre. Se requieren tres concentraciones distintas; cada clic de intensidad recoge una nueva captura. Los cocientes guardados solo pueden añadirse una vez por par de capturas. No se mezclan canales, métodos, unidades ni ajustes del sensor. Los estándares replicados se conservan como puntos separados.
- El R² y el RMSE describen el ajuste a esos puntos. No constituyen validación externa ni estimación de LOD/LOQ. Las N lecturas consecutivas de una captura no son N réplicas independientes del ensayo.

Cada captura conserva cuentas crudas, media, desviación estándar, secuencias, tiempo del dispositivo, hora de finalización de captura, etiqueta, ganancia, integración y protocolo óptico declarado. El CSV guarda la hora de recepción de cada lectura. Se rechazan cuentas de 65535, denominador cero y cambios de configuración. Esto no certifica ausencia de saturación analógica ni linealidad. Se usa la integración nominal reportada por el firmware; no se aplica una conversión radiométrica entre bandas.

## Resultados y calidad (2026-09-12)

Esta sección interpreta el experimento actual o un JSON recuperado. No modifica el firmware, las cuentas, la gráfica en vivo ni los controles validados.

- Señales y réplicas muestra componentes raw, blancos y restas; media, SD y número de lecturas; ganancia, integración, PWM, exposición e IDs. Con una sola lectura la SD se muestra como no disponible. La SD de una resta o cociente no se obtiene por propagación automática: no se ha caracterizado la dependencia entre las lecturas y exposiciones.
- Los resultados con el mismo ID de muestra y firma experimental se agrupan como repeticiones del ensayo completo. Se informa media, SD muestral y RSD = 100 SD / |media| con al menos dos ensayos. Un resultado A/B requiere capturas nuevas de ambos componentes. Si comparten señal o referencia, la estadística de réplicas se bloquea; si comparten blancos se advierte de posible correlación y deriva. La SD es descriptiva, no incertidumbre total ni precisión certificada.
- Calibración e interpretación muestra puntos, valores ajustados y residuos (medido menos ajustado), R² y RMSE = raíz de la media de residuos al cuadrado. Estima c = (y - b) / m solo con método y unidad compatibles y una captura que no pertenezca a los estándares. Se bloquea extrapolar y se retienen los límites de concentración calibrados. El ajuste es ordinario, no ponderado, y no certifica linealidad: deben revisarse residuos y controles independientes.
- El aviso de referencia baja compara el denominador con un umbral editable en cuentas (inicialmente 1). Es un criterio operativo que impide informar concentración desde un cociente de referencia baja; no constituye un límite validado de señal/ruido, detección o cuantificación. Se conservan el cociente y su evidencia.
- Un blanco o una señal corregida no positiva no recibe concentración. Tampoco se atribuye una firma completa de calibración a resultados históricos versión 2. Se recupera su evidencia y se recalcula lo verificable; para continuar un ensayo se necesitan capturas nuevas.
- Exportar resultados CSV conserva IDs, configuraciones, método, valor raw y derivado, blancos, estadísticas, advertencias y concentración cuando procede. Incluye capturas y resultados guardados, diferenciados por evidence_type; la fila de una captura que aparece también como componente de un resultado no es una réplica adicional. El destino inicial es records/. El JSON versión 3 contiene las lecturas completas y se valida contra ellas al recuperarlo. Un CSV de adquisición raw no contiene por sí solo la asignación de blancos, muestras y estándares necesaria para reconstruir el ensayo.

## Bibliografía de los cálculos nuevos

1. Chen, X., et al. (2024). *A low-cost and portable fluorometer based on an optical pick-up unit for chlorophyll-a detection*. Talanta, 269, 125447. [DOI](https://doi.org/10.1016/j.talanta.2023.125447). Archivo local low_cost_1.pdf, página PDF 5, secciones 2.5 y 3.1: diferencia entre promediado de lecturas y tres pruebas separadas por concentración. Se adapta esa distinción; no se transfieren sensibilidad, LOD ni prestaciones del instrumento publicado.
2. Cantwell, H. (ed.) (2025). *Blanks in Method Validation*, 2.ª ed. Eurachem. [Guía](https://www.eurachem.org/images/stories/Guides/pdf/MV_Guide_Blanks_supplement_2nd_ed_EN.pdf). Página PDF 11 (página impresa 4), sección 3: tipos y usos del blanco. La guía orienta su elección; la corrección rutinaria de baseline queda fuera de su alcance explícito (página PDF 10). No se cita como prescripción de nuestra fórmula de resta.
3. Marston, D. J., Slattery, S. D., Hahn, K. M., y Tsygankov, D. (2021). *Correcting Artifacts in Ratiometric Biosensor Imaging; an Improved Approach for Dividing Noisy Signals*. Frontiers in Cell and Developmental Biology, 9, 685825. [DOI](https://doi.org/10.3389/fcell.2021.685825), [texto completo](https://pmc.ncbi.nlm.nih.gov/articles/PMC8418531/). Ecuación 2: cociente con resta de fondo en ambos componentes. Resultados, apartados sobre división por señales débiles: corregir el fondo no elimina los artefactos de denominadores ruidosos. Se adapta la operación a cuentas del AS7341, no la validación de imagen celular ni el método NCF propuesto por los autores.
4. NIST/SEMATECH. *e-Handbook of Statistical Methods*, sección 2.3.6.6, [Using the calibration curve](https://itl.nist.gov/div898/handbook/mpc/section3/mpc366.htm). Respalda la inversión de y = a + b x para recuperar x con el mismo instrumento y proceso controlado. La GUI no incorpora todavía el cálculo completo de incertidumbre de la concentración.
5. Zhou, M., et al. (2026). *Ratiometric fluorescence arrays: a review of design strategies, signal decoding, mechanisms, and applications*. Microchemical Journal, 228, 118982. [DOI](https://doi.org/10.1016/j.microc.2026.118982). Archivo local Ratiometric design.pdf, página PDF 2: cocientes de emisiones y referencias internas. Un LED externo o una referencia capturada sucesivamente no garantizan autocorrección de deriva, geometría o potencia de excitación.
6. DeRose, P. C. (2008). *Standard Guide to Fluorescence: Instrument Calibration and Validation*. NISTIR 7458. [DOI](https://doi.org/10.6028/NIST.IR.7458). Referencia de alcance metrológico: los derivados de cuentas no equivalen a irradiancia, concentración universal ni eficiencia cuántica sin calibración y validación del sistema óptico.

Las referencias están disponibles dentro de Resultados y calidad, en Métodos y bibliografía. Consulta de páginas y PDFs realizada el 2026-09-12. Se verificaron los PDFs locales directamente con pdftotext; no se utilizó PaperQA2 para estas comprobaciones.

## Uso

Ejecutar `desktop_gui/app.py` con las dependencias del proyecto. En Experimentos y calibración, introducir el ID de muestra, el protocolo óptico y N lecturas. Mantener el ID al repetir un ensayo de la misma muestra. Exposición identifica la condición actual (LED, filtro y posición); no debe cambiar entre blanco y señal de esa condición. El protocolo general describe ambas exposiciones A/B y debe mantenerse durante el ensayo y la curva.

En Blanco y fondo, seleccionar el canal y capturar blanco y señal por separado. Seleccionar ambos registros y guardar intensidad corregida. Para LED sucesivos o Baseline y referencia, capturar A y B; si se desea corrección, marcarla y seleccionar el blanco de cada exposición. No hay asignación automática de blancos. Cada resultado exige un ensayo A/B nuevo. El firmware descarta la integración anterior al comando, espera la estabilización y etiqueta las muestras nuevas.

En Curva de calibración, elegir intensidad raw, intensidad con blanco o último cociente guardado. Introducir concentración conocida y unidad; guardar cada estándar, con al menos tres niveles distintos, y ajustar. Para medir una muestra desconocida no se añade un punto de concentración supuesta: se captura señal o un ensayo A/B y se consulta Resultados y calidad. Abrir un JSON recupera evidencia sin convertirla en ensayo activo. Guardar experimento JSON conserva la evidencia completa; los CSV entregan tablas de adquisición, estándares o derivados según el botón utilizado.

## Revisión de interfaz

| Antes | Después | Motivo |
| --- | --- | --- |
| Adquisición, controles y actividad en una única vista | Pestañas de adquisición y experimentos; etapas de captura explícitas | Separar la lectura en vivo de las acciones experimentales. |
| Selectores enviaban índices; CSV fallaba con campo extra | Envío de texto del selector y filas CSV planas probadas | Evitar comandos rechazados y pérdida de exportación. |
| Eje espectral equidistante | Posiciones por longitud de onda y exclusión de saturados | No representar separaciones espectrales falsas ni saturación como señal cuantitativa. |

Apple HIG orientó jerarquía, controles legibles y estados explícitos; Emil orientó respuestas inmediatas sin animaciones decorativas durante adquisición.
