# Fuentes y procedimientos del curso

## Material docente aplicado

Las referencias de grabación identifican intervalos aproximados, no citas literales de una transcripción automática.

| Fuente del curso | Procedimiento utilizado |
|---|---|
| Enunciado distribuido en L4 | Dos fuentes cruzables, texto adicional permitido, Spark, pruebas antes de materializar, PostgreSQL y Elasticsearch, dos modelos, notebook, PDF, dashboard de cinco visualizaciones y presentación de 20 minutos |
| L4 | Compose, servicios, conectores, mappings, dimensiones e idioma del modelo, materialización y relectura |
| L4 | Preparar texto, generar embeddings con Hugging Face, guardar vectores y reutilizarlos |
| L4 | Consultas textuales y kNN; comparar casos concretos y explicar pertinencia |
| L5 | Separar preparación y pruebas de carga; petición de K-fold también para el proyecto, usando CrossValidator de Spark |
| L5 | Compartir trabajo, agrupar por claves y escoger puntos de materialización |
| L5 | Batch adecuado para publicaciones anuales almacenadas |
| L5 | Evaluar codificación por lotes; se eligieron lotes pequeños medidos, no se traslada el tiempo del ejemplo al equipo propio |
| Feedback del anteproyecto, Gerardo Nereo Campos Araya, correo del 25/10/2026 | Control del volumen, límite de 512 tokens, chunking para evitar truncamiento; subconjunto aceptable si el tiempo fuera excesivo |

Aplicación concreta del feedback: cuatro PDF completos como fuentes, selección de cuerpo y anexo pertinente, auditoría de exclusiones, fragmentación con tokenizador E5 hasta 400 tokens incluyendo prefijo y especiales, solapamiento aproximado de 40 tokens, máximo observado 397, lotes de cuatro y caché. La elección 400/40 es del proyecto; no se presenta como valor exigido por el docente.

La CV de tres folds por territorio se complementa con validación cronológica 2022 y prueba 2023-2024. La CV mezcla años dentro de desarrollo: no se confunde con validación temporal. La escala se ajusta dentro de cada fold.

## Datos originales

Los 15 archivos originales y sus URLs/hashes exactos están en `config/fuentes.json`. Se incluyen para repetir la ejecución sin depender de accesos restringidos posteriores.

- INEC: 10 publicaciones anuales de estadísticas de construcción, 2015-2024, archivos Excel con desagregación cantonal y destino. Se usan obras autorizadas, área nueva/ampliada y valor nominal.
- INEC: serie de estimaciones y proyecciones de población, hoja C4, recorte 2015-2024. [Ficha de la fuente](https://admin.inec.cr/node/56328). La serie y versión se conservan tal como fueron descargadas; no se sustituyen por microdatos restringidos.
- Sánchez Hernández, Leonardo (2017), *Tendencias de crecimiento en ciudades intermedias. Los casos de San Isidro de El General, Ciudad Quesada y Guápiles*. [PEN/CONARE](https://repositorio.conare.ac.cr/items/9ece2768-86f1-445e-9dae-0193d2f31606).
- Sánchez Hernández, Leonardo (2018), *Tendencias y patrones del crecimiento urbano en la GAM, implicaciones sociales, económicas y ambientales y desafíos desde el ordenamiento territorial*. [PEN/CONARE](https://repositorio.conare.ac.cr/items/f359815a-d0fb-47cc-b981-5ad3f0a4b0b0).
- Sánchez Hernández, Leonardo (2021), *Ordenamiento territorial y crecimiento urbano: desafíos e impactos para las ciudades intermedias y la zona marino costera*. [PEN/CONARE](https://repositorio.conare.ac.cr/items/f93f1d77-df0d-4635-b790-003ea2e7bb6b).
- Pérez Molina, Eduardo (2023), *Ordenamiento territorial: impactos de la regulación territorial en la Gran Área Metropolitana*. [PEN/CONARE](https://repositorio.conare.ac.cr/items/61b3536b-3de6-4fde-a003-c2c15e976387).

Los documentos PEN pueden citar otras series, como CFIA. No se suman sus cifras a los permisos INEC ni se usan documentos futuros como predictores. Las tablas del anexo 2021 se indexan como texto con maquetación; no certifican vigencia regulatoria actual.

## Referencias técnicas

- [Modelo E5 multilingüe](https://huggingface.co/intfloat/multilingual-e5-small). Revisión fija `614241f622f53c4eeff9890bdc4f31cfecc418b3`, prefijos `passage:` / `query:`, 384 dimensiones y máximo de 512 tokens.
- [Spark: selección y validación de modelos](https://spark.apache.org/docs/3.5.7/ml-tuning.html). La implementación probada usa Spark 3.5.1; los parámetros concretos están en `functions/modelos.py` y `output/modelos.json`.
- [Kibana 8.14: Vega](https://www.elastic.co/guide/en/kibana/8.14/vega.html), para paneles con filtros y periodo globales.
- [Kibana 8.14: importación de objetos](https://www.elastic.co/guide/en/kibana/8.14/saved-objects-api-import.html), para la exportación nativa de respaldo.

Las capturas del dashboard y las métricas proceden de esta ejecución. Los ejemplos de clase orientan el procedimiento; los códigos territoriales, reglas de limpieza, modelo español y criterios de evaluación corresponden a las fuentes de este proyecto.
