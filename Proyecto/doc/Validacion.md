# Validación de la entrega

Ejecución local del 28 de octubre de 2026. No se usan resultados de ejemplo para representar una ejecución del proyecto.

## Preparación y pruebas

- 15 pruebas automatizadas aprobadas en 21,51 s (`output/Pruebas.txt`, incluido en el paquete). Incluyen limpieza sobre las 12 121 filas originales de destinos, además de casos de fallo.
- 15 originales coinciden con los hashes del manifiesto de fuentes.
- 818 totales cantonales de construcción, 840 registros de población, 12 121 destinos; 81 territorios armonizados y 810 integrados.
- Claves únicas, join sin pérdidas y reconciliación nacional por año; la suma de categorías de destino se verifica sin sumar sus detalles.
- 312 signos N.D de 2019 y la N aislada de K1413 de 2020 permanecen nulos y se registran en `output/auditoria_signos.json`; no se imputaron conteos.

## Ejecución completa y bases

El comando `python programa.py todo`, desde el servicio app, completó consecutivamente preparación, entrenamiento, embeddings, carga, búsqueda, dashboard y verificación. El registro detallado está en `output/Ejecucion_completa.txt` incluido en el paquete; los informes JSON y CSV se incluyen en el paquete.

PostgreSQL contiene las ocho tablas documentadas. La relectura JDBC compara todas las columnas con `exceptAll` en ambos sentidos. Se recalculan las métricas de los dos regresores con SQL y coinciden con Spark dentro de la tolerancia documentada. La carga se repitió sin alterar cantidades o contenido.

Elasticsearch contiene siete índices; `cp-texto` y `cp-vector` conservan los mismos 298 IDs y textos. Las predicciones son 324, correspondientes a dos modelos por 162 casos de prueba.

La segunda pasada reutilizó los 298 vectores de pasajes y las 14 consultas, con cero entradas nuevas. El informe inicial conserva la medición de 33,94 s de codificación de pasajes. Las firmas de corpus/modelo/versiones coinciden.

## Resultados y visuales

- Se ejecutaron 28 búsquedas para 14 consultas; todos los resultados del pool tienen juicio entre 0 y 2 y justificación, 110 pares.
- Q03 se ejecutó además en Dev Tools de Kibana con texto y con el vector completo: ambas respondieron 200 OK, sin shards fallidos, y recuperaron primero el mismo fragmento de Pococí. Capturas en `output/Consulta_*_Kibana.png`.
- Cinco visualizaciones de Kibana revisadas en pantalla. Se probó `provincia: "Heredia"` y se restauró el filtro vacío; capturas superior, inferior y filtrada en `output/`.
- Notebook ejecutado nuevamente después de la ejecución completa; contiene consultas reales a las bases y gráficos.
- Manual PDF: 12 páginas renderizadas y revisadas. Presentación: 15 diapositivas revisadas, cinco tablas y tres gráficos nativos editables, notas con guion. Se verificaron estructura, geometría, fuentes y libros de datos de gráficos. No se afirma una apertura nativa en PowerPoint.

## Límites de la evidencia

La validación de relevancia es interna y no tiene un segundo anotador independiente. Los folds territoriales no son folds temporales. La prueba cronológica usa versiones revisadas de las fuentes. Ni los permisos ni los textos históricos acreditan obras terminadas, causalidad o vigencia regulatoria actual. La lineal mejora el agregado de prueba, pero persistencia ganó en validación 2022; los vectores no superan BM25 en las ocho consultas reservadas.

La validación local no equivale a enviar el correo, otorgar acceso al profesor, entregar en clase o realizar la exposición. Esos pasos se registran por separado en la lista de entrega.
