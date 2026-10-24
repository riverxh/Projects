"""Operaciones Spark de carga, calidad, partición, modelado y evaluación."""
import os
from functools import reduce
from pathlib import Path

from pyspark.sql import SparkSession, Window, functions as F, types as T
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.functions import vector_to_array

COLUMNAS = ["id", "edad", "gasto_mensual", "tickets_soporte", "meses_cliente", "usa_app", "etiqueta"]
ATRIBUTOS = COLUMNAS[1:-1]
SEMILLA = 27
FOLDS = 4
ESQUEMA = T.StructType([
    T.StructField("id", T.StringType(), True),
    T.StructField("edad", T.IntegerType(), True),
    T.StructField("gasto_mensual", T.DoubleType(), True),
    T.StructField("tickets_soporte", T.IntegerType(), True),
    T.StructField("meses_cliente", T.IntegerType(), True),
    T.StructField("usa_app", T.IntegerType(), True),
    T.StructField("etiqueta", T.IntegerType(), True),
])


def iniciar_spark():
    return (SparkSession.builder.appName("T3-Abandono-Clientes")
            .master("local[2]")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.default.parallelism", "2")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())


def leer_csv(spark, ruta):
    esquema = T.StructType(ESQUEMA.fields + [T.StructField("_corrupt_record", T.StringType(), True)])
    return (spark.read.schema(esquema).option("header", True)
            .option("mode", "PERMISSIVE").option("columnNameOfCorruptRecord", "_corrupt_record")
            .csv(str(ruta)))


def limpiar_datos(entrada):
    """Rechaza nulos/valores inválidos y todos los ID con versiones contradictorias."""
    df = entrada.withColumn("id", F.trim("id"))
    reglas = [F.col(c).isNotNull() for c in COLUMNAS]
    reglas += [F.length("id") > 0, F.col("edad") > 0, F.col("gasto_mensual") >= 0,
               ~F.isnan("gasto_mensual"), F.abs(F.col("gasto_mensual")) != float("inf"),
               F.col("tickets_soporte") >= 0, F.col("meses_cliente") >= 0,
               F.col("usa_app").isin(0, 1), F.col("etiqueta").isin(0, 1)]
    if "_corrupt_record" in df.columns:
        reglas.append(F.col("_corrupt_record").isNull())
    valido = reduce(lambda a, b: a & b, reglas)
    correctos = df.filter(valido).select(*COLUMNAS)
    unicos = correctos.dropDuplicates(COLUMNAS)
    conflictos = unicos.groupBy("id").count().filter(F.col("count") > 1).select("id")
    limpio = unicos.join(conflictos, "id", "left_anti").select(*COLUMNAS)
    diagnostico = {
        "filas_entrada": df.count(), "filas_validas_antes_duplicados": correctos.count(),
        "filas_unicas_validas": unicos.count(), "identificadores_conflictivos": conflictos.count(),
        "filas_limpias": limpio.count(),
    }
    diagnostico["filas_invalidas"] = diagnostico["filas_entrada"] - diagnostico["filas_validas_antes_duplicados"]
    diagnostico["duplicados_exactos_eliminados"] = diagnostico["filas_validas_antes_duplicados"] - diagnostico["filas_unicas_validas"]
    diagnostico["filas_conflictivas_eliminadas"] = diagnostico["filas_unicas_validas"] - diagnostico["filas_limpias"]
    return limpio, diagnostico


def separar_reserva(df, semilla=SEMILLA):
    """ID estable asigna aproximadamente 20% a reserva; no depende del orden JDBC."""
    asignado = df.withColumn("__reserva", F.pmod(F.xxhash64("id", F.lit(semilla)), F.lit(100)) < 20)
    return (asignado.filter(~F.col("__reserva")).drop("__reserva"),
            asignado.filter(F.col("__reserva")).drop("__reserva"))


def agregar_folds(df, k=FOLDS, semilla=SEMILLA):
    if k < 2:
        raise ValueError("K debe ser al menos dos")
    if any(r["count"] < k for r in df.groupBy("etiqueta").count().collect()):
        raise ValueError("Cada clase necesita al menos K registros")
    ventana = Window.partitionBy("etiqueta").orderBy(F.xxhash64("id", F.lit(semilla)), "id")
    return df.withColumn("__fold", F.pmod(F.row_number().over(ventana) - 1, F.lit(k)).cast("int"))


def parametros_jdbc():
    return {
        "url": f"jdbc:postgresql://{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'tarea3')}",
        "user": os.getenv("POSTGRES_USER", "estudiante"),
        "password": os.getenv("POSTGRES_PASSWORD", "tarea3_local"),
        "driver": "org.postgresql.Driver",
    }


def escribir_tabla(df, nombre):
    if nombre not in {"tarea3", "modelo1", "modelo2"}:
        raise ValueError("Tabla no permitida")
    (df.write.format("jdbc").options(**parametros_jdbc()).option("dbtable", nombre)
     .option("batchsize", "1000").option("numPartitions", "2").mode("overwrite").save())


def leer_tabla(spark, nombre):
    if nombre not in {"tarea3", "modelo1", "modelo2"}:
        raise ValueError("Tabla no permitida")
    return spark.read.format("jdbc").options(**parametros_jdbc()).option("dbtable", nombre).load()


def construir_validadores():
    assembler = VectorAssembler(inputCols=ATRIBUTOS, outputCol="features_originales", handleInvalid="error")
    scaler = StandardScaler(inputCol="features_originales", outputCol="features", withMean=True, withStd=True)
    lr = LogisticRegression(featuresCol="features", labelCol="etiqueta", maxIter=100, tol=1e-6, standardization=False)
    rf = RandomForestClassifier(featuresCol="features", labelCol="etiqueta", numTrees=40, seed=SEMILLA,
                                featureSubsetStrategy="sqrt", maxBins=32)
    opciones = [
        ("modelo1", "Regresión logística", lr, ParamGridBuilder().addGrid(lr.regParam, [0.01, 0.1]).addGrid(lr.elasticNetParam, [0.0, 0.5]).build()),
        ("modelo2", "Bosque aleatorio", rf, ParamGridBuilder().addGrid(rf.maxDepth, [4, 8]).addGrid(rf.minInstancesPerNode, [2, 10]).build()),
    ]
    evaluador = BinaryClassificationEvaluator(labelCol="etiqueta", metricName="areaUnderROC")
    return [{"tabla": tabla, "nombre": nombre, "parametros": grid,
             "validador": CrossValidator(estimator=Pipeline(stages=[assembler, scaler, clf]),
                 estimatorParamMaps=grid, evaluator=evaluador, numFolds=FOLDS, foldCol="__fold",
                 seed=SEMILLA, parallelism=1, collectSubModels=False)}
            for tabla, nombre, clf, grid in opciones]


def evaluar(predicciones):
    filas = predicciones.groupBy("etiqueta", "prediction").count().collect()
    matriz = {(int(r["etiqueta"]), int(r["prediction"])): r["count"] for r in filas}
    tn, fp = matriz.get((0, 0), 0), matriz.get((0, 1), 0)
    fn, tp = matriz.get((1, 0), 0), matriz.get((1, 1), 0)
    n = tn + fp + fn + tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    ev = BinaryClassificationEvaluator(labelCol="etiqueta")
    return {"n": n, "auc_roc": ev.setMetricName("areaUnderROC").evaluate(predicciones),
            "auc_pr": ev.setMetricName("areaUnderPR").evaluate(predicciones),
            "accuracy": (tp + tn) / n if n else 0.0, "precision_positiva": precision,
            "recall_positivo": recall, "f1_positivo": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "tn": tn, "fp": fp, "fn": fn, "tp": tp}


def tabla_predicciones(df):
    return df.select(*COLUMNAS, F.col("prediction").cast("int").alias("prediccion"))


def curvas_agrupadas(predicciones):
    """Como máximo 101 grupos llegan al driver; las observaciones se agregan en Spark."""
    datos = (predicciones.withColumn("probabilidad", vector_to_array("probability")[1])
             .withColumn("grupo", F.floor(F.col("probabilidad") * 100).cast("int"))
             .groupBy("grupo").agg(F.sum("etiqueta").alias("positivos"),
                                  F.sum(1 - F.col("etiqueta")).alias("negativos")))
    return [r.asDict() for r in datos.orderBy(F.desc("grupo")).collect()]


def comprobar_tablas(spark, fuente, reserva, esperado1, esperado2):
    reporte = {}
    for nombre, esperado in [("tarea3", fuente), ("modelo1", esperado1), ("modelo2", esperado2)]:
        obtenido = leer_tabla(spark, nombre).select(*esperado.columns)
        distinto = esperado.exceptAll(obtenido).count() + obtenido.exceptAll(esperado).count()
        assert distinto == 0, f"Contenido distinto en {nombre}"
        assert obtenido.count() == obtenido.select("id").distinct().count(), f"ID repetido en {nombre}"
        assert obtenido.columns == esperado.columns
        reporte[nombre] = {"filas": obtenido.count(), "columnas": obtenido.columns, "diferencias": distinto}
    assert esperado1.select(*COLUMNAS).exceptAll(reserva.select(*COLUMNAS)).count() == 0
    assert esperado2.select(*COLUMNAS).exceptAll(reserva.select(*COLUMNAS)).count() == 0
    assert esperado1.count() == esperado2.count() == reserva.count()
    return reporte
