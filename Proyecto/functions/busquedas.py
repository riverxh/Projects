"""Comparación reproducible de BM25 y kNN; relevancia se anota por lectura."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from .entorno import ROOT, guardar_json
from .materializacion import es_request


def ejecutar():
    queries = json.loads((ROOT / "config/consultas.json").read_text())
    vectors = np.load(ROOT / "output/consultas_vectores.npz", allow_pickle=False)
    if list(vectors["consulta_id"]) != [q["id"] for q in queries]:
        raise ValueError("Vectores de consulta desalineados")
    guardar_json(ROOT / "output/protocolo_busqueda.json", {
        "consultas_sha256": hashlib.sha256((ROOT / "config/consultas.json").read_bytes()).hexdigest(),
        "consulta_y_mappings_congelados_antes_de_ejecutar": True, "k": 5, "num_candidates": 200,
        "texto": "BM25 multi_match texto y titulo^0.2, analyzer spanish; sin filtro territorial automático",
        "vector": "kNN coseno con E5 query:, sin filtro territorial automático",
        "relevancia": "0 no pertinente, 1 contextual/parcial, 2 responde de manera directa. Métricas estrictas consideran relevante grado 2.",
        "grupos": "Q01-Q04 desarrollo; Q05-Q12 reserva sin ajuste posterior del ranking; Q13-Q14 controles sin respuesta",
        "advertencia": "Q01-Q04 ya se exploraron en el piloto; las de reserva son una evaluación interna pequeña, no validación externa"})
    results, pool, console = [], {}, []
    for q, vector in zip(queries, vectors["vectores"]):
        for method, index in [("texto", "cp-texto"), ("vector", "cp-vector")]:
            if method == "texto":
                body = {"size": 5, "query": {"multi_match": {"query": q["texto"], "fields": ["texto", "titulo^0.2"]}}, "_source": {"excludes": ["embedding"]}}
            else:
                body = {"size": 5, "knn": {"field": "embedding", "query_vector": vector.tolist(), "k": 5, "num_candidates": 200}, "_source": {"excludes": ["embedding"]}}
            start = time.perf_counter()
            response = es_request("POST", index + "/_search", json=body)
            elapsed = time.perf_counter() - start
            hits = response["hits"]["hits"]
            results.append({**q, "metodo": method, "latencia_cliente_segundos": elapsed, "took_ms": response["took"],
                            "resultados": [{"rango": i, "score": h["_score"], **h["_source"]} for i, h in enumerate(hits, 1)]})
            for h in hits:
                key = (q["id"], h["_id"])
                pool[key] = {"consulta_id": q["id"], "consulta": q["texto"], "grupo": q["grupo"], **h["_source"]}
            if method == "texto" or q["id"] in ["Q03", "Q09", "Q13"]:
                console.append("# " + q["id"] + " " + method + ": " + q["texto"] + "\nPOST " + index + "/_search\n" + json.dumps(body, ensure_ascii=False, indent=2))
    guardar_json(ROOT / "output/resultados_busqueda.json", results)
    # Pool ciego: orden por ID, sin score, método ni posición. Evita valorar por el
    # algoritmo que produjo el pasaje y admite relevancia en varias fuentes.
    blind = [pool[k] for k in sorted(pool)]
    guardar_json(ROOT / "output/pool_relevancia.json", blind)
    (ROOT / "elastic/Consultas_Kibana.http").write_text("\n\n".join(console) + "\n")
    evaluar_si_anotado(results)
    print("Búsquedas ejecutadas:", len(results), "pares únicos para revisar:", len(blind), flush=True)


def evaluar_si_anotado(results=None):
    annotations = ROOT / "config/relevancia.json"
    if not annotations.exists():
        return
    judgments = json.loads(annotations.read_text())
    labels = {(j["consulta_id"], j["fragmento_id"]): j for j in judgments}
    results = results or json.loads((ROOT / "output/resultados_busqueda.json").read_text())
    rows = []
    for r in results:
        grades = []
        for h in r["resultados"]:
            key = (r["id"], h["fragmento_id"])
            if key not in labels:
                raise ValueError("Falta juicio de relevancia: " + str(key))
            grades.append(labels[key]["grado"])
        relevant = [i + 1 for i, g in enumerate(grades) if g == 2]
        contextual = sum(g >= 1 for g in grades)
        rows.append({"consulta_id": r["id"], "grupo": r["grupo"], "tipo": r["tipo"], "metodo": r["metodo"],
                     "precision_5_estricta": sum(g == 2 for g in grades) / 5,
                     "precision_5_contextual": contextual / 5,
                     "reciproco_primer_relevante": 1 / relevant[0] if relevant else 0,
                     "rango_primer_relevante": relevant[0] if relevant else None,
                     "latencia_cliente_segundos": r["latencia_cliente_segundos"]})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "output/metricas_busqueda.csv", index=False)
    summary = df.groupby(["grupo", "metodo"])[["precision_5_estricta", "precision_5_contextual", "reciproco_primer_relevante"]].mean().reset_index()
    summary.to_csv(ROOT / "output/resumen_busqueda.csv", index=False)
    guardar_json(ROOT / "output/evaluacion_busqueda.json", {"consultas": len(set(df.consulta_id)),
        "juicios": len(judgments), "resumen": summary.to_dict("records"),
        "limites": "Un único conjunto pequeño de juicios documentales; pool top5 de ambos métodos, no exhaustivo; no permite medir recall global ni superioridad universal. Controles sin respuesta se informan separados."})
