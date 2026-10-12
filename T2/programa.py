
import argparse
import json
from pathlib import Path
from pyspark import StorageLevel
from pyspark.sql import SparkSession, functions as F
from functions.procesamiento import (
    leer_json, articulos_por_mes, articulos_por_grupo, areas_por_persona,
    referencias_por_persona, persona_con_mas_referencias, percentiles, escribir_tabla,
)

DIRECTORIOS = (
    "crossref-parquet", "articles_month_year", "research_group",
    "research_areas_per_person", "person_most_references",
    "percentil_25", "percentil_50", "percentil_75",
)


def ejecutar(spark, rutas, salida="output", sobrescribir=False,
             incluir_ceros=False, metodo="continuous", encabezado=True,
             particiones=8, conteo="distinct-doi", incluir_unknown=False):
    """Ejecuta la cadena: JSON -> Parquet -> relectura -> ocho salidas."""
    if particiones < 1:
        raise ValueError("El número de particiones debe ser positivo.")
    if metodo not in ("continuous", "nearest-rank"):
        raise ValueError("Método de percentil desconocido.")
    if conteo not in ("distinct-doi", "entries"):
        raise ValueError("Modo de conteo de referencias desconocido.")
    destino = Path(salida).resolve()
    if not sobrescribir:
        existentes = [nombre for nombre in DIRECTORIOS if (destino / nombre).exists()]
        if existentes:
            raise FileExistsError("Ya existen salidas; usá --overwrite: " + ", ".join(existentes))
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    # Los arreglos de referencias pueden ser muy grandes. Lotes pequeños y
    # proyección de columnas evitan llenar el heap de 1 GiB del entorno local.
    spark.conf.set("spark.sql.parquet.columnarReaderBatchSize", "128")
    spark.conf.set("spark.sql.inMemoryColumnarStorage.batchSize", "128")
    modo = "overwrite" if sobrescribir else "errorifexists"
    origen = None
    articulos = None
    totales = None
    try:
        print("1/5 Lectura JSON con esquema explícito...", flush=True)
        origen = leer_json(spark, rutas).persist(StorageLevel.DISK_ONLY)
        cantidad = origen.count()
        if cantidad == 0:
            raise ValueError("La entrada no contiene artículos JSON.")
        print(f"2/5 Escritura de Parquet: {cantidad} documentos...", flush=True)
        origen.coalesce(particiones).write.mode(modo).parquet(str(destino / "crossref-parquet"))
        origen.unpersist(blocking=True)
        origen = None

        # Las métricas reciben EXCLUSIVAMENTE esta nueva lectura de Parquet.
        # No cachear los arreglos completos: cada métrica lee solamente sus
        # columnas necesarias desde Parquet mediante column pruning.
        articulos = spark.read.parquet(str(destino / "crossref-parquet"))
        releidos = articulos.count()
        if releidos != cantidad:
            raise RuntimeError("La cantidad de artículos cambió al releer Parquet.")
        print("3/5 Artículos por fecha, grupos y áreas por persona...", flush=True)
        escribir_tabla(articulos_por_mes(articulos), destino / "articles_month_year", "csv", modo, encabezado)
        escribir_tabla(articulos_por_grupo(articulos), destino / "research_group", "csv", modo, encabezado)
        escribir_tabla(areas_por_persona(articulos), destino / "research_areas_per_person", "json", modo)

        print("4/5 Referencias por persona, máximo y percentiles...", flush=True)
        totales = referencias_por_persona(
            articulos, incluir_ceros, conteo, incluir_unknown
        ).persist(StorageLevel.MEMORY_AND_DISK)
        personas = totales.count()
        maximo = persona_con_mas_referencias(totales)
        escribir_tabla(maximo, destino / "person_most_references", "json", modo)
        cuantiles = percentiles(totales, metodo).first().asDict()
        for p in (25, 50, 75):
            tabla = spark.createDataFrame([(cuantiles[f"p{p}"],)], "total_references double")
            escribir_tabla(tabla, destino / f"percentil_{p}", "csv", modo, encabezado)
        resumen = {
            "documentos_json": cantidad,
            "articulos_releidos_parquet": releidos,
            "personas_en_distribucion_referencias": personas,
            "maximo": [fila.asDict() for fila in maximo.collect()],
            "percentiles": cuantiles,
            "metodo_percentiles": metodo,
            "incluye_personas_con_cero_referencias": incluir_ceros,
            "conteo_referencias": conteo,
            "incluye_unknown_en_referencias": incluir_unknown,
            "csv_con_encabezado": encabezado,
            "zona_horaria": "UTC",
            "spark": spark.version,
            "origen_codigo": "Generado con ayuda de IA; ver README.md",
        }
        (destino / "resumen_ejecucion.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("5/5 Finalizado. Resumen: " + str(destino / "resumen_ejecucion.json"), flush=True)
        return resumen
    finally:
        for tabla in (origen, articulos, totales):
            if tabla is not None:
                tabla.unpersist()


def main():
    parser = argparse.ArgumentParser(description="T2: procesamiento Crossref con Apache Spark")
    parser.add_argument("rutas", nargs="+", help="Archivos JSON, patrones o carpetas de entrada")
    parser.add_argument("--output", default="output", help="Carpeta de salida; predeterminado: output")
    parser.add_argument("--overwrite", action="store_true", help="Reemplazar las ocho salidas existentes")
    parser.add_argument("--include-zero-references", action="store_true", help="Incluir personas sin referencias con DOI")
    parser.add_argument("--include-unknown-references", action="store_true", help="Incluir el grupo sintético unknown en referencias")
    parser.add_argument("--reference-count-mode", choices=("distinct-doi", "entries"), default="distinct-doi",
                        help="DOI distintos por persona (ejemplo Florian=2701) o todas las entradas")
    parser.add_argument("--percentile-method", choices=("continuous", "nearest-rank"), default="continuous")
    parser.add_argument("--no-csv-header", action="store_true", help="Escribir CSV sin encabezado")
    parser.add_argument("--parquet-partitions", type=int, default=8)
    args = parser.parse_args()
    spark = (SparkSession.builder.appName("T2-Crossref")
             .config("spark.sql.shuffle.partitions", "8")
             .config("spark.sql.files.openCostInBytes", "1048576")
             .config("spark.ui.enabled", "false").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    try:
        ejecutar(spark, args.rutas, args.output, args.overwrite,
                 args.include_zero_references, args.percentile_method,
                 not args.no_csv_header, args.parquet_partitions,
                 args.reference_count_mode, args.include_unknown_references)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
