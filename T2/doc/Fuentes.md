# Fuentes y procedencia de T2

Documento preparado con ayuda de Codex el 11 de octubre de 2026.

- **Enunciado del curso:** L3/2026-02-M4-T2.md. Define las ocho salidas, el esquema Parquet, la relectura, las pruebas, el manual y la entrega.
- **Ejemplos de clase:** L2/notebook/biorxiv.ipynb. Referencia para JSON multilínea, `message`, selección, alias, autores, agrupaciones y escritura. La implementación de este repositorio no se atribuye al profesor.
- **Clase grabada:** L3/video1745679371.mp4. Explicación de T2 aproximadamente 01:02–01:10; relectura de Parquet 01:14:16–01:14:30, según el índice local de las clases.
- **Docker:** Full Container del curso, `Dockerfile.arm64`. El Dockerfile de T2 conserva esa base y fija `pyspark==4.2.0` y `pytest==9.1.1`. La nueva construcción no fue validada; el programa y las pruebas se ejecutaron en la imagen existente `bigdatafull`.
- **Apache Spark:** [JSON Files](https://spark.apache.org/docs/4.2.0/sql-data-sources-json.html) y [percentile](https://spark.apache.org/docs/4.2.0/api/python/reference/pyspark.sql/api/pyspark.sql.functions.percentile.html), consultados el 11 de octubre de 2026.
- **Política del curso:** Política para el Uso de Inteligencia Artificial Generativa, versión 1.0, septiembre de 2026.

## Participación de IA

Codex explicó la preparación del entorno y los errores y posteriormente generó el programa, los esquemas, las funciones, las pruebas, el README, el manual Word y el guion. El asistente ejecutó las pruebas y contrastó las métricas con cálculos independientes sobre el ZIP original. Los encabezados del código y la documentación identifican esa procedencia.

No se afirma que el código haya sido desarrollado exclusivamente por el estudiante ni que este haya completado una revisión personal que no consta. Las revisiones y modificaciones posteriores deben declararse según lo que realmente se realice. El reconocimiento de IA no elimina la condición de autoría del enunciado.

## Datos y evidencia

El dataset completo se obtiene de `L2/crossref.zip`, material del curso, y se extrae en `data/crossref`. No se publica el ZIP ni los 31 458 JSON en este repositorio. Las pruebas crean entradas pequeñas propias. `Validacion_dataset.json` y `Comprobacion_referencias.json` documentan el contraste observado; no sustituyen los datos de entrada.
