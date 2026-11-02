"""Cinco visualizaciones de datos reales en un dashboard reproducible de Kibana."""
import json
import os
import time
from pathlib import Path
import requests
from .entorno import ROOT, guardar_json

KIBANA = os.getenv("KIBANA_URL", "http://127.0.0.1:5604").rstrip("/")
HEADERS = {"kbn-xsrf": "proyecto"}


def api(method, path, **kwargs):
    r = requests.request(method, KIBANA + path, headers=HEADERS, timeout=90, **kwargs)
    if not r.ok:
        raise RuntimeError(f"Kibana {r.status_code}: {r.text[:1500]}")
    return r


def especificacion(index, body, fmt, x, y, mark="bar", transforms=None):
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "autosize": {"type": "fit", "contains": "padding"},
            "data": {"url": {"%context%": True, "%timefield%": "fecha", "index": index, "body": body}, "format": {"property": fmt}},
            "mark": {"type": mark, "color": "#176D8A", "tooltip": True},
            "encoding": {"x": x, "y": y},
            "config": {"axis": {"labelFontSize": 11, "titleFontSize": 12}, "view": {"stroke": None}}}
    if transforms:
        spec["transform"] = transforms
    return spec


def crear():
    for attempt in range(20):
        try:
            status = api("GET", "/api/status").json()
            if status.get("status", {}).get("overall", {}).get("level") == "available":
                break
        except (requests.RequestException, RuntimeError):
            pass
        if attempt == 19:
            raise RuntimeError("Kibana no estuvo disponible en 60 segundos")
        time.sleep(3)
    api("POST", "/api/data_views/data_view", json={"data_view": {"id": "cp-integrado-view", "name": "Construcción y población", "title": "cp-integrado", "timeFieldName": "fecha"}, "override": True})
    body_area = {"size": 0, "aggs": {"valores": {"terms": {"field": "anio", "size": 20, "order": {"_key": "asc"}}, "aggs": {"area": {"sum": {"field": "area_m2"}}}}}}
    body_obras = {"size": 0, "aggs": {"valores": {"terms": {"field": "provincia", "size": 7}, "aggs": {"obras": {"sum": {"field": "obras_total"}}}}}}
    body_ratio = {"size": 0, "aggs": {"valores": {"terms": {"field": "provincia", "size": 7}, "aggs": {"area": {"sum": {"field": "area_m2"}}, "poblacion": {"sum": {"field": "poblacion"}}}}}}
    body_destinos = {"size": 0, "aggs": {"seleccion": {"filter": {"term": {"nivel": "subtotal_categoria"}}, "aggs": {"valores": {"terms": {"field": "categoria", "size": 20}, "aggs": {"area": {"sum": {"field": "area_m2"}}}}}}}}
    body_error = {"size": 0, "aggs": {"valores": {"terms": {"field": "modelo", "size": 2}, "aggs": {"mae": {"avg": {"field": "error_absoluto_m2"}}}}}}
    specs = [
        ("area", "Área autorizada por año (m²)", especificacion("cp-integrado", body_area, "aggregations.valores.buckets",
            {"field": "key", "type": "ordinal", "title": "Año", "sort": "ascending", "axis": {"labelAngle": 0}},
            {"field": "area.value", "type": "quantitative", "title": "Área autorizada (m²)", "axis": {"format": "~s"}}, "line")),
        ("obras", "Obras autorizadas por provincia, periodo seleccionado", especificacion("cp-integrado", body_obras, "aggregations.valores.buckets",
            {"field": "obras.value", "type": "quantitative", "title": "Obras", "axis": {"format": "~s"}},
            {"field": "key", "type": "nominal", "title": "Provincia", "sort": "-x"})),
        ("habitante", "Área anual por habitante, media ponderada del periodo", especificacion("cp-integrado", body_ratio, "aggregations.valores.buckets",
            {"field": "ratio", "type": "quantitative", "title": "m² por habitante", "axis": {"format": ".2f"}},
            {"field": "key", "type": "nominal", "title": "Provincia", "sort": "-x"}, transforms=[{"calculate": "datum.area.value / datum.poblacion.value", "as": "ratio"}])),
        ("destinos", "Área por categoría de destino, sin sumar subtotales y detalle", especificacion("cp-destinos", body_destinos, "aggregations.seleccion.valores.buckets",
            {"field": "area.value", "type": "quantitative", "title": "Área autorizada (m²)", "axis": {"format": "~s"}},
            {"field": "key", "type": "nominal", "title": "Categoría", "sort": "-x"})),
        ("errores", "Error absoluto medio de modelos, reserva 2023–2024", especificacion("cp-predicciones", body_error, "aggregations.valores.buckets",
            {"field": "key", "type": "nominal", "title": "Modelo"},
            {"field": "mae.value", "type": "quantitative", "title": "MAE (m²)", "axis": {"format": "~s"}})),
    ]
    objects, panels, refs = [], [], []
    for i, (key, title, spec) in enumerate(specs):
        identifier = "cp-viz-" + key
        guardar_json(ROOT / "kibana" / (identifier + ".json"), spec)
        objects.append({"type": "visualization", "id": identifier, "attributes": {"title": title, "description": "Datos del proyecto; respeta periodo y filtros globales.",
                        "visState": json.dumps({"title": title, "type": "vega", "aggs": [], "params": {"spec": json.dumps(spec)}}),
                        "uiStateJSON": "{}", "kibanaSavedObjectMeta": {"searchSourceJSON": "{}"}}, "references": []})
        grid = {"x": 0, "y": 0, "w": 48, "h": 10} if i == 0 else {"x": ((i - 1) % 2) * 24, "y": 10 + ((i - 1) // 2) * 11, "w": 24, "h": 11}
        panels.append({"version": "8.14.3", "type": "visualization", "gridData": {**grid, "i": str(i)}, "panelIndex": str(i), "embeddableConfig": {}, "panelRefName": "panel_" + str(i)})
        refs.append({"type": "visualization", "id": identifier, "name": "panel_" + str(i)})
    objects.append({"type": "dashboard", "id": "cp-dashboard", "attributes": {
        "title": "Construcción autorizada y población en Costa Rica",
        "description": "INEC 2015–2024. Permisos autorizados, no obras terminadas. Tres segregaciones agregadas a sus territorios de origen. Errores: reserva 2023–2024.",
        "panelsJSON": json.dumps(panels), "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
        "timeRestore": True, "timeFrom": "2015-01-01T06:00:00.000Z", "timeTo": "2025-01-01T05:59:59.999Z",
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})}}, "references": refs})
    result = api("POST", "/api/saved_objects/_bulk_create?overwrite=true", json=objects).json()
    if any(x.get("error") for x in result.get("saved_objects", [])):
        raise RuntimeError("No se crearon todos los objetos: " + json.dumps(result)[:2000])
    exported = api("POST", "/api/saved_objects/_export", json={"objects": [{"type": "dashboard", "id": "cp-dashboard"}, {"type": "index-pattern", "id": "cp-integrado-view"}], "includeReferencesDeep": True}).text
    (ROOT / "kibana/dashboard.ndjson").write_text(exported)
    guardar_json(ROOT / "output/dashboard.json", {"id": "cp-dashboard", "visualizaciones": 5,
                  "url_local": "http://127.0.0.1:5604/app/dashboards#/view/cp-dashboard",
                  "objetos_exportados": len(exported.strip().splitlines()) - 1, "resultado_api": result})
    print("Dashboard creado con cinco visualizaciones y exportado", flush=True)
