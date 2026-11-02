from pathlib import Path
import json
from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]


def iniciar_spark():
    return (SparkSession.builder.appName("ConstruccionPoblacionCR").master("local[2]")
            .config("spark.sql.shuffle.partitions", "4").config("spark.ui.enabled", "false")
            .config("spark.driver.bindAddress", "0.0.0.0").getOrCreate())


def guardar_json(path, obj):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
