# Tarea 2 — Procesamiento de artículos Crossref

**Estudiante responsable:** Adrian Rojas Rivera. **Modalidad:** individual.

Repositorio: [riverxh/Projects, carpeta T2](https://github.com/riverxh/Projects/tree/main/T2).


## Archivos

- `programa.py`: recibe una o varias rutas JSON, convierte a Parquet, vuelve a leerlo y produce las métricas.
- `functions/esquemas.py`: tipos completos y explícitos del punto 1; los campos opcionales ausentes quedan nulos con el tipo correcto.
- `functions/procesamiento.py`: funciones de lectura, selección, cálculos y escritura.
- `tests/test_procesamiento.py`: casos de prueba con resultados esperados calculados independientemente; incluyen integración y repetición.
- `pytest.ini`: permite ejecutar `pytest` desde la raíz de T2.
- `output/resumen_ejecucion.json`: evidencia de la ejecución real, configuración y métricas resumidas. Se genera al ejecutar.
- [Manual de ejecución en Word](doc/Manual_Tarea_2.docx): entorno, instrucciones, esquema, salidas, decisiones y fuentes.
- [Guion del video en Word](doc/Guion_video_Tarea_2.docx): preparación, pantalla, narración y comandos para un objetivo de 6:30.
- [Fuentes y procedencia](doc/Fuentes.md) y [validación observada](doc/Validacion.md).
- `Dockerfile`: adaptación del Full Container ARM64 del curso; fija PySpark y pytest.

El cuaderno `exploracion_t2.ipynb` permanece en el equipo de trabajo; se omite de la copia publicada y no es necesario para ejecutar ni probar el programa.

## Entorno comprobado

Mac con Docker Desktop; imagen del curso `bigdatafull`; Python 3.10.12, Java 17.0.20.1, PySpark 4.2.0 y pytest 9.1.1. El programa usa Python, PySpark y su biblioteca estándar. No necesita findspark dentro de `spark-submit`. Para pruebas, activar el entorno del curso que contiene PySpark y pytest.

El programa limita a 128 filas los lotes de lectura Parquet y los lotes internos de caché. Guarda temporalmente la proyección JSON en disco y evita cachear todo el Parquet: cada métrica lee sus columnas necesarias. Estas medidas reducen la memoria requerida por los arreglos grandes de referencias en el entorno local de 1 GiB de heap Java.

## Preparar una copia descargada

Descargar este repositorio y abrir una Terminal en su carpeta `T2`. Obtener `crossref.zip` del material de L2 y extraer su carpeta `crossref` dentro de `data`:

```bash
mkdir -p data
unzip -q "/ruta/al/material/L2/crossref.zip" 'crossref/*.json' -d data
```

Cambiar `/ruta/al/material/L2/crossref.zip` por la ubicación real. El dataset completo y las salidas no se incluyen en GitHub. Las pruebas generan sus propios datos y no requieren el ZIP.

Para construir y abrir una imagen nueva desde la raíz de T2:

```bash
docker build -t tarea2-bigdata .
docker run --rm -it -v "$PWD:/t2" -w /t2 tarea2-bigdata /bin/bash
```

Dentro del contenedor:

```bash
source /opt/venv/bin/activate
cd /t2
pytest
spark-submit --master 'local[2]' programa.py data/crossref
```

La nueva construcción necesita Internet y **no fue ejecutada en esta validación**. El programa y las 23 pruebas se comprobaron en la imagen del curso `bigdatafull` ya existente, con las versiones indicadas. El Dockerfile procede del material de clase y sus cambios se reconocen en `doc/Fuentes.md`. `.dockerignore` excluye datasets, salidas y cachés del contexto de construcción.

## Ejecución en el contenedor ya creado

Jupyter puede seguir abierto. En una **nueva Terminal de tu Mac**, ejecutar:

```bash
docker exec -it bigdata-t2 /bin/bash
```

Ya **dentro del contenedor**, ejecutar:

```bash
source /opt/venv/bin/activate
cd /t2
pytest -q
```

Prueba manual con la muestra (salida separada del conjunto completo):

```bash
spark-submit --master 'local[2]' programa.py data/muestra/*.json --output output_muestra
```

Conjunto completo (31 458 JSON en esta copia del material):

```bash
spark-submit --master 'local[2]' programa.py data/crossref
```

También admite la forma del enunciado con múltiples archivos:

```bash
spark-submit --master 'local[2]' programa.py data/crossref/*.json
```

Usar el directorio evita el límite de longitud de argumentos de algunas consolas. Si alguna salida ya existe, el programa detiene la ejecución antes de escribir. Para repetir intencionalmente y reemplazar las ocho salidas:

```bash
spark-submit --master 'local[2]' programa.py data/crossref --overwrite
```

Consultar opciones:

```bash
spark-submit programa.py --help
```

Las rutas relativas parten del directorio donde se ejecuta el comando. `/t2` corresponde a `/Users/adrian/Downloads/Big Data/T2` en el Mac. Si el contenedor está detenido, iniciarlo antes con `docker start bigdata-t2` desde el Mac. `docker exec` requiere un contenedor en ejecución.

## Salidas

| Directorio dentro de `output` | Contenido |
|---|---|
| `crossref-parquet` | Las nueve columnas y sus tipos anidados del punto 1. |
| `articles_month_year` | CSV: `created_year`, `created_month`, `total_articles`; orden año/mes ascendente. |
| `research_group` | CSV: `group_title`, `total`; DOI distintos por grupo. |
| `research_areas_per_person` | JSON: `full_name`, `research_areas`, `total`; lista sin repetidos y orden por total descendente. |
| `person_most_references` | JSON con el máximo de `total_references`, un registro si existe población. |
| `percentil_25`, `percentil_50`, `percentil_75` | CSV con columna `total_references`. |

Cada salida CSV/JSON contiene un archivo de datos `part-*` y metadatos de Spark como `_SUCCESS`; no se deben confundir esos metadatos con archivos de datos adicionales. El Parquet puede contener varios archivos. Los JSON de salida siguen el formato habitual de Spark: un objeto por línea.

## Decisiones que deben explicarse y, cuando corresponda, confirmarse

Estas son decisiones de esta implementación, no aclaraciones del docente:

1. `createdDate` conserva el texto `message.created.date-time`. Las fechas se interpretan en UTC. Fechas nulas o inválidas permanecen en un grupo con año/mes nulos para no descartar documentos silenciosamente.
2. Los documentos se conservan como fueron leídos; no hay deduplicación global por DOI. El conteo mensual cuenta documentos. El conteo por grupo sí usa DOI distintos; los DOI nulos o en blanco no cuentan. Los grupos nulos se conservan en esa salida.
3. Los nombres se forman con `given` y `family`, separados por espacio y con `trim` exterior. Si el resultado está vacío, se usa `unknown`. No se identifica personas por ORCID ni se intenta resolver homónimos. Un autor nulo dentro de la lista se omite; una lista de autores ausente o vacía no crea personas ficticias.
4. El mismo nombre repetido en la lista de autores de un artículo contribuye una vez para ese documento. Los campos originales de autores se conservan completos en Parquet. Los nombres se desanidan solamente para las métricas de personas.
5. Las áreas de investigación excluyen grupos nulos/en blanco; conservan los nombres originales de los grupos válidos. Cada lista se ordena alfabéticamente para reproducibilidad. Una persona sin grupos válidos puede aparecer con lista vacía y total cero. La salida se ordena por total descendente y nombre ascendente.
6. Se filtran referencias con DOI no nulo y no vacío después de `trim`. **Por defecto se cuentan DOI distintos por persona, entre todos sus artículos** (`--reference-count-mode distinct-doi`). La verificación independiente del ZIP encontró para Florian Krammer 100 artículos, 3869 entradas con DOI y **2701 DOI distintos**, exactamente el valor citado en el enunciado. El texto no dice expresamente “referencias distintas”: esta configuración es una interpretación apoyada en ese ejemplo, pendiente de confirmación. `--reference-count-mode entries` cuenta todas las entradas, incluso DOI repetidos. No se divide entre coautores ni se usan `is-referenced-by-count` o `reference-count` para sustituir el cálculo. Se preservan las mayúsculas de los DOI; normalizarlas cambia el ejemplo del docente.
7. Por defecto, la distribución incluye solo personas con nombre identificable y al menos una referencia válida. El grupo sintético `unknown` permanece en áreas, como exige el punto 4, pero se excluye del máximo y percentiles porque agrupa autores diferentes sin nombre. El punto 5 no indica expresamente qué hacer con ese grupo: también es una interpretación pendiente de confirmar. `--include-unknown-references` permite incluirlo. `--include-zero-references` incluye personas con cero. Estas opciones afectan al máximo y a los percentiles.
8. En empate del máximo se escoge el nombre ascendente. Una población sin personas produce una salida JSON sin registros y percentiles nulos; no se inventa una persona ganadora.
9. Percentiles predeterminados: exactos y continuos/interpolados mediante `pyspark.sql.functions.percentile`, con índice `(n-1)*p`. `--percentile-method nearest-rank` usa el valor observado de rango `ceil(n*p)`. No se considera que uno de estos métodos esté confirmado por el enunciado. Para población vacía, los tres valores son nulos. **Los puntos 6–8 remiten al punto 4 aunque hablan de referencias; aquí se calculan sobre todos los totales de referencias por persona, antes de seleccionar el máximo.**
10. CSV con encabezados por defecto; `--no-csv-header` permite desactivarlos. En los CSV los nulos se representan con el texto `null`. Las columnas de percentiles se llaman `total_references`; el enunciado no detalla encabezados ni nombre de esa columna.
11. JSON malformado o tipos incompatibles: lectura `FAILFAST`. Documento sin objeto `message`: error explícito. Campos opcionales ausentes: nulos. Entrada vacía: error; el programa no anuncia éxito sin artículos.
12. La escritura no es una transacción: un fallo posterior a Parquet puede dejar salidas parciales. Corregir la causa y repetir con `--overwrite` para reemplazar las ocho salidas; revisar siempre el resumen de ejecución final.

Ejemplo para cambiar las decisiones de percentiles:

```bash
spark-submit --master 'local[2]' programa.py data/crossref --overwrite --include-zero-references --percentile-method nearest-rank
```

## Pruebas y verificación

Las pruebas cubren JSON multilínea, múltiples rutas, opcionales ausentes, esquema anidado, JSON inválido, message ausente, rutas inexistentes, fechas inválidas, autores múltiples/repetidos, nombres incompletos, listas vacías/nulas, DOI repetidos por grupo, referencias con/sin DOI, coautoría, referencia DOI repetida, personas con cero, empates, población vacía, percentiles continuos/discretos, un archivo CSV y su orden, relectura de Parquet, protección contra reemplazo y repetición sin duplicación acumulativa.

La comparación con el ejemplo de Florian Krammer es una comprobación del dataset, no un valor codificado ni un sustituto de las pruebas. La salida de este programa debe revisarse antes de cualquier entrega. Ninguna comprobación local garantiza coincidir con las pruebas ocultas del docente, especialmente en las decisiones ambiguas anteriores.

## Fuentes y procedencia

- Enunciado: en especial programa principal, esquema Parquet, ocho salidas y pruebas.
- Apache Spark, [JSON](https://spark.apache.org/docs/latest/sql-data-sources-json.html), [percentile](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.percentile.html).

## Resultado observado

**23 pruebas aprobadas**, 31 458 JSON y 31 458 filas releídas del Parquet. Máximo predeterminado: **Florian Krammer, 2701**; P25 **21.0**, P50 **36.0**, P75 **64.0**. Consultar `doc/Validacion.md` para el alcance y las interpretaciones pendientes.
