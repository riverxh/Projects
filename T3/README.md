# Tarea 3 Clasificación binaria con Spark ML

Adrian Rojas Rivera · Cédula 117550336 · Modalidad individual

Predicción de abandono con el CSV de ejemplo de L5. El notebook carga y depura datos en Spark, escribe `tarea3` en PostgreSQL, vuelve a leerla, reserva datos y compara regresión logística y bosque aleatorio con validación cruzada de cuatro folds. Persiste las predicciones finales en `modelo1` y `modelo2`.

## Inicio rápido

Se necesita Docker Desktop iniciado y Docker Compose v2. No es necesario instalar Python, Java, Spark, PostgreSQL o Jupyter en el equipo. Se recomienda asignar a Docker al menos 4 GB de memoria y dos CPU; cerrar otros entornos pesados. La primera construcción requiere Internet para descargar las imágenes y dependencias. El dataset está incluido.

Abra una terminal dentro de esta carpeta `T3` (donde están Dockerfile y docker-compose.yaml):

```bash
docker compose up -d --build
docker compose ps
```

Espere a que `postgres` figure como `healthy` y `bigdata` como `Up`. Abra:

http://127.0.0.1:8893/lab?token=tarea3-local

El token predeterminado es `tarea3-local`. Abra `notebooks/Tarea_3.ipynb`. El archivo entregado ya contiene salidas. Para reproducirlo, use **Kernel → Restart Kernel and Run All Cells**, espere el mensaje **Ejecución terminada y tablas verificadas** y guarde el notebook.

Como alternativa, el siguiente comando reinicia el mismo notebook mediante un kernel nuevo y guarda automáticamente las salidas:

```bash
docker compose exec -T bigdata python scripts/ejecutar_notebook.py
```

No ejecute ambas modalidades a la vez. El notebook termina su sesión Spark al finalizar. El tiempo depende del equipo; la ejecución comprobada se registra en `output/Resumen_ejecucion.json`. La descarga inicial puede tardar bastante más que el entrenamiento.

## Verificación de PostgreSQL

Desde una terminal en `T3`, después de ejecutar el notebook:

```bash
docker compose exec -T postgres psql -U estudiante -d tarea3 -f /dev/stdin < sql/Verificacion.sql
```

En PowerShell, si la redirección anterior no funciona:

```powershell
Get-Content sql/Verificacion.sql | docker compose exec -T postgres psql -U estudiante -d tarea3
```

Las tablas esperadas son:

| Tabla | Filas en el archivo incluido | Columnas |
|---|---:|---|
| tarea3 | 10000 | id, edad, gasto_mensual, tickets_soporte, meses_cliente, usa_app, etiqueta |
| modelo1 | 1921 | Las siete anteriores y prediccion |
| modelo2 | 1921 | Las siete anteriores y prediccion |

Las tablas de modelos contienen únicamente la reserva final. Los tipos son texto para ID, enteros para los indicadores y conteos, y double precision para gasto_mensual. Los vectores de Spark no se persisten. Las escrituras usan overwrite; el notebook comprueba igualdad del contenido antes y después de repetir las tres cargas.

## Pruebas

```bash
docker compose exec -T bigdata pytest -q --junitxml=output/Pruebas.xml
```

Las pruebas cubren registros inválidos, duplicados y conflictos de ID; reserva disjunta y estable; folds por clase; datos insuficientes para K; y salida tabular sin vectores. La ejecución integral del notebook verifica además el recorrido JDBC, las predicciones y la repetición de cargas. Consulte `doc/Validacion.md`.

## Estructura

- `notebooks/Tarea_3.ipynb`: desarrollo y análisis con salidas, gráficos y métricas.
- `functions/procesamiento.py`: operaciones Spark de preparación, partición, aprendizaje y persistencia.
- `data/dataset.csv` y `data/Fuente.json`: entrada suministrada en clase e identidad del archivo.
- `Dockerfile`, `docker-compose.yaml`, `requirements.txt`: entorno de ejecución.
- `scripts/ejecutar_notebook.py`: ejecución completa y guardado de salidas.
- `sql/Verificacion.sql`: consultas para calificar las tres tablas.
- `tests/`: pruebas de las reglas y particiones.
- `output/pdf/Manual_Tarea_3.pdf`: instrucciones completas para calificación.
- `doc/Manual_Tarea_3.docx`: manual editable.
- `doc/Guion_video_Tarea_3.docx` y `doc/Guion_video.md`: guía para un video de hasta siete minutos.
- `doc/Fuentes.md`, `doc/Validacion.md`: referencias y evidencia de comprobación.
- `output/`: resultados, figuras, particiones y pipelines entrenados generados al ejecutar.

## Decisiones del modelo

Se excluye `id` como predictor. Se usan cinco atributos y la etiqueta binaria 0 permanece / 1 abandona. Un hash estable de ID y semilla 27 reserva aproximadamente 20%; quedaron 8079 registros para entrenamiento y 1921 para evaluación final. El entrenamiento se divide en cuatro folds equilibrados por clase.

Ambos pipelines contienen VectorAssembler, StandardScaler y clasificador. El escalador se ajusta dentro de cada fold para evitar usar su validación al estimar media y desviación. La búsqueda usa cuatro combinaciones por modelo, AUC ROC de CV y la misma reserva final. Se comparan también AUC PR, accuracy, precision, recall, F1 positivo y matrices de confusión. El umbral queda en 0,5; no se ajusta con la reserva.

El CSV es un ejemplo del curso sin población real ni mecanismo de generación documentados. Sus resultados no se generalizan automáticamente a una empresa real. Las referencias al ejemplo y las clases están en `doc/Fuentes.md`.

## Configuración y cierre

Valores locales predeterminados: host SQL interno `postgres`, puerto interno 5432, base `tarea3`, usuario `estudiante`, clave `tarea3_local`. PostgreSQL no publica un puerto al equipo. Jupyter se publica solo en 127.0.0.1:8893. La interfaz Spark usa 127.0.0.1:4043 mientras el notebook está ejecutándose.

Opcionalmente, copie `.env.example` a `.env` y cambie POSTGRES_PASSWORD/JUPYTER_TOKEN antes del primer arranque. Si cambia la contraseña de un volumen PostgreSQL ya creado, debe actualizarla también en la base; cambiar solo la variable no cambia el usuario existente.

Para detener sin borrar las tablas:

```bash
docker compose down
```

Para volver a iniciar:

```bash
docker compose up -d
```

El volumen conserva PostgreSQL y la carpeta local conserva notebook y resultados. `docker compose down -v` elimina la base de este entorno; úselo únicamente si desea reiniciarla y volver a ejecutar el notebook.

## Si algo falla

- Docker no responde: inicie Docker Desktop y espere a que esté listo.
- Puerto 8893 ocupado: cambie solo el puerto a la izquierda de `8893:8888` en compose y abra ese nuevo puerto; recree el servicio con `docker compose up -d`.
- PostgreSQL no está healthy: revise `docker compose logs postgres`; espere su inicialización.
- Conexión JDBC fallida: ejecute desde el servicio bigdata, no desde Python del equipo. Verifique `docker compose ps` y los valores POSTGRES de ambos servicios.
- Memoria insuficiente o kernel terminado: cierre otros contenedores, asigne más memoria a Docker, reinicie el kernel y ejecute todo desde el principio.
- Columnas o tablas no aparecen: la base se crea al arrancar, las tablas al ejecutar el notebook.
- Vea los logs con `docker compose logs --tail=80 bigdata postgres`. Una advertencia de biblioteca nativa Hadoop en este entorno local no significa que la tarea haya fallado; compruebe el mensaje final y las consultas SQL.
