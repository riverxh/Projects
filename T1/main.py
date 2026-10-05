"""Tarea 1: carga, unión, agregaciones y dos rankings por provincia."""

import os
import sys

from pyspark.sql import SparkSession

from functions.functions import (
    calculate_daily_average, calculate_daily_totals, calculate_day_totals,
    calculate_province_totals, calculate_total_kilometers,
    get_top_cyclists_by_daily_average, get_top_cyclists_by_total_km,
    join_data, load_activities, load_cyclists, load_routes,
)


def validate_arguments(arguments):
    """Validaciones propuestas en el FAQ: cantidad, extensión y existencia."""
    if len(arguments) != 3:
        raise ValueError(
            "Uso: spark-submit main.py data/ciclista.csv data/ruta.csv data/actividad.csv"
        )
    for file_path in arguments:
        if not file_path.lower().endswith(".csv"):
            raise ValueError("El archivo debe tener extensión .csv: " + file_path)
        if not os.path.isfile(file_path):
            raise ValueError("No existe el archivo: " + file_path)


def show_result(title, dataframe):
    print("\n" + title)
    dataframe.show(dataframe.count(), False)


def main():
    validate_arguments(sys.argv[1:])
    spark = SparkSession.builder.appName("Tarea1").master("local[*]").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    try:
        cyclists_df = load_cyclists(spark, sys.argv[1])
        routes_df = load_routes(spark, sys.argv[2])
        activities_df = load_activities(spark, sys.argv[3])
        joined_df = join_data(cyclists_df, routes_df, activities_df)

        totals_df = calculate_total_kilometers(joined_df)
        province_df = calculate_province_totals(joined_df)
        dates_df = calculate_day_totals(joined_df)
        daily_df = calculate_daily_totals(joined_df)
        averages_df = calculate_daily_average(daily_df)

        show_result("CICLISTAS", cyclists_df.orderBy("cedula"))
        show_result("RUTAS", routes_df.orderBy("codigo_ruta"))
        show_result("ACTIVIDADES", activities_df.orderBy("cedula", "fecha", "codigo_ruta"))
        show_result("DATOS UNIDOS", joined_df.orderBy("cedula", "fecha", "codigo_ruta"))
        show_result("TOTAL POR PERSONA", totals_df.orderBy("cedula"))
        show_result("TOTAL POR PROVINCIA", province_df.orderBy("provincia"))
        show_result("TOTAL POR DIA", dates_df.orderBy("fecha"))
        show_result("TOTAL POR PERSONA Y DIA", daily_df.orderBy("cedula", "fecha"))
        show_result("PROMEDIO POR DIA CON ACTIVIDAD", averages_df.orderBy("cedula"))
        show_result("TOP 5 POR PROVINCIA - TOTAL KM (INCLUYE EMPATES)",
                    get_top_cyclists_by_total_km(totals_df))
        show_result("TOP 5 POR PROVINCIA - PROMEDIO DIARIO (INCLUYE EMPATES)",
                    get_top_cyclists_by_daily_average(averages_df))
    finally:
        spark.stop()


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
