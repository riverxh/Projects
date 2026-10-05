"""Pruebas de lectura de los tres CSV ficticios de este avance."""

from functions.functions import load_activities, load_cyclists, load_routes


def test_load_cyclists(spark_session):
    cyclists_df = load_cyclists(spark_session, "tests/data/ciclista.csv")

    assert cyclists_df.columns == ["cedula", "nombre", "provincia"]
    assert cyclists_df.count() == 3

    cyclists = cyclists_df.orderBy("cedula").collect()
    assert cyclists[0].asDict() == {
        "cedula": 1, "nombre": "Ana Mora", "provincia": "San José"
    }
    assert cyclists[1].asDict() == {
        "cedula": 2, "nombre": "Luis Vega", "provincia": "San José"
    }
    assert cyclists[2].asDict() == {
        "cedula": 3, "nombre": "Marta Ruiz", "provincia": "Cartago"
    }


def test_load_routes(spark_session):
    routes_df = load_routes(spark_session, "tests/data/ruta.csv")

    assert routes_df.columns == ["codigo_ruta", "nombre_ruta", "kilometros"]
    assert routes_df.count() == 2

    routes = routes_df.orderBy("codigo_ruta").collect()
    assert routes[0].asDict() == {
        "codigo_ruta": 100, "nombre_ruta": "Ruta Centro", "kilometros": 10.5
    }
    assert routes[1].asDict() == {
        "codigo_ruta": 200, "nombre_ruta": "Ruta Montaña", "kilometros": 20.25
    }


def test_load_activities(spark_session):
    activities_df = load_activities(spark_session, "tests/data/actividad.csv")

    assert activities_df.columns == ["codigo_ruta", "cedula", "fecha"]
    assert activities_df.count() == 5

    # El enunciado permite recorrer la misma ruta varias veces en un mismo día.
    repeated_activities = activities_df.filter(
        (activities_df["codigo_ruta"] == 100)
        & (activities_df["cedula"] == 1)
        & (activities_df["fecha"] == "2026-10-01")
    )
    assert repeated_activities.count() == 2

    assert activities_df.filter(
        (activities_df["codigo_ruta"] == 200)
        & (activities_df["cedula"] == 1)
        & (activities_df["fecha"] == "2026-10-03")
    ).count() == 1

    assert activities_df.filter(
        (activities_df["codigo_ruta"] == 200)
        & (activities_df["cedula"] == 2)
        & (activities_df["fecha"] == "2026-10-01")
    ).count() == 1

    assert activities_df.filter(
        (activities_df["codigo_ruta"] == 100)
        & (activities_df["cedula"] == 2)
        & (activities_df["fecha"] == "2026-10-02")
    ).count() == 1
