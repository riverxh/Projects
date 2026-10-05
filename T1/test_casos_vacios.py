"""Lecturas vacías con columnas estables y uniones sin correspondencias."""

from functions.functions import load_cyclists, load_routes, load_activities, join_data


def test_empty_cyclists_csv(spark_session):
    result = load_cyclists(spark_session, "tests/data/vacio.csv")
    assert result.count() == 0
    assert result.columns == ["cedula", "nombre", "provincia"]


def test_empty_routes_csv(spark_session):
    result = load_routes(spark_session, "tests/data/vacio.csv")
    assert result.count() == 0
    assert result.columns == ["codigo_ruta", "nombre_ruta", "kilometros"]


def test_empty_activities_csv(spark_session):
    result = load_activities(spark_session, "tests/data/vacio.csv")
    assert result.count() == 0
    assert result.columns == ["codigo_ruta", "cedula", "fecha"]


def test_join_with_no_cyclists(spark_session):
    cyclists = load_cyclists(spark_session, "tests/data/vacio.csv")
    routes = load_routes(spark_session, "tests/data/ruta.csv")
    activities = load_activities(spark_session, "tests/data/actividad.csv")
    assert join_data(cyclists, routes, activities).count() == 0


def test_join_with_no_routes_keeps_unknown_distances(spark_session):
    cyclists = load_cyclists(spark_session, "tests/data/ciclista.csv")
    routes = load_routes(spark_session, "tests/data/vacio.csv")
    activities = load_activities(spark_session, "tests/data/actividad.csv")
    result = join_data(cyclists, routes, activities)
    assert result.count() == 6
    assert result.na.drop(subset=["kilometros"]).count() == 0
