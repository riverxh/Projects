"""Esquemas explícitos según el punto 1 de T2. Generado con ayuda de IA."""

from pyspark.sql.types import (
    ArrayType, BooleanType, StringType, StructField, StructType,
)


def textos(*nombres):
    return [StructField(nombre, StringType(), True) for nombre in nombres]


INSTITUCION = StructType(textos("name"))
AUTOR = StructType([
    StructField("ORCID", StringType(), True),
    StructField("affiliation", ArrayType(INSTITUCION, True), True),
    StructField("authenticated-orcid", BooleanType(), True),
    *textos("family", "given", "name", "sequence", "suffix"),
])
REFERENCIA = StructType(textos(
    "DOI", "ISSN", "article-title", "author", "doi-asserted-by", "first-page",
    "issn-type", "issue", "journal-title", "key", "unstructured", "volume",
    "volume-title", "year",
))
ENLACE = StructType(textos(
    "URL", "content-type", "content-version", "intended-application",
))
MENSAJE = StructType([
    StructField("DOI", StringType(), True),
    StructField("author", ArrayType(AUTOR, True), True),
    StructField("institution", ArrayType(INSTITUCION, True), True),
    StructField("group-title", StringType(), True),
    StructField("created", StructType(textos("date-time")), True),
    StructField("prefix", StringType(), True),
    StructField("reference", ArrayType(REFERENCIA, True), True),
    StructField("link", ArrayType(ENLACE, True), True),
    StructField("subtype", StringType(), True),
])
ENTRADA = StructType([StructField("message", MENSAJE, True)])
SALIDA = StructType([
    StructField("doi", StringType(), True),
    StructField("author", ArrayType(AUTOR, True), True),
    StructField("inst", ArrayType(INSTITUCION, True), True),
    *textos("groupTitle", "createdDate", "prefix"),
    StructField("reference", ArrayType(REFERENCIA, True), True),
    StructField("link", ArrayType(ENLACE, True), True),
    StructField("subtype", StringType(), True),
])
