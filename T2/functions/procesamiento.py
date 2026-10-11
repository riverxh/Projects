"""Transformaciones de T2. Generado con ayuda de IA; decisiones en README.md."""

import math
from pyspark.sql import DataFrame, Window, functions as F
from .esquemas import ENTRADA


def leer_json(spark, rutas):
    """Lee documentos multilínea; rechaza JSON malformado y message ausente."""
    if isinstance(rutas, str):
        rutas = [rutas]
    if not rutas:
        raise ValueError("Se requiere al menos una ruta JSON.")
    raw = (spark.read.schema(ENTRADA).option("multiLine", True)
           .option("mode", "FAILFAST").json(list(rutas)))
    if raw.where(F.col("message").isNull()).limit(1).count():
        raise ValueError("Hay un documento sin objeto message.")
    return proyectar(raw)


def proyectar(raw):
    """Mantiene una fila por documento y las estructuras anidadas completas."""
    return raw.select(
        F.col("message.DOI").alias("doi"),
        F.col("message.author").alias("author"),
        F.col("message.institution").alias("inst"),
        F.col("message.group-title").alias("groupTitle"),
        F.col("message.created.date-time").alias("createdDate"),
        F.col("message.prefix").alias("prefix"),
        F.col("message.reference").alias("reference"),
        F.col("message.link").alias("link"),
        F.col("message.subtype").alias("subtype"),
    )


def articulos_por_mes(articulos: DataFrame):
    """Cuenta documentos; fechas ausentes/inválidas quedan en el grupo nulo."""
    fecha = F.try_to_timestamp(F.col("createdDate"))
    return (articulos.select(
        F.year(fecha).alias("created_year"),
        F.month(fecha).alias("created_month"),
    ).groupBy("created_year", "created_month")
        .agg(F.count(F.lit(1)).alias("total_articles"))
        .orderBy("created_year", "created_month"))


def articulos_por_grupo(articulos: DataFrame):
    """Cuenta DOI distintos no vacíos por grupo; mantiene el grupo nulo."""
    identificador = F.when(
        F.length(F.trim(F.col("doi"))) > 0, F.col("doi")
    )
    return (articulos.groupBy(F.col("groupTitle").alias("group_title"))
            .agg(F.countDistinct(identificador).alias("total"))
            .orderBy(F.desc("total"), F.asc("group_title")))


def personas_por_articulo(articulos: DataFrame):
    """Expande autores; un nombre repetido en un artículo contribuye una vez."""
    autores = F.filter(F.col("author"), lambda autor: autor.isNotNull())

    def nombre(autor):
        texto = F.trim(F.concat_ws(" ", autor["given"], autor["family"]))
        return F.when(F.length(texto) == 0, F.lit("unknown")).otherwise(texto)

    nombres = F.array_distinct(F.transform(autores, nombre))
    return articulos.withColumn("full_name", F.explode(nombres))


def areas_por_persona(articulos: DataFrame):
    personas = personas_por_articulo(articulos)
    grupo = F.when(F.length(F.trim(F.col("groupTitle"))) > 0, F.col("groupTitle"))
    return (personas.groupBy("full_name")
            .agg(F.sort_array(F.collect_set(grupo)).alias("research_areas"))
            .withColumn("total", F.size("research_areas"))
            .orderBy(F.desc("total"), F.asc("full_name")))


def referencias_por_persona(articulos: DataFrame, incluir_ceros=False,
                           conteo="distinct-doi", incluir_unknown=False):
    """Conteo configurable: distinct-doi reproduce el ejemplo Florian=2701.

    entries cuenta todas las entradas; ninguno cuenta citas recibidas.
    """
    if conteo not in ("distinct-doi", "entries"):
        raise ValueError("Modo de conteo de referencias desconocido.")
    validas = F.filter(
        F.col("reference"),
        lambda ref: ref.isNotNull() & ref["DOI"].isNotNull()
        & (F.length(F.trim(ref["DOI"])) > 0),
    )
    base = articulos.withColumn("_referencias_validas", validas)
    personas = personas_por_articulo(base)
    if not incluir_unknown:
        personas = personas.where(F.col("full_name") != "unknown")
    if conteo == "distinct-doi":
        referencias = personas.select("full_name", F.explode("_referencias_validas").alias("_ref"))
        resultado = referencias.groupBy("full_name").agg(
            F.countDistinct(F.col("_ref.DOI")).alias("total_references")
        )
        if incluir_ceros:
            resultado = (personas.select("full_name").distinct()
                         .join(resultado, "full_name", "left")
                         .fillna({"total_references": 0}))
    else:
        cantidad = F.when(F.col("_referencias_validas").isNull(), F.lit(0)).otherwise(F.size("_referencias_validas"))
        resultado = (personas.groupBy("full_name")
                     .agg(F.sum(cantidad).cast("long").alias("total_references")))
    if not incluir_ceros:
        resultado = resultado.where(F.col("total_references") > 0)
    return resultado


def persona_con_mas_referencias(totales: DataFrame):
    """Desempata por nombre ascendente; población vacía produce cero filas."""
    return totales.orderBy(F.desc("total_references"), F.asc("full_name")).limit(1)


def percentiles(totales: DataFrame, metodo="continuous"):
    """Devuelve una fila con p25/p50/p75. Vacío: tres valores nulos.

    continuous: interpolación exacta de Spark; nearest-rank: rango ceil(p*n).
    Ambas son decisiones configurables, no aclaraciones confirmadas del docente.
    """
    probabilidades = (0.25, 0.5, 0.75)
    if metodo == "continuous":
        valores = totales.agg(F.percentile("total_references", list(probabilidades)).alias("_p"))
        return valores.select(*[
            F.col("_p")[i].alias(f"p{int(p * 100)}")
            for i, p in enumerate(probabilidades)
        ])
    if metodo != "nearest-rank":
        raise ValueError("Método de percentil desconocido.")
    valores = totales.where(F.col("total_references").isNotNull())
    n = valores.count()
    if not n:
        return valores.agg(*[
            F.max(F.lit(None).cast("double")).alias(f"p{int(p * 100)}")
            for p in probabilidades
        ])
    ordenados = valores.withColumn(
        "_rango", F.row_number().over(Window.orderBy("total_references", "full_name"))
    )
    return ordenados.agg(*[
        F.max(F.when(F.col("_rango") == math.ceil(p * n),
                     F.col("total_references").cast("double"))).alias(f"p{int(p * 100)}")
        for p in probabilidades
    ])


def escribir_tabla(tabla, ruta, formato, modo="errorifexists", encabezado=True):
    """Produce un archivo de datos por tabla, además de metadatos de Spark."""
    escritor = tabla.coalesce(1).write.mode(modo)
    if formato == "csv":
        escritor.option("header", encabezado).option("nullValue", "null").csv(str(ruta))
    elif formato == "json":
        escritor.option("ignoreNullFields", False).json(str(ruta))
    else:
        raise ValueError("Formato de tabla no soportado.")
