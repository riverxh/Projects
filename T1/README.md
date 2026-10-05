# Tarea 1 - Big Data

**Autor:** Adrian Rojas Rivera. **Modalidad:** individual.

Programa en PySpark para integrar ciclistas, rutas y actividades, calcular totales por persona, provincia y fecha, y presentar dos rankings por provincia.


## Ejecución desde una copia nueva

Requisito: Docker instalado y en ejecución. Descomprimir el ZIP, abrir una terminal y entrar a la carpeta `T1` que contiene `Dockerfile`.

```bash
docker build -t tarea1-bigdata .
docker run --rm -it tarea1-bigdata /bin/bash
```

Dentro del contenedor:

```bash
source /opt/venv/bin/activate
cd /src
spark-submit main.py data/ciclista.csv data/ruta.csv data/actividad.csv
pytest
```

El programa imprime entradas, unión, agregados intermedios y los dos rankings. Las pruebas se descubren con el comando `pytest` sin opciones adicionales. También se pueden ejecutar directamente:

```bash
docker run --rm tarea1-bigdata spark-submit main.py data/ciclista.csv data/ruta.csv data/actividad.csv
docker run --rm tarea1-bigdata pytest
```

El Dockerfile se conserva del `Dockerfile.arm64` del curso, basado en Java 17 sobre Ubuntu Jammy. Usa una imagen base multiplataforma; la verificación de esta entrega se realizó en ARM64 con Python 3.10, Spark 4.2.0 y pytest 9.1.1.

## Entradas

Los tres CSV usan UTF-8, comas como separador, punto decimal y **ninguna fila de encabezado**. El orden es obligatorio:

| Archivo | Columnas |
|---|---|
| `ciclista.csv` | cédula numérica, nombre completo, provincia |
| `ruta.csv` | código numérico, nombre de ruta, kilómetros decimales |
| `actividad.csv` | código de ruta, cédula, fecha `YYYY-MM-DD` |

Se asumen identificadores únicos en los catálogos de ciclistas y rutas y fechas válidas con el formato indicado. Las repeticiones de actividades son recorridos independientes y se conservan. Los datos incluidos son ficticios: 17 ciclistas, 8 rutas y 21 actividades.

La lectura utiliza esquemas explícitos. La fecha se conserva como texto con formato ISO; se agrupa por la fecha completa, sin mezclar el mismo día de meses distintos. El programa valida cantidad de argumentos, extensión CSV y existencia de archivos.

## Procedimiento y criterios de cálculo

1. Cargar los tres CSV en funciones independientes.
2. Hacer dos uniones `left`: ciclistas con actividades por cédula y resultado con rutas por código. Seleccionar columnas para evitar identificadores duplicados.
3. Sumar kilómetros por persona, provincia y fecha. Una cuarta agregación produce el total por persona y día.
4. Promediar los totales diarios de cada persona: **se consideran los días con actividades de distancia conocida**. No se construye un calendario de días sin actividad, ya que el enunciado no fija un período. Este es el criterio adoptado y documentado para la entrega.
5. Aplicar `dense_rank` en una ventana por provincia, ordenada por la métrica descendente, como en el ejemplo del profesor. El límite N se aplica al rango e **incluye empates**, por lo que puede haber más de N personas.

Una persona sin actividades permanece en la unión con valores nulos y no participa en los agregados ni rankings de distancia, siguiendo el filtrado de kilómetros nulos del ejemplo. No se inventan ceros ni fechas. Cero kilómetros sí es una distancia conocida y participa en el cálculo. Se omiten las claves faltantes necesarias para cada agrupación; las distancias desconocidas se excluyen. En el ranking se requieren cédula, provincia y métrica conocidas.

`calculate_daily_average` recibe un DataFrame con **una fila por persona y día** y columna `km_dia`. Las funciones de ranking reciben agregados ya calculados; no rehacen las lecturas ni las uniones.

## Resultados de referencia

| Provincia | Total de kilómetros |
|---|---:|
| Alajuela | 300.25 |
| Cartago | 41.25 |
| San José | 342.50 |

Total general: **684.00 km**. Ana tiene 41.25 km en dos días activos: su promedio diario es **20.625 km**, no 13.75 km por actividad.

En San José, el top por total tiene las cédulas **4, 5, 6, 1, 7**; por promedio diario, **4, 6, 7, 5, 8**. En Alajuela, las cédulas 13 y 14 comparten el quinto rango y se incluyen ambas: aparecen seis personas. Marta, cédula 3, permanece en la unión sin actividades.

## Pruebas

Se incluyen **33 pruebas**: 3 de lectura, 5 de uniones, 5 de entradas vacías o sin correspondencia, 9 de agregaciones, 7 de rankings y 4 del programa/ejemplo completo.

Las agregaciones se prueban desde DataFrames intermedios y los rankings desde métricas preconstruidas, según la rúbrica. Se comprueban recorridos repetidos, homónimos, fechas de meses distintos, promedios diarios, nulos, distancias cero, empates, N variable y entradas vacías. Las comparaciones de filas se ordenan explícitamente cuando corresponde.

## Archivos

- `main.py`: argumentos y secuencia de ejecución.
- `functions/functions.py`: lecturas, uniones, agregaciones y rankings reutilizables.
- `conftest.py`: sesión de Spark para pytest.
- `test_*.py`: pruebas por responsabilidad.
- `data/`: ejemplo completo; `tests/data/`: ejemplo pequeño estable y CSV vacío.
- `Dockerfile`: configuración del entorno del curso.
- `doc/Manual.pdf`: manual de ejecución.
- `doc/Fuentes.md`: procedencia del código y adaptaciones.
