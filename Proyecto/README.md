# Construcción autorizada y dinámica poblacional en Costa Rica

Proyecto de Big Data, módulo 4. Adrián Rojas Rivera. Octubre de 2026.

El proyecto cruza publicaciones anuales de construcción del INEC con la población cantonal de la hoja C4 para 2015-2024. Predice el área autorizada del año siguiente con dos regresores de Spark y compara búsqueda textual y vectorial sobre cuatro investigaciones del Programa Estado de la Nación (PEN). Los textos se usan como contexto documental independiente.

El ZIP de entrega incluye los 15 originales. La copia para Git excluye únicamente el Excel completo de población, de aproximadamente 162 MB: si se clona el repositorio, copiar `data/originales/poblacion/Poblacion_2000_2050_INEC.xlsx` desde el ZIP a esa misma ruta antes de ejecutar. Su SHA-256 se comprueba en `config/fuentes.json`. El resto del código y los resultados es común a ambas copias.

## Ejecución desde una copia nueva

Requisitos: Docker Desktop en ejecución, Compose v2, conexión para descargar imágenes y el modelo público, y al menos 4 GB asignados a Docker. La prueba se hizo con 4 GB y 8 CPU en Docker; los servicios tienen límites de memoria. Reservar varios GB libres para imágenes, volúmenes y el modelo (~490 MB). No se requiere Python ni Java instalados en el host. Los puertos locales 8894, 9204 y 5604 deben estar libres.

Abrir una terminal en esta carpeta, la que contiene `docker-compose.yaml`, y ejecutar en orden:

```bash
docker compose up -d --build
docker compose exec -T app python scripts/descargar_modelo.py
docker compose exec -T app python -m pytest -q
docker compose exec -T app python programa.py todo
docker compose exec -T app python scripts/generar_analisis.py
docker compose exec -T app python scripts/ejecutar_notebook.py
```

La construcción inicial descarga dependencias. `todo` ejecuta ETL, ambos modelos, embeddings, cargas, consultas, dashboard y verificaciones. Si Kibana aún está iniciando, esperar a que abra su página y repetir únicamente `programa.py dashboard`. Las etapas imprimen su nombre y dejan registros estructurados en `output/`. Los archivos originales incluidos se validan con SHA-256; no hay que volver a descargarlos.

Accesos después de ejecutar:

- Dashboard: [Kibana](http://127.0.0.1:5604/app/dashboards#/view/cp-dashboard).
- Consultas: [Dev Tools](http://127.0.0.1:5604/app/dev_tools#/console).
- Notebook: [Jupyter](http://127.0.0.1:8894/lab), token de demostración `proyecto-local`.
- Elasticsearch: [estado local](http://127.0.0.1:9204/_cluster/health).

Los servicios se publican solo en la interfaz local. Las credenciales de ejemplo corresponden exclusivamente a este entorno de demostración. PostgreSQL se accede desde la red interna de Compose, base `proyecto`, usuario `estudiante`.

## Etapas y comprobaciones

Cada etapa puede repetirse sin ejecutar las demás:

```bash
docker compose exec -T app python programa.py preparar
docker compose exec -T app python programa.py entrenar
docker compose exec -T app python programa.py embeddings
docker compose exec -T app python programa.py cargar
docker compose exec -T app python programa.py buscar
docker compose exec -T app python programa.py dashboard
docker compose exec -T app python programa.py verificar
docker compose exec -T postgres psql -U estudiante -d proyecto < sql/Verificacion.sql
```

Dependencias: `entrenar` y `cargar` requieren `preparar`; `cargar` también requiere predicciones y embeddings; `buscar` y `dashboard` requieren la carga. El notebook revisa los resultados existentes y consulta ambas bases; no vuelve a entrenar. Spark transforma, agrupa, cruza y entrena; openpyxl interpreta los encabezados irregulares de Excel antes de formar los DataFrames.

`cargar` reemplaza únicamente el esquema SQL `proyecto` y los siete índices `cp-*` de esta instalación. Usa tablas de preparación antes de sustituir el esquema SQL dentro de una transacción. No usar estas conexiones para alojar otros trabajos con los mismos nombres. Repetir `cargar` y `verificar` conserva cantidades y contenido. El esquema SQL se crea mediante el programa; `sql/Esquema.sql` es su documentación ejecutable, no un paso adicional obligatorio.

Para detener conservando los datos: `docker compose stop`. Para iniciar de nuevo: `docker compose up -d`. Evitar `down -v` si se desean conservar los volúmenes. Los vectores se reutilizan por texto, prefijo, revisión del modelo y versiones de librerías. `embeddings_inicial.json` conserva la primera medición del corpus y `embeddings.json` la última ejecución.

## Cantidades esperadas

| Tabla de PostgreSQL, esquema proyecto | Filas |
|---|---:|
| territorios | 81 |
| construccion_cantonal | 818 |
| poblacion_cantonal | 840 |
| destinos_cantonales | 12 121 |
| construccion_agrupada | 810 |
| poblacion_agrupada | 810 |
| integrado | 810 |
| predicciones | 324 |

Elasticsearch: `cp-construccion` 818, `cp-poblacion` 840, `cp-destinos` 12 121, `cp-integrado` 810, `cp-predicciones` 324, `cp-texto` 298 y `cp-vector` 298. Los últimos dos conservan exactamente los mismos IDs y textos; solo el segundo agrega vectores de 384 componentes. El dashboard contiene cinco visualizaciones.

## Resultados medidos

La prueba predictiva 2023-2024 tiene 162 casos. La regresión lineal obtuvo MAE 11 790,68 m² y RMSE 22 202,14 m²; el bosque, MAE 13 783,18 m² y RMSE 26 836,64 m². La persistencia obtuvo RMSE 24 385,12 m². Sin embargo, **persistencia ganó en validación 2022**. El resultado no demuestra que un modelo aprendido sea siempre mejor.

Se conservaron 298 fragmentos en español de 194 páginas, con máximo real de 397 tokens, incluidos prefijo y especiales. La codificación inicial de pasajes tomó 33,94 s en este entorno. Las ocho consultas reservadas empataron en precisión@5 estricta (0,30); BM25 tuvo MRR 0,650 y vectores 0,625. No se afirma superioridad general del método vectorial. Consultar el análisis para las limitaciones temporales, territoriales y de relevancia.

## Archivos para revisar y presentar

- `output/pdf/Manual_proyecto.pdf`: ejecución y documentación completa.
- `doc/Presentacion_proyecto.pptx` y `doc/Guion_presentacion.md`: 15 diapositivas y recorrido de 20 minutos.
- `notebooks/Proyecto_Construccion_Poblacion.ipynb`: notebook con salidas ejecutadas.
- `doc/Analisis_resultados.md`: comparación de modelos, búsquedas y límites.
- `doc/Esquemas.md`, `sql/Esquema.sql`, `elastic/*mapping.json`: diagramas, campos y estructuras.
- `elastic/Consultas_Kibana.http`: copiar cada bloque completo en Dev Tools y ejecutarlo con el cursor dentro del bloque. Incluye consultas vectoriales completas Q03, Q09 y Q13.
- `kibana/dashboard.ndjson`: exportación nativa de siete objetos. Puede importarse en Stack Management > Saved Objects después de cargar los índices; el programa principal ya los crea automáticamente.
- `config/relevancia.json`, `doc/Criterio_relevancia.md`: 110 juicios documentados. Si se cambian consultas, modelo o fragmentación y aparecen IDs nuevos, revisar el pool y añadir juicios antes de calcular métricas; no asignar relevancia automáticamente.
- `doc/Fuentes_y_procedimientos.md`, `doc/Validacion.md`, `doc/Lista_entrega.md`: fuentes, evidencia y cierre de entrega.

Los resultados CSV/JSON, vectores y notebook se incluyen como evidencia. Los Parquet intermedios, modelos Spark serializados, cachés y volúmenes se regeneran; se excluyen del paquete para evitar archivos voluminosos y duplicados. `requirements.lock.txt` fija el entorno efectivamente probado; `requirements.txt` expresa las dependencias principales.

## Problemas frecuentes

- Si Docker no responde, iniciar Docker Desktop antes de Compose.
- Si faltan pesos o el tokenizador, ejecutar primero `scripts/descargar_modelo.py`; la descarga usa el modelo público sin token personal.
- Si un puerto está ocupado, detener el servicio que lo utiliza o cambiar el puerto del lado izquierdo en Compose y ajustar los enlaces del navegador.
- Si la máquina se queda sin memoria, cerrar otros contenedores y mantener los límites definidos; no aumentar lotes sin medir.
- Si un panel no muestra datos, restaurar el intervalo 01/01/2015 a 31/12/2024 en hora de Costa Rica, quitar filtros de ensayos y verificar los índices.
- Los controles de búsqueda sin respuesta también devuelven vecinos. Un score alto no acredita pertinencia ni vigencia normativa.
