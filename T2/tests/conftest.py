"""Entorno de pruebas generado con ayuda de IA."""
import os
import sys
import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    os.environ["PYSPARK_PYTHON"] = sys.executable
    sesion = (SparkSession.builder.master("local[2]").appName("T2-pruebas")
              .config("spark.ui.enabled", "false")
              .config("spark.sql.shuffle.partitions", "2")
              .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    sesion.sparkContext.setLogLevel("ERROR")
    yield sesion
    sesion.stop()
