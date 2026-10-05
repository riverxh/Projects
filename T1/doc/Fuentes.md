# Material del curso usado en este proyecto

Este proyecto se desarrolla como ejercicio guiado de la Tarea 1. Se distinguen los ejemplos recibidos de las adaptaciones realizadas.

| Material | Uso en el avance actual |
|---|---|
| `2026-02-M4-T1.md` | Requisitos de entrada, archivos sin encabezado, modularidad, uniones, agregaciones y pruebas. |
| `FAQ.md` | Organización de la carpeta, funciones de carga, argumentos del programa, fixture de Spark y esquema de pruebas. |
| `3-Full-Container/basic/read.py` | Lectura CSV con esquema explícito. |
| `3-Full-Container/notebook-example/Spark_DataFrames_API.ipynb` | Inferencia de tipos, renombrado, visualización, filtros, ordenamiento y comprobación de filas. |
| `Tarea 1 Solución.zip`, compartido por el profesor según confirmó el usuario | `join_dfs` como base de `join_data`; datos en memoria con `createDataFrame`; variantes `left` e `inner` y comparación con DataFrames esperados. |

El ZIP no identifica una autoría individual en el documento de integrantes, por lo que no se atribuye a una persona concreta. Se conserva una copia original y su inventario de hashes en la carpeta de referencias del espacio de trabajo.

## Adaptaciones del ejemplo de unión

- `nombre_ciclista`, `codigo_de_ruta` y `kms` se llaman `nombre`, `codigo_ruta` y `kilometros` en este proyecto.
- `join_data` recibe ciclistas, rutas y actividades en el orden usado por el FAQ. Internamente une ciclistas con actividades y después incorpora rutas.
- Se usa por defecto `left` en ambas relaciones para conservar a las personas sin actividades, siguiendo la variante probada en `test_left_join` del ZIP.
- Se mantiene el filtro de kilómetros nulos de la variante `inner` del ejemplo.
- Se añadieron pruebas propias para recorridos repetidos y actividades vacías, casos relevantes para el enunciado.
- Se ordenan explícitamente las tablas que se comparan por filas; `orderBy` procede del cuaderno.

## Etapas finales

- Las agregaciones adaptan `groupBy` y `sum` de la función `aggregate` del ZIP. Se separan por responsabilidad para probar totales por persona, provincia y fecha.
- El promedio se calcula después de sumar por persona y día, siguiendo el TODO del FAQ para `calculate_daily_average`. Se emplea `mean`, ya presente en el ZIP. El criterio adoptado considera días con actividad y no inventa un calendario.
- El ranking adapta `top_n`, con `Window.partitionBy`, `dense_rank` y orden descendente. Se conservan empates y se documenta que puede haber más de N personas.
- Las rutas usan ahora `FloatType` con esquema explícito, como `main.py` del ZIP, para leer también archivos vacíos con las columnas correctas. Las fechas siguen como texto ISO, sin incorporar un procedimiento de conversión adicional.
- La validación de argumentos implementa la cantidad, existencia y extensión de archivos propuestas por el FAQ mediante Python estándar.
- El `Dockerfile` de la entrega es una copia idéntica de `3-Full-Container/Dockerfile.arm64`, compartido como material del curso.
- Se utilizan datos ficticios propios con punto decimal. Las pruebas se diseñaron para la rúbrica; no se copiaron los datos personales de ejemplo del ZIP.
