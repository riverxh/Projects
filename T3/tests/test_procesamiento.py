import pytest
from pyspark.sql import functions as F
from functions.procesamiento import ESQUEMA, COLUMNAS, limpiar_datos, separar_reserva, agregar_folds, tabla_predicciones, iniciar_spark


@pytest.fixture(scope="session")
def spark():
    sesion = iniciar_spark()
    sesion.sparkContext.setLogLevel("ERROR")
    yield sesion
    sesion.stop()


def test_limpieza_no_resuelve_conflictos_arbitrariamente(spark):
    filas = [(" a ", 30, 50.0, 1, 12, 1, 0), ("a", 30, 50.0, 1, 12, 1, 0),
             ("b", 20, 60.0, 2, 10, 0, 0), ("b", 20, 60.0, 2, 10, 0, 1),
             ("c", 0, 1.0, 0, 1, 0, 1), ("d", 25, -1.0, 0, 1, 0, 1),
             ("e", 25, 5.0, 0, 1, 2, 1), ("f", 25, float("nan"), 0, 1, 0, 1),
             ("g", 25, 5.0, 0, 1, 0, 2), (None, 25, 5.0, 0, 1, 0, 1)]
    limpio, d = limpiar_datos(spark.createDataFrame(filas, ESQUEMA))
    assert [r.id for r in limpio.collect()] == ["a"]
    assert d["filas_invalidas"] == 6
    assert d["duplicados_exactos_eliminados"] == 1
    assert d["filas_conflictivas_eliminadas"] == 2


def test_reserva_es_disjunta_completa_y_estable(spark):
    df = spark.createDataFrame([(str(i), 25, 5.0, 0, 1, i % 2, i % 2) for i in range(100)], ESQUEMA)
    train, test = separar_reserva(df)
    _, test_otra = separar_reserva(df.repartition(3))
    assert train.count() + test.count() == 100
    assert train.join(test, "id").count() == 0
    assert test.select("id").exceptAll(test_otra.select("id")).count() == 0
    assert 5 < test.count() < 40


def test_folds_equilibran_cada_clase_sin_omitir_registros(spark):
    df = spark.createDataFrame([(str(i), 25, 5.0, 0, 1, 0, i % 2) for i in range(24)], ESQUEMA)
    folds = agregar_folds(df, 4)
    assert folds.count() == 24
    assert {(r.etiqueta, r["__fold"], r["count"]) for r in folds.groupBy("etiqueta", "__fold").count().collect()} == {(c, k, 3) for c in [0, 1] for k in range(4)}


def test_folds_rechazan_clase_sin_datos_suficientes(spark):
    df = spark.createDataFrame([("a", 25, 5.0, 0, 1, 0, 0), ("b", 25, 5.0, 0, 1, 0, 1)], ESQUEMA)
    with pytest.raises(ValueError):
        agregar_folds(df, 4)


def test_salida_sql_contiene_solo_columnas_y_prediccion(spark):
    df = spark.createDataFrame([("a", 25, 5.0, 0, 1, 0, 1)], ESQUEMA)
    resultado = tabla_predicciones(df.withColumn("prediction", F.lit(1.0)).withColumn("features", F.array(F.lit(5.0))))
    assert resultado.columns == COLUMNAS + ["prediccion"]
    assert resultado.first().prediccion == 1
