# Guion de presentación del proyecto

Duración prevista: 20 minutos, incluyendo una demostración de aproximadamente 2 minutos y medio. Las preguntas van después. Ensayar con cronómetro y explicar las decisiones con palabras propias.

Antes de presentar: abrir las diapositivas, el dashboard y Dev Tools; comprobar los contenedores y tener lista la consulta Q03 en texto y vector. Mantener el periodo 2015–2024 y quitar filtros del ensayo. El notebook y las salidas guardadas sirven de respaldo si la demostración se interrumpe.

## 1. Presentación (0:00–0:40)

Soy Adrian Rojas Rivera. Este proyecto estudia construcción autorizada y dinámica poblacional en Costa Rica. La primera pregunta es cuánto permite estimar la población y el historial constructivo sobre el área que se autorizará el año siguiente. La segunda es cómo recuperar fragmentos sobre regulación, vivienda y crecimiento urbano mediante consultas en español. Comparo dos modelos predictivos y dos formas de búsqueda, conservando la referencia de cada dato y documento.

Fuente: anteproyecto entregado, secciones 1 y 6.

## 2. Fuentes y objetivos (0:40–1:50)

La rama numérica utiliza diez cuadros de construcción del INEC, de 2015 a 2024, y la hoja C4 de población cantonal. Son operaciones estadísticas diferentes y comparten una clave territorial y el año. El área se expresa en metros cuadrados, mientras la población conserva los decimales de la fuente para realizar los cálculos.

Los cuatro documentos del Estado de la Nación aportan contexto para búsqueda. Son investigaciones en español sobre expansión urbana y ordenamiento territorial. El texto constituye una fuente independiente y no entra como predictor del modelo numérico. También es importante delimitar el significado de los datos: los permisos representan autorizaciones administrativas y no acreditan que una obra haya terminado.

Fuente: config/fuentes.json y anteproyecto. INEC: https://admin.inec.cr/node/56328 . PEN: https://repositorio.conare.ac.cr/ .

## 3. Cruce territorial y calidad (1:50–3:10)

Los cuadros Excel tienen encabezados, subtotales y filas de detalle. La lectura reconoce las posiciones de las métricas, incluyendo columnas espaciadoras de archivos históricos, y conserva archivo, hoja, fila y columnas de procedencia. No se suman al mismo tiempo un subtotal y sus componentes.

La cobertura territorial cambia por las segregaciones de Río Cuarto, Monteverde y Puerto Jiménez. Para comparar años reúno esos cantones con Grecia, Puntarenas y Golfito, respectivamente. Esto produce 81 agrupaciones estables para el análisis. Los 818 totales cantonales de construcción y los 840 registros de población se convierten en 810 registros integrados. Las claves son únicas y el área conserva el total nacional de cada año. Los signos de ausencia permanecen identificados y no se imputan automáticamente como cero.

Fuente: output/etl.json, output/reconciliacion_nacional.csv y tests/test_proyecto.py.

## 4. Arquitectura (3:10–4:20)

La preparación de los Excel y el cruce utilizan DataFrames de Spark. PostgreSQL almacena las fuentes preparadas y el conjunto integrado mediante JDBC. La rama predictiva entrena los modelos con Spark ML y guarda sus predicciones y errores.

La otra rama extrae el texto de los PDF, lo limpia y divide en fragmentos. Hugging Face genera los vectores localmente. Elasticsearch almacena las representaciones textual y vectorial, además de los índices numéricos que alimentan Kibana. Docker reúne Spark y Jupyter, PostgreSQL, Elasticsearch y Kibana. Los vectores se guardan en caché para repetir consultas sin pagar nuevamente el costo de inferencia.

Fuente: docker-compose.yaml y programa.py. Curso: L4 video1908915064, 00:15:40–00:50:00, y L5 video1400804262, aproximadamente 01:44–01:46.

## 5. Evaluación temporal y K-fold (4:20–5:50)

Cada caso busca estimar el área del año siguiente utilizando únicamente el historial previo: las dos áreas anteriores, las obras y población más recientes y el crecimiento poblacional. Se generan 648 casos supervisados, con objetivos de 2017 a 2024.

Para incorporar K-fold, agrupo territorios completos en tres folds dentro de 2017–2021. El escalador se ajusta dentro de cada entrenamiento y no utiliza su fold de evaluación. Estos folds mezclan años del periodo de desarrollo y deben interpretarse como un diagnóstico territorial. La evaluación cronológica utiliza 2022 para comparar familias y reserva 2023–2024 para la prueba final. Después de elegir los parámetros, reajusto ambos modelos con 2017–2022. Las versiones revisadas de las fuentes hacen que esta sea una evaluación retrospectiva.

Fuente: output/decisiones_antes_prueba.json, output/cv_particiones.csv y output/modelos.json. Curso: L5 video1324764996, 00:02:40–00:06:10.

## 6. Error de los modelos (5:50–7:20)

Comparo regresión lineal regularizada, bosque aleatorio y una referencia simple: repetir el área del año anterior. El ajuste usa logaritmos y las predicciones vuelven a metros cuadrados. La selección y las métricas finales se calculan en la unidad original.

En los 162 casos reservados, la regresión lineal obtiene MAE de aproximadamente 11.791 metros cuadrados y RMSE de 22.202. El bosque alcanza errores mayores, de 13.783 y 26.837. La persistencia queda entre ambos. La lineal mejora el RMSE global en cerca de 8,95% frente a persistencia. Sin embargo, la referencia había ganado en validación 2022, y en 2023 mantiene menor MAE que la lineal. Por eso, la conclusión corresponde a esta reserva y no a una superioridad garantizada en cualquier año.

Fuente: output/metricas_modelos.csv y output/validacion_modelos.csv.

## 7. Diferencias entre modelos (7:20–8:40)

El historial de área es la información dominante: las dos áreas previas reúnen aproximadamente 84,4% de la importancia del bosque. La regresión lineal también asigna sus coeficientes más grandes a esas variables, aunque coeficientes e importancias tienen interpretaciones distintas.

La lineal produce un ajuste suave con pocos predictores. El bosque promedia regiones del espacio y tiene más dificultad para extrapolar valores extremos con pocos ejemplos. Su menor error de entrenamiento y mayor error cronológico son compatibles con un ajuste más específico del desarrollo. Ambos modelos tienden a subestimar en la prueba. El uso del objetivo logarítmico sin corrección de sesgo es una explicación posible, junto con cambios temporales. No modifiqué el modelo después de observar la prueba ni interpreto las variables como causas.

Fuente: output/atributos_modelos.csv, output/errores_territorio.csv y doc/Analisis_resultados.md.

## 8. Corpus y feedback (8:40–10:00)

El profesor recomendó controlar el tamaño de los textos y dividirlos para evitar truncamientos. Primero medí una muestra y después procesé las cuatro fuentes. De las 232 páginas originales, el alcance final conserva 194 páginas con 298 fragmentos. Se excluyen portadas, referencias y párrafos dudosos, con un registro de cada decisión.

Cada entrada tiene como máximo 400 tokens, incluyendo el prefijo y los tokens especiales. El máximo observado fue 397, por debajo del límite de 512 del modelo E5. Los vectores tienen 384 dimensiones y conservan documento, autor, año y página. Las páginas de tablas de 2021 mantienen su maquetación textual y referencia al PDF. Eso permite localizarlas, pero una afirmación sobre una fila municipal todavía requiere revisar el original.

Fuente: output/embeddings.json y output/revision_corpus.json. Modelo: https://huggingface.co/intfloat/multilingual-e5-small . Feedback del docente del 25 de octubre de 2026.

## 9. Protocolo de búsqueda (10:00–11:10)

BM25 busca sobre texto con un analizador español. La búsqueda vectorial transforma la consulta con el prefijo query y busca vecinos por similitud coseno. Ambos índices contienen exactamente los mismos fragmentos.

Se prepararon cuatro consultas de desarrollo, ocho reservadas y dos controles sin respuesta. Se revisó la unión de los cinco primeros resultados de cada método: 110 pares de consulta y fragmento. Durante esa revisión el pool no mostraba método, posición ni score. El grado dos corresponde a una respuesta directa, el uno a contexto parcial y el cero a un resultado no pertinente. La precisión entre los cinco primeros y la posición del primer relevante usan el grado dos. Es una evaluación interna pequeña y no tuvo un segundo anotador independiente.

Fuente: config/consultas.json, config/relevancia.json y doc/Criterio_relevancia.md.

## 10. Comparación de búsquedas (11:10–12:30)

En las consultas de desarrollo, la precisión estricta mejora de 0,35 con BM25 a 0,60 con vectores. Esa diferencia no se repite en reserva: ambos métodos alcanzan 0,30. El recíproco medio del primer relevante es 0,650 con BM25 y 0,625 con vectores.

Esto muestra por qué conviene separar desarrollo y evaluación. Los resultados permiten reconocer casos de utilidad semántica, pero no justifican sustituir toda búsqueda textual. La diferencia de posición media es pequeña y no se evaluó significancia estadística. Los controles también enseñan un límite práctico: ambos motores devuelven vecinos incluso cuando el corpus no contiene una respuesta. El sistema recupera fragmentos y todavía no incorpora una abstención calibrada.

Fuente: output/resumen_busqueda.csv y output/metricas_busqueda.csv.

## 11. Casos concretos (12:30–13:50)

La consulta sobre restricciones urbanas obtiene su primer pasaje directamente relevante en la primera posición con vectores y en la cuarta con BM25. Para inundaciones en Pococí, ambos recuperan primero la evidencia correcta. En el mismo conjunto aparecen pasajes de Ciudad Quesada, que se consideran no pertinentes cuando la pregunta exige Pococí.

La pregunta sobre congestión y viajes hacia San José queda sin una respuesta directa entre los cinco primeros de ambos métodos. En cambio, para renovación urbana y servicios, BM25 ubica el primer relevante antes que los vectores. Estos ejemplos ayudan a distinguir tema, ubicación y fecha, y explican por qué un score alto no debe mostrarse como una probabilidad de respuesta correcta.

Fuente: output/resultados_busqueda.json y las justificaciones de config/relevancia.json.

## 12. Demostración en Kibana (13:50–16:20)

Abrir http://127.0.0.1:5604/app/dashboards#/view/cp-dashboard . Mostrar el periodo 2015–2024 y recorrer los cinco gráficos: área anual, obras por provincia, área por habitante, categorías de destino y error de los modelos. Explicar que área por habitante usa suma de área entre suma de población del periodo y que la visualización de destinos usa solamente subtotales de categoría.

Aplicar temporalmente el filtro `provincia: "Heredia"` y mostrar que cambia la selección. Quitar el filtro. Abrir Dev Tools y ejecutar la consulta Q03 textual y su equivalente vectorial del archivo elastic/Consultas_Kibana.http. Mostrar el documento de 2017, página PDF 40, y su referencia. Si falta tiempo, ejecutar únicamente esas dos consultas y explicar el resto con la tabla de la diapositiva anterior. El archivo de resultados queda como respaldo.

Fuente: kibana/dashboard.ndjson y elastic/Consultas_Kibana.http.

## 13. Reproducción y pruebas (16:20–17:50)

El README documenta la construcción del entorno y las etapas del programa. El paquete incluye los originales, sus hashes, el notebook ejecutado, los esquemas SQL, los mappings y la exportación del dashboard. Los pesos del modelo se descargan por una revisión fija y no se incluyen en el comprimido.

Las quince pruebas comprueban lectura histórica, duplicados, dominios numéricos, armonización, historia temporal y fragmentación. La carga relee las ocho tablas de PostgreSQL y compara todas sus columnas con los DataFrames. Además, recalcula MAE y RMSE mediante SQL y verifica los identificadores y textos de los dos índices. La repetición de cargas conserva los conteos. Los logs y registros permiten revisar la ejecución sin esperar de nuevo todo el proceso durante la exposición.

Fuente: README.md, output/pruebas.log, output/cargas.json y output/verificacion_bases.json.

## 14. Alcance de los resultados (17:50–19:00)

El proyecto trabaja con agregados anuales. El horizonte es corto y hay heterogeneidad entre territorios. La armonización aborda tres segregaciones identificadas y no certifica ausencia de cualquier otro cambio de límites. Las versiones revisadas y los cambios de procesamiento de las fuentes condicionan la comparación histórica.

El corpus textual contiene documentos de 2017 a 2023 y algunas investigaciones utilizan datos del CFIA, cuya cobertura difiere de los cuadros del INEC. Por eso sus cifras no se fusionan como si midieran exactamente lo mismo. Las referencias históricas tampoco acreditan vigencia normativa actual. Para ampliar el uso harían falta una serie mayor, revisión territorial más fina y una evaluación documental independiente con más consultas.

Fuente: doc/Analisis_resultados.md y anteproyecto, secciones 3–7.

## 15. Conclusiones (19:00–20:00)

El cruce entre construcción y población es viable y conserva los totales de las fuentes. La regresión lineal consigue menor error global en la reserva final, aunque la referencia de persistencia sigue siendo competitiva y ganó en otros periodos. Para búsqueda, la ventaja de los vectores depende de la consulta y no se confirmó como una mejora global sobre BM25 en la reserva.

El aporte principal es una ejecución trazable que permite examinar datos, decisiones y errores. Las siguientes mejoras serían ampliar la historia, revisar filtros territoriales y evaluar nuevas estrategias con consultas que no se hayan usado para ajustar el sistema. Con esto cierro la presentación y quedo atento a las preguntas.

Fuente: métricas y registros de ejecución incluidos en output/.
