"""Pruebas independientes de CSV, siguiendo los DataFrames en memoria del ZIP."""

from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from functions.functions import join_data


def test_join_matches_cyclists_and_routes(spark_session):
    cyclists_df = spark_session.createDataFrame(
        [(1, "Ana Mora", "San José"), (2, "Luis Vega", "San José")],
        ["cedula", "nombre", "provincia"],
    )
    routes_df = spark_session.createDataFrame(
        [(100, "Ruta Centro", 10.5), (200, "Ruta Montaña", 20.25)],
        ["codigo_ruta", "nombre_ruta", "kilometros"],
    )
    activities_df = spark_session.createDataFrame(
        [(200, 1, "2026-10-03"), (100, 2, "2026-10-02")],
        ["codigo_ruta", "cedula", "fecha"],
    )

    result = join_data(cyclists_df, routes_df, activities_df)
    expected = spark_session.createDataFrame(
        [
            (1, "Ana Mora", "San José", 200, "2026-10-03", "Ruta Montaña", 20.25),
            (2, "Luis Vega", "San José", 100, "2026-10-02", "Ruta Centro", 10.5),
        ],
        ["cedula", "nombre", "provincia", "codigo_ruta", "fecha", "nombre_ruta", "kilometros"],
    )

    assert result.columns == expected.columns
    assert result.orderBy("cedula").collect() == expected.orderBy("cedula").collect()


def test_join_preserves_repeated_activities(spark_session):
    cyclists_df = spark_session.createDataFrame(
        [(1, "Ana Mora", "San José")], ["cedula", "nombre", "provincia"]
    )
    routes_df = spark_session.createDataFrame(
        [(100, "Ruta Centro", 10.5)], ["codigo_ruta", "nombre_ruta", "kilometros"]
    )
    activities_df = spark_session.createDataFrame(
        [(100, 1, "2026-10-01"), (100, 1, "2026-10-01")],
        ["codigo_ruta", "cedula", "fecha"],
    )

    result = join_data(cyclists_df, routes_df, activities_df)

    assert result.count() == 2
    assert result.filter(
        (result["cedula"] == 1)
        & (result["codigo_ruta"] == 100)
        & (result["fecha"] == "2026-10-01")
        & (result["kilometros"] == 10.5)
    ).count() == 2


def test_left_join_keeps_cyclist_without_activities(spark_session):
    cyclists_df = spark_session.createDataFrame(
        [(1, "Ana Mora", "San José"), (3, "Marta Ruiz", "Cartago")],
        ["cedula", "nombre", "provincia"],
    )
    routes_df = spark_session.createDataFrame(
        [(100, "Ruta Centro", 10.5)], ["codigo_ruta", "nombre_ruta", "kilometros"]
    )
    activities_df = spark_session.createDataFrame(
        [(100, 1, "2026-10-01")], ["codigo_ruta", "cedula", "fecha"]
    )

    result = join_data(cyclists_df, routes_df, activities_df)

    assert result.count() == 2
    assert result.filter(result["cedula"] == 3).head().asDict() == {
        "cedula": 3,
        "nombre": "Marta Ruiz",
        "provincia": "Cartago",
        "codigo_ruta": None,
        "fecha": None,
        "nombre_ruta": None,
        "kilometros": None,
    }


def test_left_join_with_empty_activities(spark_session):
    cyclists_df = spark_session.createDataFrame(
        [(3, "Marta Ruiz", "Cartago")], ["cedula", "nombre", "provincia"]
    )
    routes_df = spark_session.createDataFrame(
        [(100, "Ruta Centro", 10.5)], ["codigo_ruta", "nombre_ruta", "kilometros"]
    )
    activity_schema = StructType([
        StructField("codigo_ruta", IntegerType()),
        StructField("cedula", IntegerType()),
        StructField("fecha", StringType()),
    ])
    activities_df = spark_session.createDataFrame([], schema=activity_schema)

    result = join_data(cyclists_df, routes_df, activities_df)

    assert result.count() == 1
    assert result.head().asDict() == {
        "cedula": 3,
        "nombre": "Marta Ruiz",
        "provincia": "Cartago",
        "codigo_ruta": None,
        "fecha": None,
        "nombre_ruta": None,
        "kilometros": None,
    }


def test_inner_join_follows_example_filter_for_missing_kilometers(spark_session):
    cyclists_df = spark_session.createDataFrame(
        [(1, "Ana Mora", "San José"), (2, "Luis Vega", "San José"), (3, "Marta Ruiz", "Cartago")],
        ["cedula", "nombre", "provincia"],
    )
    routes_df = spark_session.createDataFrame(
        [(100, "Ruta Centro", 10.5), (200, "Ruta Montaña", None)],
        ["codigo_ruta", "nombre_ruta", "kilometros"],
    )
    activities_df = spark_session.createDataFrame(
        [(100, 1, "2026-10-01"), (200, 2, "2026-10-01")],
        ["codigo_ruta", "cedula", "fecha"],
    )

    result = join_data(cyclists_df, routes_df, activities_df, "inner", "inner")

    assert result.count() == 1
    assert result.head().asDict() == {
        "cedula": 1,
        "nombre": "Ana Mora",
        "provincia": "San José",
        "codigo_ruta": 100,
        "fecha": "2026-10-01",
        "nombre_ruta": "Ruta Centro",
        "kilometros": 10.5,
    }
