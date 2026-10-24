# Validación de la tarea 3

Fecha de ejecución: 2026-10-23T10:05:11.480477-06:00.

## Ejecución integral

El notebook se ejecutó completo en el servicio bigdata de Docker Compose, con Python 3.10.12, Spark 3.5.1, Java 17 y JDBC 42.7.3. PostgreSQL 16.6 corre en un servicio separado. El notebook tiene 11 celdas de código ejecutadas, sin errores, y cinco figuras integradas.

- Entrada y salida de calidad: 10000 registros; 0 inválidos, 0 duplicados exactos y 0 filas de ID conflictivos.
- Entrenamiento: 8079; reserva: 1921; semilla: 27; K: 4.
- Las particiones son disjuntas y cubren todos los ID; los folds se equilibran por clase.
- Se comparó el contenido completo de tarea3 tras escribir y leer por JDBC.
- tarea3 tiene 10000 filas; modelo1 y modelo2 tienen 1921 cada una.
- Las tablas de modelos contienen las siete columnas originales y prediccion; no contienen vectores.
- Se repitieron las tres escrituras con overwrite y se comprobó igualdad del contenido y conteos.
- Las consultas de sql/Verificacion.sql terminaron correctamente; salida en output/Verificacion_SQL.txt.

El tiempo del procesamiento registrado dentro del notebook fue 41.6 segundos, sin construcción de imagen; varía según equipo. La identidad del dataset se comprueba mediante SHA-256.

## Pruebas automatizadas

Comando: `docker compose exec -T bigdata pytest -q --junitxml=output/Pruebas.xml`.

Resultado: 5 pruebas, 0 fallos y 0 errores. Se prueban reglas de limpieza con datos inválidos y conflictos, reserva estable y disjunta, folds equilibrados, rechazo de clases insuficientes y salida SQL sin vectores. La advertencia de deprecación distutils proviene de PySpark; no produjo fallos.

## Métricas finales

| Métrica | Regresión logística | Bosque aleatorio |
|---|---:|---:|
| AUC ROC | 0.7181 | 0.7196 |
| AUC PR | 0.6242 | 0.6299 |
| Accuracy | 0.6710 | 0.6653 |
| Precision positiva | 0.6381 | 0.6564 |
| Recall positivo | 0.4988 | 0.4243 |
| F1 positivo | 0.5599 | 0.5154 |

La interpretación completa está dentro del notebook y en output/Analisis_resultados.md. No se modificaron hiperparámetros ni umbral según la reserva.

## Cobertura de la rúbrica

| Rubro | Evidencia |
|---|---|
| Documentación | README y output/pdf/Manual_Tarea_3.pdf |
| Datos de entrada | Sección 2, data/Fuente.json y diccionario |
| Carga y limpieza | Sección 2, esquema explícito, diagnóstico y pruebas |
| Exploración | Sección 5, estadísticas, histogramas y Pearson |
| Escalado | Secciones 6 y 7, StandardScaler dentro de Pipeline |
| Escritura en PostgreSQL | Sección 3, tarea3 y relectura JDBC |
| Dos modelos y K-fold | Sección 6, CrossValidator, grillas y entrenamiento |
| Evaluación y persistencia | Secciones 8 y 9, métricas y modelo1/modelo2 |
| Análisis | Sección 10, errores, comparación y limitaciones |

La publicación de enlaces, la grabación y el envío no forman parte de estas verificaciones locales.
