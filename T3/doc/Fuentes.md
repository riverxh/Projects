# Fuentes de la tarea 3

## Material del curso

1. **Enunciado Tarea 3 Spark ML**, archivo `2026-02-M4-T3.md`, dentro de `L5/T3.zip`, carpeta `T3`. Define entrada y esquema, limpieza, exploración, escalado, PostgreSQL, dos modelos, CrossValidator, reserva final, tablas y documentos. Fecha escrita de entrega: 26 de octubre de 2026 antes de las 19:00, hora de Costa Rica.
2. **Ejemplo de clasificación**, `T3/notebooks/Binary classification.ipynb`, y **dataset**, `T3/data/dataset.csv`, ambos del paquete L5/T3. Se retoman el caso de abandono, los atributos, la etiqueta, VectorAssembler y regresión logística. El CSV se conserva sin modificaciones y su SHA-256 está en `data/Fuente.json`. La versión entregada incorpora el esquema explícito, reglas de calidad, escalado, segundo clasificador, CV, PostgreSQL y verificaciones que exige el enunciado.
3. **Configuración de ejemplo**, Dockerfile y requirements del paquete L5/T3. Se conserva Java 17, Spark 3.5.1 y el conector PostgreSQL JDBC 42.7.3; se añade el servicio PostgreSQL y se fijan las dependencias usadas por esta tarea.
4. **L5, grabación `video1324764996.mp4`**, aproximadamente 00:00-00:11:10. Entrada y preparación en 00:00-00:02:40; K-fold en 00:02:40-00:06:10; predicciones y salidas del notebook en 00:06:10-00:08:20; repetición de cargas con overwrite en 00:08:20-00:11:10. K=4 es un ejemplo de la explicación y una decisión de esta solución, no un requisito fijo del curso.
5. **L4, grabación `video1908915064.mp4`**, aproximadamente 00:28:30-00:38:30 para conectores, DataFrames, materialización y relectura; 01:04:30-01:07:30 para VectorAssembler y regresión logística.
6. **L1, grabación `video2937477289.mp4`**, aproximadamente 00:07:07-00:09:03, e Introducción del curso, diapositivas 7 y 8, para identificación y formato de entrega.

Los intervalos de las grabaciones son aproximados. Las referencias anteriores son paráfrasis; los nombres de API y parámetros se cotejan con los archivos de ejemplo y la documentación oficial. El dataset no documenta población real, moneda del gasto ni mecanismo de generación. No se le atribuye un origen empresarial no indicado.

## Documentación técnica complementaria

- Apache Spark 3.5.1, [ML Tuning](https://spark.apache.org/docs/3.5.1/ml-tuning.html): CrossValidator, ParamGridBuilder y selección de parámetros.
- Apache Spark 3.5.1, [StandardScaler](https://spark.apache.org/docs/3.5.1/ml-features.html#standardscaler): centrado y escalado dentro del pipeline.
- Apache Spark 3.5.1, [JDBC Data Source](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html): lectura y escritura JDBC de DataFrames.

Las decisiones específicas del hash para la reserva, folds equilibrados, grillas de parámetros, métricas y pruebas se documentan en el notebook. No se atribuyen al docente como instrucciones textuales.
