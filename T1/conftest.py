"""Sesión de Spark compartida por las pruebas, siguiendo el FAQ del curso."""

import pytest

from pyspark.sql import SparkSession


@pytest.fixture(scope="module")
def spark_session():
    spark = SparkSession.builder.appName("pytest-local-spark").master("local").getOrCreate()
    yield spark
    spark.stop()
