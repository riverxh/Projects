"""Funciones de la tarea, desarrolladas paso a paso desde los ejemplos de clase."""

from pyspark.sql.functions import col, dense_rank, mean, sum
from pyspark.sql.types import FloatType, IntegerType, StringType, StructField, StructType
from pyspark.sql.window import Window


def load_cyclists(spark, file_path):
    """Leer cédula, nombre y provincia desde un CSV sin encabezado."""
    csv_schema = StructType([
        StructField("cedula", IntegerType()),
        StructField("nombre", StringType()),
        StructField("provincia", StringType()),
    ])

    return spark.read.csv(file_path, schema=csv_schema, header=False)


def load_routes(spark, file_path):
    """Leer rutas con el esquema explícito y FloatType del ZIP del profesor."""
    csv_schema = StructType([
        StructField("codigo_ruta", IntegerType()),
        StructField("nombre_ruta", StringType()),
        StructField("kilometros", FloatType()),
    ])
    return spark.read.csv(file_path, schema=csv_schema, header=False)


def load_activities(spark, file_path):
    """Leer actividades conservando la fecha como texto YYYY-MM-DD."""
    csv_schema = StructType([
        StructField("codigo_ruta", IntegerType()),
        StructField("cedula", IntegerType()),
        StructField("fecha", StringType()),
    ])

    return spark.read.csv(file_path, schema=csv_schema, header=False)


def join_data(cyclists_df, routes_df, activities_df, type1="left", type2="left"):
    """Unir las entidades siguiendo join_dfs del ZIP facilitado por el profesor.

    La variante left conserva a los ciclistas sin actividades con campos nulos.
    Los nombres de columnas se adaptan a los CSV de este proyecto.
    """
    cyclists_activities_df = cyclists_df.alias("c").join(
        activities_df.alias("a"),
        cyclists_df["cedula"] == activities_df["cedula"],
        type1,
    ).select("c.*", "a.codigo_ruta", "a.fecha")

    joined_df = cyclists_activities_df.alias("ca").join(
        routes_df.alias("r"),
        cyclists_activities_df["codigo_ruta"] == routes_df["codigo_ruta"],
        type2,
    ).select("ca.*", "r.nombre_ruta", "r.kilometros")

    # Regla de la variante inner en el ejemplo del profesor.
    if type1 == "inner" or type2 == "inner":
        joined_df = joined_df.na.drop(subset=["kilometros"])

    return joined_df


def calculate_total_kilometers(joined_df):
    """Total por ciclista con kilómetros conocidos; la cédula distingue homónimos."""
    valid_df = joined_df.replace("", None).na.drop(subset=["cedula", "kilometros"])
    return valid_df.groupBy("cedula", "nombre", "provincia").agg(
        sum("kilometros").alias("total_km")
    )


def calculate_province_totals(joined_df):
    """Total por provincia; excluye distancias o provincias desconocidas."""
    valid_df = joined_df.replace("", None).na.drop(subset=["provincia", "kilometros"])
    return valid_df.groupBy("provincia").agg(sum("kilometros").alias("total_km"))


def calculate_day_totals(joined_df):
    """Total global por fecha completa, sin mezclar meses distintos."""
    valid_df = joined_df.replace("", None).na.drop(subset=["fecha", "kilometros"])
    return valid_df.groupBy("fecha").agg(sum("kilometros").alias("total_km"))


def calculate_daily_totals(joined_df):
    """Un registro por ciclista y día, sumando los recorridos repetidos."""
    valid_df = joined_df.replace("", None).na.drop(subset=["cedula", "fecha", "kilometros"])
    return valid_df.groupBy("cedula", "nombre", "provincia", "fecha").agg(
        sum("kilometros").alias("km_dia")
    )


def calculate_daily_average(daily_totals_df):
    """Promediar los totales diarios: una fila por persona y día con actividad."""
    valid_df = daily_totals_df.na.drop(subset=["cedula", "fecha", "km_dia"])
    return valid_df.groupBy("cedula", "nombre", "provincia").agg(
        mean("km_dia").alias("promedio_diario")
    )


def _top_by_province(aggregated_df, metric, top_n):
    """Adaptación de top_n del profesor: N niveles por provincia, incluidos empates."""
    if type(top_n) is not int or top_n < 1:
        raise ValueError("top_n debe ser un entero mayor que cero")
    valid_df = aggregated_df.replace("", None).na.drop(subset=["cedula", "provincia", metric])
    province_window = Window.partitionBy("provincia").orderBy(col(metric).desc())
    ranked_df = valid_df.withColumn("posicion", dense_rank().over(province_window))
    # La cédula ordena la presentación, pero no rompe empates en la ventana.
    return ranked_df.filter(col("posicion") <= top_n).orderBy("provincia", "posicion", "cedula")


def get_top_cyclists_by_total_km(totals_df, top_n=5):
    """Ranking por provincia a partir de totales por ciclista ya calculados."""
    return _top_by_province(totals_df, "total_km", top_n)


def get_top_cyclists_by_daily_average(averages_df, top_n=5):
    """Ranking por provincia a partir de promedios diarios ya calculados."""
    return _top_by_province(averages_df, "promedio_diario", top_n)
