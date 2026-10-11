# Guion del video de la Tarea 2

Objetivo 6:30. Límite 7 minutos. Preparado con ayuda de IA. Consultar el Word para la preparación y los comandos completos.

## 0 a 20 segundos — Presentación

**Pantalla:** README de T2, título y procedencia.

**Narración sugerida:** Soy Adrian Rojas Rivera y presento la Tarea 2 de Big Data. El programa procesa artículos Crossref, genera Parquet y calcula métricas de artículos, áreas y referencias. Para preparar el código, las pruebas y la documentación utilicé Codex; esa participación está declarada en el repositorio.

## 20 segundos a 1 minuto — Ambiente y estructura

**Pantalla:** README, Dockerfile y programa.py.

**Narración sugerida:** El entorno comprobado utiliza Python 3.10, Java 17, PySpark 4.2.0 y pytest 9.1.1. El Dockerfile parte del Full Container del curso. programa.py recibe las rutas y coordina la ejecución; esquemas.py define los tipos y procesamiento.py contiene las transformaciones. Jupyter se usó para explorar, pero el programa principal se ejecuta directamente con Spark.

## 1 minuto a 1 minuto 40 segundos — JSON y relectura de Parquet

**Pantalla:** leer_json y proyectar en procesamiento.py; luego ejecutar en programa.py.

**Narración sugerida:** Cada JSON contiene un objeto message y se lee con multiLine y un esquema explícito. Se seleccionan las nueve columnas solicitadas, conservando autores, instituciones, referencias y enlaces como estructuras anidadas. Después de escribir Parquet se hace una nueva lectura con spark.read.parquet. Todas las métricas reciben esa nueva tabla. También se comprueba que conserve la cantidad inicial de documentos.

## 1 minuto 40 segundos a 2 minutos 10 segundos — Artículos por mes y grupo

**Pantalla:** articulos_por_mes y articulos_por_grupo.

**Narración sugerida:** Para los meses se utiliza createdDate en UTC y se cuentan documentos, sin multiplicarlos por autores. El resultado se ordena por año y mes. Para los grupos se cuentan DOI distintos, de modo que un artículo repetido no aumente el total dentro del mismo grupo. Las fechas inválidas se conservan en el grupo nulo.

## 2 minutos 10 segundos a 2 minutos 45 segundos — Nombres y áreas

**Pantalla:** personas_por_articulo y areas_por_persona.

**Narración sugerida:** El nombre se forma con given y family y se aplica trim. Un resultado vacío se reemplaza por unknown. Se eliminan nombres repetidos dentro del artículo. Las áreas se obtienen como un conjunto de grupos por persona, sin repetidos; total es el tamaño de esa lista. El orden principal es por cantidad descendente. La identificación por nombre puede agrupar homónimos.

## 2 minutos 45 segundos a 3 minutos 30 segundos — Referencias y percentiles

**Pantalla:** referencias_por_persona, persona_con_mas_referencias y percentiles.

**Narración sugerida:** Solo se consideran referencias con DOI válido. El modo predeterminado cuenta DOI distintos por persona. Se eligió porque Florian Krammer tiene 3869 entradas con DOI, pero 2701 DOI distintos, que coincide con el ejemplo del enunciado. Es una interpretación documentada. Se excluyen unknown y las personas con cero referencias del máximo y de los percentiles. Los percentiles se calculan sobre toda esa población, antes de escoger el máximo, con el método continuo exacto de Spark. Estas decisiones tienen opciones alternativas.

## 3 minutos 30 segundos a 4 minutos 10 segundos — Pruebas y excepciones

**Pantalla:** tests/test_procesamiento.py y después Terminal.

**Narración sugerida:** Las pruebas usan casos pequeños con resultados esperados: lectura, tipos anidados, duplicados, nulos, nombres, referencias, empates, percentiles y entradas inválidas. La prueba de integración ejecuta la cadena completa, relee Parquet y comprueba la protección contra reemplazos. Ahora ejecuto pytest desde la raíz del proyecto.

## 4 minutos 10 segundos a 5 minutos 20 segundos — Ejecución completa

**Pantalla:** Terminal dentro de /t2. Ejecutar el programa y explicar mientras trabaja.

**Narración sugerida:** Ejecuto Spark con el directorio del dataset y dos hilos locales. overwrite reemplaza las salidas anteriores para repetir la demostración. El programa lee los JSON, escribe Parquet, lo relee y genera las demás salidas. Se redujo el tamaño de los lotes de lectura para trabajar con arreglos grandes de referencias. Espero al mensaje Finalizado antes de revisar los resultados.

## 5 minutos 20 segundos a 6 minutos — Resultados

**Pantalla:** Resumen, máximo, tres percentiles y primera parte del CSV mensual.

**Narración sugerida:** En esta ejecución deben coincidir los documentos JSON y las filas releídas del Parquet. La validación guardada registró 31 458 en ambas etapas. El máximo predeterminado fue Florian Krammer con 2701; los percentiles fueron 21, 36 y 64. Cada CSV y JSON tiene un archivo de datos part, además de metadatos. El contraste independiente con el ZIP coincidió también en meses, grupos y áreas.

## 6 minutos a 6 minutos 30 segundos — Documentación y cierre

**Pantalla:** Manual Word, doc/Validacion.md y declaración del README.

**Narración sugerida:** El manual explica el entorno, los comandos, las salidas y las decisiones ambiguas. Las evidencias documentan las 23 pruebas y la validación del dataset. El repositorio contiene código, pruebas y documentación; los datos completos se obtienen del material del curso. La procedencia de IA está reconocida y el manual Word debe exportarse al formato solicitado para la entrega. Gracias.
