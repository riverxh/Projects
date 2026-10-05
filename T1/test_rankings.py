"""Rankings probados desde agregados preparados, sin lectura, unión ni sumas."""

from pyspark.sql.types import FloatType, IntegerType, StringType, StructField, StructType

from functions.functions import get_top_cyclists_by_total_km, get_top_cyclists_by_daily_average


def aggregated(spark, rows, metric="total_km"):
    schema = StructType([
        StructField("cedula", IntegerType()), StructField("nombre", StringType()),
        StructField("provincia", StringType()), StructField(metric, FloatType()),
    ])
    return spark.createDataFrame(rows, schema)


def test_top_five_is_per_province_not_global(spark_session):
    data = aggregated(spark_session, [
        (1, "A", "San José", 100.0), (2, "B", "San José", 90.0),
        (3, "C", "San José", 80.0), (4, "D", "San José", 70.0),
        (5, "E", "San José", 60.0), (6, "F", "San José", 50.0),
        (11, "G", "Alajuela", 8.0), (12, "H", "Alajuela", 7.0),
    ])
    result = get_top_cyclists_by_total_km(data)
    assert result.count() == 7
    assert result.filter(result["provincia"] == "San José").count() == 5
    assert result.filter(result["provincia"] == "Alajuela").count() == 2
    assert result.filter(result["cedula"] == 6).count() == 0
    assert result.filter(result["cedula"] == 5).head()["posicion"] == 5


def test_top_n_parameter_and_small_province(spark_session):
    data = aggregated(spark_session, [
        (1, "A", "San José", 10.0), (2, "B", "San José", 30.0),
        (3, "C", "San José", 20.0), (4, "D", "Cartago", 1.0),
    ])
    result = get_top_cyclists_by_total_km(data, 2).collect()
    assert [row["cedula"] for row in result] == [4, 2, 3]
    assert [row["posicion"] for row in result] == [1, 1, 2]


def test_dense_rank_includes_ties_at_cutoff(spark_session):
    data = aggregated(spark_session, [
        (1, "A", "San José", 100.0), (2, "B", "San José", 100.0),
        (3, "C", "San José", 90.0), (4, "D", "San José", 80.0),
    ])
    result = get_top_cyclists_by_total_km(data, 2).collect()
    assert [row["cedula"] for row in result] == [1, 2, 3]
    assert [row["posicion"] for row in result] == [1, 1, 2]


def test_daily_ranking_uses_supplied_average(spark_session):
    data = aggregated(spark_session, [
        (1, "Ana", "San José", 20.625), (2, "Luis", "San José", 50.0),
        (3, "Marta", "Cartago", 8.0),
    ], "promedio_diario")
    result = get_top_cyclists_by_daily_average(data, 1).collect()
    assert [row["cedula"] for row in result] == [3, 2]
    assert result[1]["promedio_diario"] == 50.0


def test_rankings_accept_empty_aggregates(spark_session):
    assert get_top_cyclists_by_total_km(aggregated(spark_session, [])).count() == 0
    assert get_top_cyclists_by_daily_average(
        aggregated(spark_session, [], "promedio_diario")
    ).count() == 0


def test_rankings_exclude_unknown_values_but_keep_zero(spark_session):
    data = aggregated(spark_session, [
        (1, "A", "San José", None), (2, "B", None, 10.0),
        (3, "C", "", 20.0), (4, "D", "San José", 0.0),
    ])
    result = get_top_cyclists_by_total_km(data).collect()
    assert len(result) == 1
    assert result[0]["cedula"] == 4
    assert result[0]["total_km"] == 0.0


def test_top_n_requires_positive_integer(spark_session):
    data = aggregated(spark_session, [(1, "A", "San José", 10.0)])
    for invalid_n in [0, -1, 1.5, "2", True]:
        try:
            get_top_cyclists_by_total_km(data, invalid_n)
        except ValueError:
            pass
        else:
            assert False, "Debió rechazar top_n=" + str(invalid_n)
