"""Agregaciones probadas desde intermedios en memoria, sin efectuar uniones."""

from pyspark.sql.types import FloatType, IntegerType, StringType, StructField, StructType

from functions.functions import (
    calculate_total_kilometers, calculate_province_totals, calculate_day_totals,
    calculate_daily_totals, calculate_daily_average,
)


def joined_data(spark, rows):
    schema = StructType([
        StructField("cedula", IntegerType()), StructField("nombre", StringType()),
        StructField("provincia", StringType()), StructField("fecha", StringType()),
        StructField("kilometros", FloatType()),
    ])
    return spark.createDataFrame(rows, schema)


def example(spark):
    return joined_data(spark, [
        (1, "Ana", "San José", "2026-10-01", 10.5),
        (1, "Ana", "San José", "2026-10-01", 10.5),
        (1, "Ana", "San José", "2026-10-03", 20.25),
        (2, "Luis", "San José", "2026-10-01", 20.25),
        (2, "Luis", "San José", "2026-10-02", 10.5),
        (3, "Marta", "Cartago", None, None),
        (4, "Ana", "Cartago", "2026-10-02", 30.0),
    ])


def test_totals_by_cyclist_keep_repeats_and_distinguish_same_name(spark_session):
    result = calculate_total_kilometers(example(spark_session)).orderBy("cedula").collect()
    assert len(result) == 3
    assert result[0].asDict() == {"cedula": 1, "nombre": "Ana", "provincia": "San José", "total_km": 41.25}
    assert result[1]["total_km"] == 30.75
    assert result[2]["cedula"] == 4
    assert result[2]["total_km"] == 30.0


def test_totals_by_province(spark_session):
    result = calculate_province_totals(example(spark_session)).orderBy("provincia").collect()
    assert result[0].asDict() == {"provincia": "Cartago", "total_km": 30.0}
    assert result[1].asDict() == {"provincia": "San José", "total_km": 72.0}
    assert len(result) == 2


def test_totals_by_complete_date(spark_session):
    data = joined_data(spark_session, [
        (1, "Ana", "San José", "2026-10-01", 10.5),
        (2, "Luis", "San José", "2026-10-01", 20.25),
        (1, "Ana", "San José", "2026-11-01", 30.0),
    ])
    result = calculate_day_totals(data).orderBy("fecha").collect()
    assert len(result) == 2
    assert result[0].asDict() == {"fecha": "2026-10-01", "total_km": 30.75}
    assert result[1].asDict() == {"fecha": "2026-11-01", "total_km": 30.0}


def test_daily_totals_sum_multiple_activities(spark_session):
    result = calculate_daily_totals(example(spark_session))
    ana = result.filter(result["cedula"] == 1).orderBy("fecha").collect()
    assert len(ana) == 2
    assert ana[0]["km_dia"] == 21.0
    assert ana[1]["km_dia"] == 20.25
    assert result.filter(result["cedula"] == 3).count() == 0


def test_daily_average_starts_from_daily_intermediate(spark_session):
    daily = spark_session.createDataFrame([
        (1, "Ana", "San José", "2026-10-01", 21.0),
        (1, "Ana", "San José", "2026-10-03", 20.25),
        (2, "Luis", "San José", "2026-10-01", 50.0),
    ], ["cedula", "nombre", "provincia", "fecha", "km_dia"])
    result = calculate_daily_average(daily).orderBy("cedula").collect()
    assert len(result) == 2
    assert result[0]["promedio_diario"] == 20.625
    assert result[1]["promedio_diario"] == 50.0


def test_unknown_kilometers_do_not_become_zero_or_daily_observations(spark_session):
    data = joined_data(spark_session, [
        (1, "Ana", "San José", "2026-10-01", None),
        (1, "Ana", "San José", "2026-10-02", 20.0),
        (3, "Marta", "Cartago", None, None),
    ])
    totals = calculate_total_kilometers(data).collect()
    assert len(totals) == 1
    assert totals[0]["total_km"] == 20.0
    daily = calculate_daily_totals(data)
    assert daily.count() == 1
    assert calculate_daily_average(daily).head()["promedio_diario"] == 20.0


def test_zero_kilometers_is_a_real_activity(spark_session):
    data = joined_data(spark_session, [
        (1, "Ana", "San José", "2026-10-01", 0.0),
        (1, "Ana", "San José", "2026-10-02", 20.0),
    ])
    daily = calculate_daily_totals(data)
    assert daily.count() == 2
    assert calculate_daily_average(daily).head()["promedio_diario"] == 10.0


def test_aggregations_on_empty_intermediate(spark_session):
    empty = joined_data(spark_session, [])
    assert calculate_total_kilometers(empty).count() == 0
    assert calculate_province_totals(empty).count() == 0
    assert calculate_day_totals(empty).count() == 0
    daily = calculate_daily_totals(empty)
    assert daily.count() == 0
    assert calculate_daily_average(daily).count() == 0


def test_unknown_grouping_keys_are_not_invented(spark_session):
    data = joined_data(spark_session, [
        (1, "Ana", "", "2026-10-01", 5.0),
        (2, "Luis", "San José", "", 10.0),
        (3, "Marta", "Cartago", "2026-10-02", 20.0),
    ])
    assert calculate_province_totals(data).count() == 2
    assert calculate_day_totals(data).count() == 2
    assert calculate_daily_totals(data).count() == 2
