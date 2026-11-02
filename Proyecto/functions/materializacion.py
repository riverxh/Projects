"""Carga repetible en el esquema proyecto y los índices locales cp-*."""
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import psycopg2
from psycopg2 import sql
import requests
from pyspark.sql import functions as F, types as T
from .entorno import ROOT, iniciar_spark, guardar_json

ES = os.getenv("ELASTICSEARCH_URL", "http://127.0.0.1:9204").rstrip("/")
JDBC = "jdbc:postgresql://" + os.getenv("POSTGRES_HOST", "postgres") + ":5432/" + os.getenv("POSTGRES_DB", "proyecto")
PROPS = {"user": os.getenv("POSTGRES_USER", "estudiante"), "password": os.getenv("POSTGRES_PASSWORD", "proyecto_local"), "driver": "org.postgresql.Driver"}
TABLES = ["territorios", "construccion_cantonal", "poblacion_cantonal", "destinos_cantonales", "construccion_agrupada", "poblacion_agrupada", "integrado", "predicciones"]
INDEX = {"construccion_cantonal": "cp-construccion", "poblacion_cantonal": "cp-poblacion", "destinos_cantonales": "cp-destinos", "integrado": "cp-integrado", "predicciones": "cp-predicciones"}


def conectar_pg():
    return psycopg2.connect(host=os.getenv("POSTGRES_HOST", "postgres"), dbname=os.getenv("POSTGRES_DB", "proyecto"),
                            user=PROPS["user"], password=PROPS["password"])


def es_request(method, path, **kwargs):
    response = requests.request(method, ES + "/" + path.lstrip("/"), timeout=120, **kwargs)
    if not response.ok:
        raise RuntimeError(f"Elasticsearch {response.status_code}: {response.text[:1200]}")
    return response.json()


def mapping(schema):
    props = {}
    for field in schema.fields:
        if isinstance(field.dataType, (T.IntegerType, T.LongType)):
            props[field.name] = {"type": "long"}
        elif isinstance(field.dataType, (T.FloatType, T.DoubleType, T.DecimalType)):
            props[field.name] = {"type": "double"}
        else:
            props[field.name] = {"type": "keyword", "ignore_above": 16000}
    props["fecha"] = {"type": "date"}
    return {"settings": {"number_of_shards": 1, "number_of_replicas": 0}, "mappings": {"dynamic": "strict", "properties": props}}


def crear_indice(name, definition):
    if not name.startswith("cp-"):
        raise ValueError("Se permiten solo índices del proyecto")
    exists = requests.head(ES + "/" + name, timeout=30)
    if exists.status_code == 200:
        es_request("DELETE", name)
    elif exists.status_code != 404:
        exists.raise_for_status()
    es_request("PUT", name, json=definition)
    guardar_json(ROOT / "elastic" / (name + "_mapping.json"), definition)


def bulk(name, pairs):
    count = 0; lines = []
    for identifier, doc in pairs:
        lines.append(json.dumps({"index": {"_index": name, "_id": identifier}}))
        lines.append(json.dumps(doc, ensure_ascii=False, allow_nan=False))
        if len(lines) >= 200:
            response = es_request("POST", "_bulk", data="\n".join(lines) + "\n", headers={"Content-Type": "application/x-ndjson"})
            if response["errors"]:
                raise ValueError("Errores en bulk: " + json.dumps([i for i in response["items"] if i["index"].get("error")])[:1500])
            count += len(lines) // 2; lines = []
    if lines:
        response = es_request("POST", "_bulk", data="\n".join(lines) + "\n", headers={"Content-Type": "application/x-ndjson"})
        if response["errors"]:
            raise ValueError("Errores en bulk final: " + json.dumps(response["items"])[:1000])
        count += len(lines) // 2
    es_request("POST", name + "/_refresh")
    if es_request("GET", name + "/_count")["count"] != count:
        raise ValueError("Conteo de índice diferente a documentos enviados")
    return count


def pares_dataframe(df, table):
    for row in df.toLocalIterator():
        doc = row.asDict()
        year = doc.get("anio", doc.get("anio_objetivo"))
        doc["fecha"] = f"{year}-01-01T06:00:00.000Z"
        keys = [doc.get(k, "") for k in ["codigo_canton", "codigo_agrupacion", "anio", "anio_objetivo", "modelo", "id"]]
        identifier = hashlib.sha256(json.dumps(keys).encode()).hexdigest()
        yield identifier, doc


def cargar():
    spark = iniciar_spark(); spark.sparkContext.setLogLevel("ERROR")
    try:
        frames = {name: spark.read.parquet(str(ROOT / "data/preparados" / name)) for name in TABLES}
        for name, df in frames.items():
            df.write.jdbc(JDBC, "public.stage_" + name, mode="overwrite", properties=PROPS)
        # El esquema es exclusivo de esta aplicación. Staging se completa antes de
        # reemplazarlo; rollback conserva la versión anterior si hay un fallo.
        with conectar_pg() as db:
            with db.cursor() as cur:
                cur.execute("DROP SCHEMA IF EXISTS proyecto CASCADE; CREATE SCHEMA proyecto")
                for name in TABLES:
                    cur.execute(sql.SQL("ALTER TABLE public.{} SET SCHEMA proyecto").format(sql.Identifier("stage_" + name)))
                    cur.execute(sql.SQL("ALTER TABLE proyecto.{} RENAME TO {}").format(sql.Identifier("stage_" + name), sql.Identifier(name)))
                keys = {"territorios": ["codigo_agrupacion"], "construccion_cantonal": ["codigo_canton", "anio"],
                        "poblacion_cantonal": ["codigo_canton", "anio"], "destinos_cantonales": ["id"],
                        "construccion_agrupada": ["codigo_agrupacion", "anio"], "poblacion_agrupada": ["codigo_agrupacion", "anio"],
                        "integrado": ["codigo_agrupacion", "anio"], "predicciones": ["modelo", "codigo_agrupacion", "anio_objetivo"]}
                for name, kk in keys.items():
                    cur.execute(sql.SQL("ALTER TABLE proyecto.{} ADD PRIMARY KEY ({})").format(sql.Identifier(name), sql.SQL(",").join(map(sql.Identifier, kk))))
                for name in ["construccion_agrupada", "poblacion_agrupada", "integrado", "predicciones"]:
                    cur.execute(sql.SQL("ALTER TABLE proyecto.{} ADD FOREIGN KEY (codigo_agrupacion) REFERENCES proyecto.territorios(codigo_agrupacion)").format(sql.Identifier(name)))
                cur.execute("ALTER TABLE proyecto.integrado ADD CHECK (poblacion>0 AND area_m2>=0)")
                cur.execute("ALTER TABLE proyecto.predicciones ADD CHECK (prediccion_m2>=0 AND anio_datos=anio_objetivo-1)")
        for name, df in frames.items():
            read_back = spark.read.jdbc(JDBC, "proyecto." + name, properties=PROPS).select(df.columns)
            if df.exceptAll(read_back).limit(1).count() or read_back.exceptAll(df).limit(1).count():
                raise ValueError("La relectura PostgreSQL no reproduce el contenido de " + name)
        counts = {}
        for table, name in INDEX.items():
            df = frames[table]; definition = mapping(df.schema)
            crear_indice(name, definition); counts[name] = bulk(name, pares_dataframe(df, table))
        # Validaciones de DataFrame también para el texto antes de materializarlo.
        frags = [json.loads(line) for line in (ROOT / "output/fragmentos.jsonl").read_text().splitlines()]
        basic = [{k: c[k] for k in ["fragmento_id", "documento_id", "pagina_pdf", "tokens_entrada", "texto"]} for c in frags]
        text_df = spark.createDataFrame(basic)
        if text_df.select("fragmento_id").distinct().count() != len(frags) or text_df.filter("tokens_entrada>400 OR length(trim(texto))=0").count():
            raise ValueError("Corpus inválido antes de indexar")
        v = np.load(ROOT / "output/embeddings.npz", allow_pickle=False)
        if list(v["fragmento_id"]) != [c["fragmento_id"] for c in frags] or v["vectores"].shape != (len(frags), 384):
            raise ValueError("Vectores desalineados con fragmentos")
        props = {"fragmento_id": {"type": "keyword"}, "documento_id": {"type": "keyword"},
                 "titulo": {"type": "text", "analyzer": "spanish"}, "autor": {"type": "keyword"}, "anio": {"type": "integer"},
                 "idioma": {"type": "keyword"}, "pagina_pdf": {"type": "integer"}, "tipo": {"type": "keyword"},
                 "texto": {"type": "text", "analyzer": "spanish"}, "url_fuente": {"type": "keyword"}, "url_pdf": {"type": "keyword"},
                 "pdf_sha256": {"type": "keyword"}, "char_inicio": {"type": "integer"}, "char_fin": {"type": "integer"},
                 "tokens_entrada": {"type": "integer"}, "fecha": {"type": "date"}}
        for name, vectorial in [("cp-texto", False), ("cp-vector", True)]:
            p = dict(props)
            if vectorial:
                p["embedding"] = {"type": "dense_vector", "dims": 384, "index": True, "similarity": "cosine", "index_options": {"type": "hnsw"}}
            definition = {"settings": {"number_of_shards": 1, "number_of_replicas": 0}, "mappings": {"dynamic": "strict", "properties": p}}
            crear_indice(name, definition)
            def pares():
                for i, c in enumerate(frags):
                    doc = {k: c[k] for k in props if k != "fecha"}; doc["fecha"] = f"{c['anio']}-01-01T06:00:00.000Z"
                    if vectorial:
                        doc["embedding"] = v["vectores"][i].tolist()
                    yield c["fragmento_id"], doc
            counts[name] = bulk(name, pares())
        guardar_json(ROOT / "output/cargas.json", {"indices": counts, "tablas": {k: v.count() for k, v in frames.items()}, "relectura_sql_contenido_identico": True, "escritura": "Reemplazo del esquema proyecto y recreación de cp-*; fuentes originales intactas"})
    finally:
        spark.stop()
    return verificar()


def verificar():
    expected = json.loads((ROOT / "output/cargas.json").read_text())
    tables, indices = {}, {}
    with conectar_pg() as db:
        with db.cursor() as cur:
            for name, count in expected["tablas"].items():
                cur.execute(sql.SQL("SELECT count(*) FROM proyecto.{}").format(sql.Identifier(name)))
                observed = cur.fetchone()[0]
                if observed != count:
                    raise ValueError(f"Conteo PostgreSQL: {name}: {observed} != {count}")
                tables[name] = observed
            cur.execute("SELECT count(*) FROM proyecto.predicciones p JOIN proyecto.integrado i ON p.codigo_agrupacion=i.codigo_agrupacion AND p.anio_objetivo=i.anio WHERE abs(p.observado_m2-i.area_m2)>0.001")
            if cur.fetchone()[0]:
                raise ValueError("Objetivos SQL diferentes al integrado")
            cur.execute("SELECT count(*) FROM proyecto.integrado i JOIN proyecto.construccion_agrupada c USING(codigo_agrupacion,anio) JOIN proyecto.poblacion_agrupada p USING(codigo_agrupacion,anio) WHERE abs(i.area_m2-c.area_m2)>0.001 OR abs(i.poblacion-p.poblacion)>0.001")
            if cur.fetchone()[0]:
                raise ValueError("Cruce SQL inconsistente")
            cur.execute("SELECT modelo,count(*),avg(error_absoluto_m2),sqrt(avg(error_m2*error_m2)) FROM proyecto.predicciones GROUP BY modelo ORDER BY modelo")
            sqlmetrics = [dict(zip(["modelo", "n", "mae_m2", "rmse_m2"], r)) for r in cur.fetchall()]
            recorded = json.loads((ROOT / "output/modelos.json").read_text())["metricas"]
            for row in sqlmetrics:
                ref = next(r for r in recorded if r["modelo"] == row["modelo"] and r["particion"] == "prueba_2023_2024")
                if row["n"] != ref["n"] or any(abs(row[k] - ref[k]) > .0001 for k in ["mae_m2", "rmse_m2"]):
                    raise ValueError("Las métricas SQL no coinciden con las de Spark")
    for name, count in expected["indices"].items():
        observed = es_request("GET", name + "/_count")["count"]
        if observed != count:
            raise ValueError(f"Conteo Elasticsearch diferente: {name}")
        indices[name] = observed
    # Comparar todos los identificadores y el texto entre los dos índices.
    a = es_request("POST", "cp-texto/_search", json={"size": 2000, "sort": ["fragmento_id"], "_source": ["fragmento_id", "texto"]})["hits"]["hits"]
    b = es_request("POST", "cp-vector/_search", json={"size": 2000, "sort": ["fragmento_id"], "_source": ["fragmento_id", "texto"]})["hits"]["hits"]
    if [r["_source"] for r in a] != [r["_source"] for r in b] or len(a) != indices["cp-texto"]:
        raise ValueError("Los índices no contienen los mismos fragmentos")
    result = {"tablas": tables, "indices": indices, "fragmentos_identicos_entre_indices": True,
              "cruce_sql_comprobado": True, "objetivos_prediccion_comprobados": True, "metricas_recalculadas_sql": sqlmetrics}
    guardar_json(ROOT / "output/verificacion_bases.json", result)
    print(result, flush=True)
    return result
