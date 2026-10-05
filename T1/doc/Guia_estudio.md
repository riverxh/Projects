# Comprender la solución antes de entregarla

## 1. Qué hace cada parte

`main.py` coordina el proceso: lee argumentos, crea Spark, llama a las funciones, imprime resultados y cierra la sesión. La lógica está en `functions/functions.py` para poder probarla por partes.

Las tres funciones `load_*` leen CSV sin encabezado. `StructType` reúne los campos y `StructField` define nombre y tipo. Para rutas se usa ahora `FloatType`, que aparece en el ZIP del profesor; así se preserva el esquema incluso si el archivo está vacío. La fecha se conserva como texto ISO, que identifica el día completo.

## 2. Cómo se relacionan las tablas

Una actividad contiene un código de ruta, una cédula y una fecha. La primera unión busca el nombre y la provincia mediante la cédula. La segunda busca nombre y distancia de la ruta mediante su código. Los alias indican de qué tabla sale cada columna.

Se usa `left` para conservar a todos los ciclistas en la tabla intermedia. Marta no tiene actividad: sus datos personales siguen presentes y los de ruta/actividad son `NULL`. Los cálculos excluyen distancias desconocidas, como hace el ejemplo del profesor. Esto es distinto de inventarle una actividad de cero kilómetros.

Con los datos completos hay 21 actividades y 22 filas unidas. La fila adicional pertenece a Marta.

## 3. Cómo se suman los kilómetros

`groupBy` reúne filas con las mismas claves. `sum` suma las distancias del grupo. Las claves cambian según la pregunta:

| Pregunta | Claves | Columna de salida |
|---|---|---|
| ¿Cuánto recorrió cada persona? | cédula, nombre, provincia | `total_km` |
| ¿Cuánto se recorrió por provincia? | provincia | `total_km` |
| ¿Cuánto se recorrió en cada fecha? | fecha completa | `total_km` |
| ¿Cuánto recorrió cada persona cada día? | cédula, nombre, provincia, fecha | `km_dia` |

La cédula impide mezclar dos personas con el mismo nombre. Dos actividades iguales se suman dos veces, porque representan dos recorridos.

## 4. Por qué el promedio requiere dos etapas

Ana recorre 10.5 + 10.5 km el 1 de octubre y 20.25 km el 3 de octubre. Primero se calculan sus totales diarios: 21.0 y 20.25. Después `mean` obtiene `(21.0 + 20.25) / 2 = 20.625`.

Promediar las tres actividades directamente produciría 13.75, que es un promedio por recorrido. Para esta entrega se documentó el criterio de días con actividad; el enunciado no define un intervalo de calendario para contar días sin recorridos.

## 5. Por qué el top es por provincia

`Window.partitionBy('provincia')` separa los rankings. Dentro de cada provincia se ordena por la métrica de mayor a menor. `dense_rank` asigna el mismo rango a valores empatados y no deja huecos entre rangos. Finalmente se conservan rangos menores o iguales a N.

La cédula se usa después para ordenar la presentación entre empatados; no se agrega a la ventana para romper el empate. En Alajuela, dos personas tienen 30 km y rango 5: ambas aparecen. Esto sigue el ejemplo del profesor y debe explicarse en la presentación.

## 6. Qué demuestran las pruebas

Las pruebas de unión preparan ciclistas, rutas y actividades pequeños en memoria. Las de agregación comienzan con una tabla que ya representa recorridos unidos. Las de ranking comienzan con totales o promedios preparados. Así, un fallo en una etapa no impide comprobar las demás.

El ejemplo completo se verifica además de forma integrada. Los totales por provincia suman 684 km y los totales diarios también. En San José los rankings por total y promedio tienen diferente orden y diferentes personas en el corte.

## 7. Comprobación de comprensión

Antes de grabar, explica con tus palabras:

1. Por qué `header=False` conserva a la primera persona del CSV.
2. Por qué hay 22 filas unidas si existen 21 actividades.
3. Por qué las dos primeras actividades de Ana no se eliminan como duplicados.
4. Por qué el promedio de Ana es 20.625 y no 13.75.
5. Por qué Alajuela tiene seis personas en un top de cinco rangos.
6. Por qué una persona con cero kilómetros puede participar y otra con kilómetros desconocidos no.
7. Qué función cambiarías si el profesor pidiera otro criterio de promedio o un máximo estricto de cinco personas.

## Ejecución en el contenedor que ya usaste

En la consola que muestra `(venv)` y `/t1`:

```bash
spark-submit main.py data/ciclista.csv data/ruta.csv data/actividad.csv
pytest
```

En la copia distribuida, el manual usa `/src`, que es el directorio de trabajo definido por el Dockerfile. Ambas formas ejecutan los mismos archivos.
