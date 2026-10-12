# Validación observada — 11 de octubre de 2026

- Pruebas finales: `pytest -q` → **23 passed in 14.26s**.
- Ejecución real: `spark-submit --master 'local[2]' programa.py data/crossref --overwrite` → finalizó con código de salida 0.
- Documentos JSON leídos: **31 458**. Artículos de la nueva lectura Parquet: **31 458**.
- Ocho archivos de datos Parquet. Un archivo de datos por cada salida CSV/JSON; los metadatos de Spark son adicionales.
- Máximo con configuración predeterminada: **Florian Krammer, 2701 DOI de referencias distintos**.
- P25: **21**; P50: **36**; P75: **64**. Método continuo exacto, personas identificadas con al menos una referencia con DOI.
- Se contrastaron meses, grupos, áreas por persona y su orden, máximo y percentiles mediante cálculos independientes en Python sobre `L2/crossref.zip`, sin usar las funciones del programa para construir los valores esperados.

La primera ejecución completa detectó un agotamiento de memoria al releer lotes grandes de Parquet. Se corrigió reduciendo los lotes a 128 filas, usando almacenamiento temporal en disco y evitando cachear todas las columnas del Parquet. La ejecución completa posterior terminó correctamente con el heap Java predeterminado de 1 GiB.

La comparación de referencias encontró una ambigüedad real: Florian Krammer tiene 3869 entradas con DOI en 100 artículos, pero 2701 DOI distintos. Se eligió la segunda interpretación porque reproduce el ejemplo del enunciado. La implementación permite contar todas las entradas con `--reference-count-mode entries`. También permite incluir `unknown` en referencias, incluir personas con cero y cambiar la definición de percentil. Estas opciones no representan aclaraciones confirmadas del docente.

Evidencia detallada:

- `Validacion_dataset.json`: comprobaciones de las salidas finales contra el ZIP.
- `Comprobacion_referencias.json`: conteo independiente y diez mayores totales.
- `../output/resumen_ejecucion.json`: configuración y resumen del programa.
