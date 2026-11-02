import json
from pathlib import Path
import numpy as np
import pytest
from pyspark.sql import functions as F
from functions.entorno import ROOT, iniciar_spark
from functions.datos import (cargar_fuentes, extraer_poblacion, extraer_construccion,
    limpiar_construccion, schema_construccion, casos_supervisados, exigir_clave, agrupar_codigo, asignar_provincia)
from functions.fragmentacion import fragmentar, n_tokens
from functions.textos import texto_narrativo, codificar_cache


@pytest.fixture(scope="session")
def spark():
    s = iniciar_spark(); s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()


@pytest.fixture(scope="session")
def fuentes():
    m = cargar_fuentes(); p, cat = extraer_poblacion(m["poblacion"])
    c, d, n = extraer_construccion(m["construccion"], cat)
    return p, cat, c, d, n


def test_originales_y_cobertura_demografica(fuentes):
    p, cat, *_ = fuentes
    assert len(p) == 840 and len(cat) == 84
    for row in p:
        assert abs(float(row["poblacion"]) - float(row["hombres"]) - float(row["mujeres"])) < .001
    sanjose = next(x for x in p if x["codigo_canton"] == "101" and x["anio"] == 2024)
    assert round(float(sanjose["poblacion"])) == 352298


def test_cabeceras_historicas_con_espaciadores_y_ejemplo_original(fuentes):
    _, _, c, _, n = fuentes
    assert len(c) == 818
    y16 = [r for r in c if r["anio"] == 2016]
    assert len(y16) == 81
    assert json.loads(y16[0]["columnas_metricas"])["obras_ampliacion"] == "J"
    sj = next(r for r in c if r["codigo_canton"] == "101" and r["anio"] == 2024)
    assert int(sj["area_m2"]) == 101064 and int(sj["obras_total"]) == 679
    assert int(sj["area_nueva_m2"]) + int(sj["area_ampliacion_m2"]) == 101064
    for national in n:
        for key in ["obras_total", "area_m2", "valor_miles_colones"]:
            assert sum(float(x[key]) for x in c if x["anio"] == national["anio"]) == pytest.approx(national[key], abs=.001)


def fila_valida():
    return {"codigo_canton": "101", "canton": "San José", "anio": 2024,
            "obras_total": "1", "area_m2": "10", "valor_miles_colones": "20", "area_ampliacion_m2": "-"}


def test_signo_no_se_convierte_en_cero(spark):
    df = spark.createDataFrame([fila_valida()], schema_construccion())
    clean = limpiar_construccion(df)
    assert clean.first()["area_ampliacion_m2"] is None


@pytest.mark.parametrize("campo,valor", [("area_m2", "-2"), ("obras_total", "1.5"), ("area_m2", "texto")])
def test_reglas_de_dominio_rechazan_datos_invalidos(spark, campo, valor):
    row = fila_valida(); row[campo] = valor
    with pytest.raises(ValueError):
        limpiar_construccion(spark.createDataFrame([row], schema_construccion()))


def test_claves_duplicadas_no_se_silencian(spark):
    row = fila_valida()
    with pytest.raises(ValueError, match="duplicada"):
        limpiar_construccion(spark.createDataFrame([row, row], schema_construccion()))


def test_agregacion_de_las_tres_segregaciones(spark):
    df = spark.createDataFrame([(c,) for c in ["203", "216", "601", "612", "607", "613", "101"]], "codigo_canton string")
    r = {x.codigo_canton: x.codigo_agrupacion for x in agrupar_codigo(df).collect()}
    assert r == {"203": "203", "216": "203", "601": "601", "612": "601", "607": "607", "613": "607", "101": "101"}


def historia(spark, objetivo=999.0):
    return spark.createDataFrame([("101", 2015, 10.0, 1, 100.0), ("101", 2016, 20.0, 2, 110.0), ("101", 2017, objetivo, 3, 120.0)],
                                  "codigo_agrupacion string, anio int, area_m2 double, obras_total long, poblacion double")


def test_predictores_no_utilizan_el_objetivo_del_mismo_anio(spark):
    a = casos_supervisados(historia(spark)).first().asDict()
    b = casos_supervisados(historia(spark, 8888.0)).first().asDict()
    assert a["area_t"] == b["area_t"] == 20.0
    assert a["area_t_menos1"] == b["area_t_menos1"] == 10.0
    assert a["poblacion_t"] == b["poblacion_t"] == 110.0
    assert a["anio_datos"] == 2016 and a["anio_objetivo"] == 2017
    assert a["label_log"] != b["label_log"]


def test_historia_incompleta_se_rechaza(spark):
    with pytest.raises(ValueError, match="incompleta"):
        casos_supervisados(historia(spark).filter("anio != 2016"))


@pytest.fixture(scope="session")
def tokenizer():
    from transformers import AutoTokenizer
    from huggingface_hub import snapshot_download
    m = json.loads((ROOT / "config/modelo.json").read_text())
    snapshot = snapshot_download(m["modelo"], revision=m["revision"], token=False,
        cache_dir=str(ROOT / ".cache/huggingface/hub"), local_files_only=True)
    return AutoTokenizer.from_pretrained(snapshot, local_files_only=True)


def test_fragmentos_conservan_texto_y_respetan_prefijo(tokenizer):
    text = "\n\n".join("Ordenamiento y expansión urbana en Pococí. " * 50 for _ in range(4)) + " Última evidencia."
    parts = fragmentar(text, tokenizer, 400, 40)
    coverage = set()
    for c in parts:
        assert n_tokens(tokenizer, "passage: " + c["texto"]) <= 400
        coverage.update(range(c["char_inicio"], c["char_fin"]))
    assert all(i in coverage for i, ch in enumerate(text) if not ch.isspace())
    assert parts[-1]["texto"].endswith("Última evidencia.")


def test_formulas_dudosas_se_separan_sin_inventar_simbolos():
    text = "Párrafo narrativo que explica el ordenamiento territorial y su relación con el entorno.\n\nFórmula \uf074 = 123\n\n101 202 303 404 505"
    clean, excluded = texto_narrativo(text)
    assert "Párrafo narrativo" in clean
    assert "\uf074" not in clean
    assert len(excluded) == 2


def test_cache_reutiliza_y_distingue_prefijos(tokenizer, tmp_path, monkeypatch):
    import functions.textos as module
    (tmp_path / "output").mkdir(); monkeypatch.setattr(module, "ROOT", tmp_path)
    class Encoder:
        entradas = 0
        def encode(self, texts, **kwargs):
            self.entradas += len(texts)
            return np.tile(np.array([1., 0., 0., 0.]), (len(texts), 1))
    e = Encoder(); model = {"dimensiones": 4, "modelo": "prueba", "revision": "a"}
    a, aa = codificar_cache(["texto de prueba"], "passage: ", e, tokenizer, model, {})
    b, bb = codificar_cache(["texto de prueba"], "passage: ", e, tokenizer, model, {})
    _, cc = codificar_cache(["texto de prueba"], "query: ", e, tokenizer, model, {})
    assert aa["nuevos"] == 1 and bb["nuevos"] == 0 and cc["nuevos"] == 1
    assert e.entradas == 2 and np.array_equal(a, b)


def test_categorias_y_detalles_se_conservan_en_niveles_distintos(fuentes, spark):
    _, _, cantonales, details, _ = fuentes
    sj = [r for r in details if r["anio"] == 2024 and r["codigo_canton"] == "101"]
    subtotal = next(r for r in sj if r["destino"] == "VIVIENDAS")
    casas = next(r for r in sj if r["destino"] == "Casas")
    assert subtotal["nivel"] == "subtotal_categoria" and casas["nivel"] == "detalle"
    assert subtotal["area_m2"] == "52361" and casas["area_m2"] == "8503"
    # Ejecutar las reglas sobre todo el detalle original, incluida la notación
    # N.D de 2019 y la anomalía aislada N de Coto Brus 2020.
    clean = asignar_provincia(limpiar_construccion(spark.createDataFrame(details, schema_construccion(True)), False))
    assert clean.count() == 12121
    assert clean.filter("id = '2020-608-1413'").first()["obras_reparacion"] is None
    # Una provincia seleccionada debe conservar destinos y sumar la misma área
    # anual que sus totales cantonales, sin contar también el detalle.
    filtered = clean.filter("provincia = 'Heredia' AND anio = 2024 AND nivel = 'subtotal_categoria'")
    expected = sum(float(r["area_m2"]) for r in cantonales if r["anio"] == 2024 and r["codigo_canton"].startswith("4"))
    assert filtered.count() > 0
    assert filtered.agg(F.sum("area_m2")).first()[0] == pytest.approx(expected, abs=.001)


def test_solo_subtotales_de_categoria_reconcilian_area_nacional(fuentes):
    _, _, _, details, national = fuentes
    for n in national:
        vals = [r["area_m2"] for r in details if r["anio"] == n["anio"] and r["nivel"] == "subtotal_categoria"]
        known = [float(v) for v in vals if v not in [None, "-", ".", ""]]
        assert sum(known) == pytest.approx(n["area_m2"], abs=.001)
