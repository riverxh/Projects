"""Argumentos y una comprobación completa, adicional a las pruebas independientes."""

from main import validate_arguments
from functions.functions import (
    load_cyclists, load_routes, load_activities, join_data,
    calculate_total_kilometers, calculate_daily_totals, calculate_daily_average,
    calculate_province_totals, calculate_day_totals,
    get_top_cyclists_by_total_km, get_top_cyclists_by_daily_average,
)


def test_valid_arguments():
    validate_arguments(["data/ciclista.csv", "data/ruta.csv", "data/actividad.csv"])


def test_wrong_argument_count():
    try:
        validate_arguments(["data/ciclista.csv"])
    except ValueError as error:
        assert "Uso:" in str(error)
    else:
        assert False, "Debió exigir los tres archivos"


def test_missing_file_and_wrong_extension():
    for path, expected in [("no_existe.csv", "No existe"), ("main.py", "extensión")]:
        try:
            validate_arguments([path, "data/ruta.csv", "data/actividad.csv"])
        except ValueError as error:
            assert expected in str(error)
        else:
            assert False, "Debió rechazar " + path


def test_full_example_known_totals_and_rankings(spark_session):
    cyclists = load_cyclists(spark_session, "data/ciclista.csv")
    routes = load_routes(spark_session, "data/ruta.csv")
    activities = load_activities(spark_session, "data/actividad.csv")
    assert cyclists.count() == 17
    assert routes.count() == 8
    assert activities.count() == 21

    joined = join_data(cyclists, routes, activities)
    assert joined.count() == 22
    totals = calculate_total_kilometers(joined)
    daily = calculate_daily_totals(joined)
    averages = calculate_daily_average(daily)
    provinces = calculate_province_totals(joined).orderBy("provincia").collect()
    dates = calculate_day_totals(joined).orderBy("fecha").collect()
    assert [row["total_km"] for row in provinces] == [300.25, 41.25, 342.5]
    assert [row["total_km"] for row in dates] == [601.5, 51.75, 30.75]
    assert totals.filter(totals["cedula"] == 1).head()["total_km"] == 41.25
    assert averages.filter(averages["cedula"] == 1).head()["promedio_diario"] == 20.625
    assert totals.filter(totals["cedula"] == 3).count() == 0

    top_total = get_top_cyclists_by_total_km(totals)
    top_average = get_top_cyclists_by_daily_average(averages)
    assert [r["cedula"] for r in top_total.filter(top_total["provincia"] == "San José").collect()] == [4, 5, 6, 1, 7]
    assert [r["cedula"] for r in top_average.filter(top_average["provincia"] == "San José").collect()] == [4, 6, 7, 5, 8]
    assert top_total.filter(top_total["provincia"] == "Alajuela").count() == 6
    assert top_total.count() == 13
