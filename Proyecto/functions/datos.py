"""Extracción trazable de Excel y transformaciones de DataFrames Spark."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import re
import unicodedata

import openpyxl
from pyspark.sql import functions as F, types as T, Window

ROOT = Path(__file__).resolve().parents[1]
METRICAS = ["obras_total", "area_m2", "valor_miles_colones", "obras_nuevas", "area_nueva_m2",
            "valor_nueva_miles", "obras_ampliacion", "area_ampliacion_m2", "valor_ampliacion_miles",
            "obras_reparacion", "valor_reparacion_miles"]
GRUPOS = {"216": "203", "612": "601", "613": "607"}
NOMBRES_GRUPOS = {"203": "Grecia y Río Cuarto", "601": "Puntarenas y Monteverde", "607": "Golfito y Puerto Jiménez"}
PROVINCIAS = {"1": "San José", "2": "Alajuela", "3": "Cartago", "4": "Heredia", "5": "Guanacaste", "6": "Puntarenas", "7": "Limón"}


def normalizar(v):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode().lower())


def cargar_fuentes():
    manifest = json.loads((ROOT / "config/fuentes.json").read_text())
    for x in manifest["construccion"] + [manifest["poblacion"]] + manifest["textos"]:
        if hashlib.sha256((ROOT / x["archivo"]).read_bytes()).hexdigest() != x["sha256"]:
            raise ValueError(f"Original modificado: {x['archivo']}")
    return manifest


def extraer_poblacion(meta):
    path = ROOT / meta["archivo"]
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["C4"].iter_rows(values_only=True))
    out, catalogo, seen = [], {}, set()
    positions = []
    for i, row in enumerate(rows):
        if normalizar(row[0]) == "cantones":
            boundaries = {normalizar(v): j for j, v in enumerate(row) if normalizar(v) in ["total", "hombres", "mujeres"]}
            starts = sorted(boundaries.values()) + [len(row)]
            positions = []
            for label, start in boundaries.items():
                end = starts[starts.index(start) + 1]
                for j in range(start, end):
                    year = rows[i + 1][j]
                    if isinstance(year, int) and 2015 <= year <= 2024:
                        positions.append((label, j, year))
        elif isinstance(row[0], str) and re.match(r"^\d{3}_", row[0]):
            code, name = row[0].split("_", 1)
            catalogo[code] = name
            values = {}
            for label, j, year in positions:
                key = (code, year)
                values.setdefault(year, {"codigo_canton": code, "canton": name, "anio": year,
                                          "archivo": path.name, "hoja": "C4", "fila": i + 1, "fuente_url": meta["url"]})
                values[year][{"total": "poblacion", "hombres": "hombres", "mujeres": "mujeres"}[label]] = str(row[j])
                values[year][f"celda_{label}"] = f"{openpyxl.utils.get_column_letter(j + 1)}{i + 1}"
            for year, value in values.items():
                if (code, year) in seen:
                    raise ValueError(f"Población duplicada: {code}/{year}")
                seen.add((code, year)); out.append(value)
    wb.close()
    if len(catalogo) != 84 or len(out) != 840:
        raise ValueError(f"Cobertura inesperada de población: {len(catalogo)}, {len(out)}")
    return out, catalogo


def fila_construccion(row, anio, codigo, nombre, path, hoja, n, url, columnas):
    return {"anio": anio, "codigo_canton": codigo, "canton": nombre,
            **{k: None if v is None else str(v).strip() for k, v in zip(METRICAS, row[1:12])},
            "archivo": path.name, "hoja": hoja, "fila": n, "fuente_url": url,
            "columnas_metricas": json.dumps(dict(zip(METRICAS, [openpyxl.utils.get_column_letter(j + 1) for j in columnas])))}


def extraer_construccion(manifest, catalogo):
    names = {normalizar(v): k for k, v in catalogo.items()}
    names[normalizar("Vázquez de Coronado")] = "111"
    totals, details, national = [], [], []
    for meta in manifest:
        path = ROOT / meta["archivo"]
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sh = wb.worksheets[0]; rows = list(sh.iter_rows(values_only=True))
        year = meta["anio"]
        if not any(str(year) in str(c) for row in rows[:10] for c in row):
            raise ValueError("El año del cuadro no coincide con el inventario")
        starts = {}
        for row in rows[:20]:
            for j, value in enumerate(row):
                if normalizar(value) in ["totales", "construccion", "ampliacion", "reparacion"]:
                    starts[normalizar(value)] = j
        if len(starts) != 4:
            raise ValueError(f"Cabecera de métricas no reconocida {year}: {starts}")
        cols = ([starts['totales'] + k for k in range(3)] + [starts['construccion'] + k for k in range(3)]
                + [starts['ampliacion'] + k for k in range(3)] + [starts['reparacion'] + k for k in range(2)])
        label_col = starts['totales'] - 1
        canonical = lambda row: [row[label_col]] + [row[j] for j in cols]
        canton = None; name = None; category = None
        count = 0
        for i, row in enumerate(rows):
            label = str(row[label_col] or "").strip(); key = normalizar(label)
            if key == "costarica":
                national.append({"anio": year, **{k: float(v) for k, v in zip(METRICAS[:3], canonical(row)[1:4])}})
            if key in ["provincia", "costarica"]:
                canton = None; category = None
            if key == "canton":
                r = canonical(rows[i + 1]); name = str(r[0]).strip(); canton = names.get(normalizar(name))
                if not canton:
                    raise ValueError(f"Cantón sin equivalencia: {year}: {name}")
                totals.append(fila_construccion(r, year, canton, name, path, sh.title, i + 2, meta["url"], cols))
                count += 1; category = None
                continue
            # Saltar el total que ya se registró y todos los agregados nacionales/provinciales.
            if canton and i > 0 and normalizar(rows[i - 1][label_col]) == "canton":
                continue
            if canton and label and any(isinstance(v, (int, float)) for v in canonical(row)[1:12]):
                upper = label.isupper()
                if upper:
                    category = label
                d = fila_construccion(canonical(row), year, canton, name, path, sh.title, i + 1, meta["url"], cols)
                d.update({"destino": label, "categoria": category or "SIN CATEGORIA",
                          "nivel": "subtotal_categoria" if upper else "detalle",
                          "id": f"{year}-{canton}-{i + 1}"})
                details.append(d)
        wb.close()
        expected = 81 if year < 2019 else 82 if year < 2024 else 84
        if count != expected:
            raise ValueError(f"Conteo cantonal inesperado {year}: {count}")
    return totals, details, national


def schema_construccion(detalle=False):
    fields = [T.StructField("anio", T.IntegerType(), False), T.StructField("codigo_canton", T.StringType(), False), T.StructField("canton", T.StringType(), False)]
    fields += [T.StructField(m, T.StringType(), True) for m in METRICAS]
    fields += [T.StructField("archivo", T.StringType()), T.StructField("hoja", T.StringType()),
               T.StructField("fila", T.IntegerType()), T.StructField("fuente_url", T.StringType()), T.StructField("columnas_metricas", T.StringType())]
    if detalle:
        fields += [T.StructField(k, T.StringType()) for k in ["destino", "categoria", "nivel", "id"]]
    return T.StructType(fields)


def limpiar_construccion(df, exigir_totales=True):
    out = df
    for m in METRICAS:
        # Signos y ausencias se conservan en la extracción cruda; aquí permanecen nulos.
        # No se interpreta '-' o '.' como cero sin información adicional.
        pattern = r"^[+-]?\d+(\.\d+)?([Ee][+-]?\d+)?$"
        # N.D aparece en el detalle publicado de 2019. La única N aislada es una
        # anomalía de la celda K1413 de 2020, que se conserva cruda y queda nula.
        # No se infiere el conteo a partir de otras columnas ni se admite N fuera
        # de esa celda identificada.
        anomaly = F.lit(False)
        if "id" in out.columns and m == "obras_reparacion":
            anomaly = (F.col("id") == "2020-608-1413") & (F.trim(F.col(m)) == "N")
        unexpected = F.col(m).isNotNull() & ~F.trim(F.col(m)).isin("-", ".", "", "N.D") & ~F.trim(F.col(m)).rlike(pattern) & ~anomaly
        if out.filter(unexpected).limit(1).count():
            raise ValueError("Símbolo numérico inesperado en " + m)
        out = out.withColumn(m, F.when(F.trim(F.col(m)).rlike(pattern), F.col(m).cast("double")))
    bad = F.lit(False)
    for m in METRICAS:
        bad = bad | (F.col(m) < 0) | F.isnan(m)
    if exigir_totales:
        for m in METRICAS[:3]:
            bad = bad | F.col(m).isNull()
    for m in ["obras_total", "obras_nuevas", "obras_ampliacion", "obras_reparacion"]:
        bad = bad | (F.col(m) != F.floor(m))
    if out.filter(bad).limit(1).count():
        raise ValueError("Valores inválidos en construcción")
    for m in ["obras_total", "obras_nuevas", "obras_ampliacion", "obras_reparacion"]:
        out = out.withColumn(m, F.col(m).cast("long"))
    if exigir_totales:
        exigir_clave(out, ["codigo_canton", "anio"])
    return out


def exigir_clave(df, cols):
    if df.filter(F.expr(" OR ".join(f"`{k}` IS NULL" for k in cols))).limit(1).count():
        raise ValueError("Clave nula")
    if df.groupBy(*cols).count().filter("count > 1").limit(1).count():
        raise ValueError("Clave duplicada")


def agrupar_codigo(df):
    code = F.col("codigo_canton")
    expr = code
    for child, parent in GRUPOS.items():
        expr = F.when(code == child, F.lit(parent)).otherwise(expr)
    return df.withColumn("codigo_agrupacion", expr)


def asignar_provincia(df):
    """Conservar provincia también en destinos para los filtros comunes de Kibana."""
    lookup = F.create_map(*[F.lit(v) for pair in PROVINCIAS.items() for v in pair])
    out = df.withColumn("provincia", lookup[F.substring("codigo_canton", 1, 1)])
    if out.filter(F.col("provincia").isNull()).limit(1).count():
        raise ValueError("Código cantonal sin provincia reconocida")
    return out


def construir_integrado(construccion, poblacion, territorios):
    c = agrupar_codigo(construccion).groupBy("codigo_agrupacion", "anio").agg(
        *[F.sum(m).alias(m) for m in METRICAS],
        F.concat_ws(";", F.sort_array(F.collect_set("codigo_canton"))).alias("codigos_construccion"),
        F.concat_ws(";", F.sort_array(F.collect_list(F.concat_ws(":", "archivo", "hoja", F.col("fila").cast("string"))))).alias("origen_construccion"))
    p = agrupar_codigo(poblacion).groupBy("codigo_agrupacion", "anio").agg(
        *[F.sum(m).alias(m) for m in ["poblacion", "hombres", "mujeres"]],
        F.concat_ws(";", F.sort_array(F.collect_set("codigo_canton"))).alias("codigos_poblacion"),
        F.concat_ws(";", F.sort_array(F.collect_list(F.concat_ws(":", "archivo", "hoja", "celda_total")))).alias("origen_poblacion"))
    exigir_clave(c, ["codigo_agrupacion", "anio"]); exigir_clave(p, ["codigo_agrupacion", "anio"])
    if c.join(p, ["codigo_agrupacion", "anio"], "left_anti").count() or p.join(c, ["codigo_agrupacion", "anio"], "left_anti").count():
        raise ValueError("El cruce pierde registros")
    joined = c.join(p, ["codigo_agrupacion", "anio"], "inner").join(territorios, "codigo_agrupacion", "inner")
    joined = joined.withColumn("area_por_habitante", F.col("area_m2") / F.col("poblacion"))
    exigir_clave(joined, ["codigo_agrupacion", "anio"])
    return c, p, joined


def preparar(spark):
    manifest = cargar_fuentes()
    pop_rows, catalogo = extraer_poblacion(manifest["poblacion"])
    con_rows, det_rows, nat_rows = extraer_construccion(manifest["construccion"], catalogo)
    out = ROOT / "output"; out.mkdir(exist_ok=True)
    raw = ROOT / "data/preparados"; raw.mkdir(exist_ok=True)
    for name, rows in [("construccion_extraida", con_rows), ("poblacion_extraida", pop_rows), ("destinos_extraidos", det_rows)]:
        (raw / f"{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    audit = [{"id": r["id"], "archivo": r["archivo"], "fila": r["fila"], "campo": m, "original": r[m],
              "tratamiento": "nulo; no se infiere un valor numérico"}
             for r in det_rows for m in METRICAS if r[m] in ["N.D", "N"]]
    (out / "auditoria_signos.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    c = limpiar_construccion(spark.createDataFrame(con_rows, schema_construccion())).cache()
    d = asignar_provincia(limpiar_construccion(spark.createDataFrame(det_rows, schema_construccion(True)), False)).cache()
    ps = T.StructType([T.StructField(k, T.StringType()) for k in ["codigo_canton", "canton", "archivo", "hoja", "fuente_url", "poblacion", "hombres", "mujeres", "celda_total", "celda_hombres", "celda_mujeres"]] + [T.StructField("anio", T.IntegerType()), T.StructField("fila", T.IntegerType())])
    p = spark.createDataFrame(pop_rows, ps)
    for k in ["poblacion", "hombres", "mujeres"]:
        p = p.withColumn(k, F.col(k).cast("double"))
    exigir_clave(p, ["codigo_canton", "anio"])
    if p.filter("poblacion IS NULL OR poblacion <= 0 OR hombres IS NULL OR mujeres IS NULL OR hombres < 0 OR mujeres < 0 OR abs(poblacion-hombres-mujeres)>0.001").count():
        raise ValueError("Inconsistencia demográfica")
    territory_rows = [(code, NOMBRES_GRUPOS.get(code, name), PROVINCIAS[code[0]]) for code, name in sorted(catalogo.items()) if code not in GRUPOS]
    t = spark.createDataFrame(territory_rows, "codigo_agrupacion string, agrupacion string, provincia string")
    cg, pg, j = construir_integrado(c, p, t)
    n = spark.createDataFrame(nat_rows)
    observed = c.groupBy("anio").agg(*[F.sum(k).alias(k + "_calculado") for k in METRICAS[:3]])
    check = observed.join(n, "anio")
    if check.filter("obras_total_calculado != obras_total OR area_m2_calculado != area_m2 OR abs(valor_miles_colones_calculado-valor_miles_colones)>0.01").count():
        raise ValueError("Los totales cantonales no reconcilian con el total nacional")
    if j.count() != 810 or t.count() != 81:
        raise ValueError("Cobertura integrada diferente de la esperada")
    conservation = cg.groupBy("anio").agg(F.sum("area_m2").alias("agrupado")).join(observed, "anio")
    if conservation.filter("abs(agrupado-area_m2_calculado)>0.001").count():
        raise ValueError("Armonización no conserva área")
    frames = {"territorios": t, "construccion_cantonal": c, "poblacion_cantonal": p,
              "destinos_cantonales": d, "construccion_agrupada": cg, "poblacion_agrupada": pg, "integrado": j}
    counts = {}
    for name, df in frames.items():
        df.write.mode("overwrite").parquet(str(raw / name)); counts[name] = df.count()
    csv = j.orderBy("anio", "codigo_agrupacion").toPandas()
    csv.to_csv(out / "integrado.csv", index=False)
    check.orderBy("anio").toPandas().to_csv(out / "reconciliacion_nacional.csv", index=False)
    report = {"filas": counts, "claves_unicas": True, "totales_nacionales_preservados": True,
              "cruce_sin_perdidas": True, "reglas_territoriales": GRUPOS,
              "signos_no_convertidos_a_cero": True, "hoja_poblacion": "C4", "anios": [2015, 2024]}
    (out / "etl.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def casos_supervisados(integrado):
    w = Window.partitionBy("codigo_agrupacion").orderBy("anio")
    # Cada fila del objetivo usa solo mediciones de t-1 y t-2.
    ds = integrado.withColumnRenamed("anio", "anio_objetivo")
    for name, source, lag in [("area_t", "area_m2", 1), ("area_t_menos1", "area_m2", 2),
                              ("obras_t", "obras_total", 1), ("poblacion_t", "poblacion", 1), ("poblacion_t_menos1", "poblacion", 2)]:
        ds = ds.withColumn(name, F.lag(source, lag).over(Window.partitionBy("codigo_agrupacion").orderBy("anio_objetivo")))
    ds = ds.withColumn("anio_datos", F.lag("anio_objetivo").over(Window.partitionBy("codigo_agrupacion").orderBy("anio_objetivo")))
    ds = ds.filter("anio_objetivo >= 2017")
    if ds.filter("area_t IS NULL OR area_t_menos1 IS NULL OR poblacion_t IS NULL OR poblacion_t_menos1 IS NULL OR anio_datos != anio_objetivo-1").count():
        raise ValueError("Historia incompleta o salto temporal")
    ds = ds.withColumn("crecimiento_poblacion", F.col("poblacion_t") / F.col("poblacion_t_menos1") - 1)
    for col in ["area_t", "area_t_menos1", "obras_t", "poblacion_t"]:
        ds = ds.withColumn("log_" + col, F.log1p(col))
    return ds.withColumn("label_log", F.log1p("area_m2"))
