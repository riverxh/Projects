"""Casos con resultados esperados independientes. Generado con ayuda de IA."""
import json
import pytest
from pyspark.sql.types import ArrayType, StructType
from functions.esquemas import SALIDA
from functions.procesamiento import (
    leer_json, articulos_por_mes, articulos_por_grupo, areas_por_persona,
    referencias_por_persona, persona_con_mas_referencias, percentiles, escribir_tabla,
)
from programa import ejecutar


def articulo(doi="a", grupo="Salud", autores=None, referencias=None,
             fecha="2021-03-26T15:50:17Z"):
    return {"doi": doi, "groupTitle": grupo, "author": autores,
            "reference": referencias, "createdDate": fecha}


def tabla(spark, *filas):
    return spark.createDataFrame(list(filas), SALIDA)


def pares(df, clave, valor):
    return {fila[clave]: fila[valor] for fila in df.collect()}


def test_lectura_multilinea_y_esquema_completo(spark, tmp_path):
    ruta = tmp_path / "uno.json"
    ruta.write_text(json.dumps({"message": {
        "DOI": "10/prueba", "author": [{"given": "Ana", "affiliation": []}],
        "institution": [{"name": "Instituto"}], "group-title": "Salud",
        "created": {"date-time": "2021-03-26T15:50:17Z"},
        "reference": [{"DOI": "10/ref"}], "link": [{"URL": "https://example.org"}],
    }}, indent=2))
    df = leer_json(spark, [str(ruta)])
    assert df.schema == SALIDA
    fila = df.first()
    assert fila.doi == "10/prueba" and fila.inst[0].name == "Instituto"
    assert fila.createdDate == "2021-03-26T15:50:17Z"
    assert fila.author[0].name is None and fila.author[0].suffix is None
    assert fila.reference[0].ISSN is None
    assert isinstance(df.schema["author"].dataType, ArrayType)
    assert isinstance(df.schema["author"].dataType.elementType["affiliation"].dataType.elementType, StructType)


def test_lectura_varios_archivos_y_opcionales_ausentes(spark, tmp_path):
    for nombre in ("a", "b"):
        (tmp_path / f"{nombre}.json").write_text(json.dumps({"message": {"DOI": nombre}}))
    df = leer_json(spark, [str(tmp_path / "a.json"), str(tmp_path / "b.json")])
    assert {r.doi for r in df.collect()} == {"a", "b"}
    assert all(r.author is None for r in df.collect())


def test_entrada_sin_rutas(spark):
    with pytest.raises(ValueError, match="ruta"):
        leer_json(spark, [])


def test_documento_sin_message(spark, tmp_path):
    ruta = tmp_path / "sin_message.json"
    ruta.write_text('{"status":"ok"}')
    with pytest.raises(ValueError, match="message"):
        leer_json(spark, [str(ruta)])


def test_json_malformado(spark, tmp_path):
    ruta = tmp_path / "roto.json"
    ruta.write_text('{"message": {"DOI":')
    with pytest.raises(Exception):
        leer_json(spark, [str(ruta)]).collect()


def test_ruta_inexistente(spark, tmp_path):
    with pytest.raises(Exception, match="PATH_NOT_FOUND"):
        leer_json(spark, [str(tmp_path / "no_existe.json")])


def test_mes_cuenta_articulos_no_autores_y_usa_created(spark):
    df = tabla(spark,
        articulo("a", autores=[{"given": "Ana"}, {"given": "Luis"}]),
        articulo("b", fecha="2021-03-31T23:59:59Z"),
        articulo("c", fecha="2020-12-01T00:00:00Z"),
    )
    assert [tuple(r) for r in articulos_por_mes(df).collect()] == [(2020, 12, 1), (2021, 3, 2)]


def test_fechas_invalidas_no_desaparecen(spark):
    df = tabla(spark, articulo(fecha=None), articulo(fecha="no-es-fecha"))
    assert [tuple(r) for r in articulos_por_mes(df).collect()] == [(None, None, 2)]


def test_grupos_deduplican_doi_y_no_cuentan_identificador_vacio(spark):
    df = tabla(spark, articulo("a"), articulo("a"), articulo("b"),
               articulo("a", grupo="Biologia"), articulo(" ", grupo=None))
    assert pares(articulos_por_grupo(df), "group_title", "total") == {
        "Salud": 2, "Biologia": 1, None: 0,
    }


def test_areas_nombres_distintos_y_unknown(spark):
    ana = {"given": "Ana", "family": "Perez"}
    df = tabla(spark,
        articulo("a", autores=[ana, ana, {"given": "  ", "family": " "}]),
        articulo("b", autores=[ana], grupo="Biologia"),
        articulo("c", autores=[{"family": "Solo"}], grupo=None),
        articulo("d", autores=None), articulo("e", autores=[]),
        articulo("f", autores=[None]),
    )
    filas = areas_por_persona(df).collect()
    assert filas[0].full_name == "Ana Perez"
    resultados = {r.full_name: (r.research_areas, r.total) for r in filas}
    assert resultados == {"Ana Perez": (["Biologia", "Salud"], 2),
                           "unknown": (["Salud"], 1), "Solo": ([], 0)}


def test_referencias_coautores_doi_repetidos_y_doi_ausente(spark):
    ana, luis = {"given": "Ana"}, {"given": "Luis"}
    df = tabla(spark,
        articulo("a", autores=[ana, ana, luis], referencias=[
            {"DOI": "x"}, {"DOI": "x"}, {}, {"DOI": " "}, None,
        ]),
        articulo("b", autores=[ana], referencias=[{"DOI": "y"}]),
        articulo("c", autores=[{"given": "Cero"}], referencias=None),
        articulo("d", autores=[{"given": "Vacio"}], referencias=[]),
    )
    assert pares(referencias_por_persona(df, conteo="entries"), "full_name", "total_references") == {"Ana": 3, "Luis": 2}
    assert pares(referencias_por_persona(df, True, "entries"), "full_name", "total_references") == {
        "Ana": 3, "Luis": 2, "Cero": 0, "Vacio": 0,
    }
    assert pares(referencias_por_persona(df), "full_name", "total_references") == {"Ana": 2, "Luis": 1}
    assert pares(referencias_por_persona(df, True), "full_name", "total_references") == {
        "Ana": 2, "Luis": 1, "Cero": 0, "Vacio": 0,
    }


def test_doi_distinto_por_persona_a_traves_de_varios_articulos(spark):
    df = tabla(spark,
        articulo("a", autores=[{"given": "Ana"}], referencias=[{"DOI": "x"}, {"DOI": "x"}]),
        articulo("b", autores=[{"given": "Ana"}], referencias=[{"DOI": "x"}, {"DOI": "y"}]),
    )
    assert referencias_por_persona(df).first().total_references == 2
    assert referencias_por_persona(df, conteo="entries").first().total_references == 4


def test_unknown_solo_se_incluye_en_referencias_si_se_solicita(spark):
    df = tabla(spark, articulo(autores=[{}, {"given": "Ana"}], referencias=[{"DOI": "x"}]))
    assert pares(referencias_por_persona(df), "full_name", "total_references") == {"Ana": 1}
    assert pares(referencias_por_persona(df, incluir_unknown=True), "full_name", "total_references") == {"Ana": 1, "unknown": 1}
    assert "unknown" in pares(areas_por_persona(df), "full_name", "total")
    with pytest.raises(ValueError, match="Modo"):
        referencias_por_persona(df, conteo="invalido")


def test_maximo_desempata_por_nombre(spark):
    df = spark.createDataFrame([("Zoe", 8), ("Ana", 8), ("Luis", 3)], "full_name string, total_references long")
    assert tuple(persona_con_mas_referencias(df).first()) == ("Ana", 8)


@pytest.mark.parametrize("metodo,esperado", [
    ("continuous", (7.5, 15.0, 22.5)), ("nearest-rank", (0.0, 10.0, 20.0)),
])
def test_percentiles_segun_definicion(spark, metodo, esperado):
    df = spark.createDataFrame([("a", 0), ("b", 10), ("c", 20), ("d", 30)], "full_name string, total_references long")
    assert tuple(percentiles(df, metodo).first()) == esperado


@pytest.mark.parametrize("metodo", ["continuous", "nearest-rank"])
def test_percentiles_persona_unica_y_empates(spark, metodo):
    df = spark.createDataFrame([("a", 7), ("b", 7)], "full_name string, total_references long")
    assert tuple(percentiles(df, metodo).first()) == (7.0, 7.0, 7.0)
    assert tuple(percentiles(df.limit(1), metodo).first()) == (7.0, 7.0, 7.0)


def test_metodo_percentil_invalido(spark):
    df = spark.createDataFrame([], "full_name string, total_references long")
    with pytest.raises(ValueError, match="Método"):
        percentiles(df, "invalido")


def test_transformaciones_vacias(spark):
    df = tabla(spark)
    assert articulos_por_mes(df).count() == 0
    assert articulos_por_grupo(df).count() == 0
    assert areas_por_persona(df).count() == 0
    refs = referencias_por_persona(df)
    assert refs.count() == 0 and persona_con_mas_referencias(refs).count() == 0
    for metodo in ("continuous", "nearest-rank"):
        assert tuple(percentiles(refs, metodo).first()) == (None, None, None)


def test_escritura_un_archivo_encabezado_y_orden(spark, tmp_path):
    df = tabla(spark, articulo(fecha="2022-02-01"), articulo(fecha="2020-01-01"))
    destino = tmp_path / "meses"
    escribir_tabla(articulos_por_mes(df), destino, "csv")
    archivos = list(destino.glob("part-*.csv"))
    assert len(archivos) == 1
    assert archivos[0].read_text().splitlines() == [
        "created_year,created_month,total_articles", "2020,1,1", "2022,2,1",
    ]
    with pytest.raises(ValueError, match="Formato"):
        escribir_tabla(df, tmp_path / "otro", "xml")


def test_cadena_completa_relectura_parquet_y_repeticion(spark, tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    for i, mes in enumerate(("2021-01-01T00:00:00Z", "2021-02-01T00:00:00Z")):
        (entrada / f"{i}.json").write_text(json.dumps({"message": {
            "DOI": f"10/{i}", "author": [{"given": "Ana", "family": "Perez"}],
            "group-title": "Salud", "created": {"date-time": mes},
            "reference": [{"DOI": f"10/ref{i}"}],
        }}, indent=2))
    salida = tmp_path / "salida"
    resumen = ejecutar(spark, [str(entrada)], str(salida), particiones=2)
    assert resumen["documentos_json"] == resumen["articulos_releidos_parquet"] == 2
    assert resumen["maximo"] == [{"full_name": "Ana Perez", "total_references": 2}]
    assert resumen["percentiles"] == {"p25": 2.0, "p50": 2.0, "p75": 2.0}
    assert spark.read.parquet(str(salida / "crossref-parquet")).schema == SALIDA
    for nombre in ("articles_month_year", "research_group", "percentil_25", "percentil_50", "percentil_75"):
        assert len(list((salida / nombre).glob("part-*.csv"))) == 1
    for nombre in ("research_areas_per_person", "person_most_references"):
        assert len(list((salida / nombre).glob("part-*.json"))) == 1
    ganador = json.loads(next((salida / "person_most_references").glob("part-*.json")).read_text())
    assert ganador == {"full_name": "Ana Perez", "total_references": 2}
    with pytest.raises(FileExistsError):
        ejecutar(spark, [str(entrada)], str(salida))
    repeticion = ejecutar(spark, [str(entrada)], str(salida), sobrescribir=True)
    assert repeticion["maximo"] == resumen["maximo"]


def test_programa_entrada_vacia_y_particiones_invalidas(spark, tmp_path):
    entrada = tmp_path / "vacio"
    entrada.mkdir()
    with pytest.raises(ValueError, match="no contiene"):
        ejecutar(spark, [str(entrada)], str(tmp_path / "salida"))
    with pytest.raises(ValueError, match="particiones"):
        ejecutar(spark, [str(entrada)], str(tmp_path / "salida"), particiones=0)
