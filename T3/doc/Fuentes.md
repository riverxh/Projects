# Fuentes de la tarea 3

## Material del curso

1. **Enunciado Tarea 3 Spark ML**, archivo `2026-02-M4-T3.md`, dentro de `L5/T3.zip`, carpeta `T3`. Define entrada y esquema, limpieza, exploración, escalado, PostgreSQL, dos modelos, CrossValidator, reserva final, tablas y documentos. Fecha escrita de entrega: 26 de octubre de 2026 antes de las 19:00, hora de Costa Rica.
2. **Ejemplo de clasificación**, `T3/notebooks/Binary classification.ipynb`, y **dataset**, `T3/data/dataset.csv`, ambos del paquete L5/T3. Se retoman el caso de abandono, los atributos, la etiqueta, VectorAssembler y regresión logística. El CSV se conserva sin modificaciones y su SHA-256 está en `data/Fuente.json`. La versión entregada incorpora el esquema explícito, reglas de calidad, escalado, segundo clasificador, CV, PostgreSQL y verificaciones que exige el enunciado.
3. **Configuración de ejemplo**, Dockerfile y requirements del paquete L5/T3. Se conserva Java 17, Spark 3.5.1 y el conector PostgreSQL JDBC 42.7.3; se añade el servicio PostgreSQL y se fijan las dependencias usadas por esta tarea.


## Documentación técnica complementaria

- Apache Spark 3.5.1, [ML Tuning](https://spark.apache.org/docs/3.5.1/ml-tuning.html): CrossValidator, ParamGridBuilder y selección de parámetros.
- Apache Spark 3.5.1, [StandardScaler](https://spark.apache.org/docs/3.5.1/ml-features.html#standardscaler): centrado y escalado dentro del pipeline.
- Apache Spark 3.5.1, [JDBC Data Source](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html): lectura y escritura JDBC de DataFrames.

