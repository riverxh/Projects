# Guion del video de T3

Duración objetivo: 6:30. Máximo permitido: 7:00.

Antes de grabar: notebook ejecutado, terminal con consulta SQL y texto legible. No esperar el entrenamiento durante la grabación.

## 0:00 a 0:35 Presentación y recorrido

En pantalla: Mostrar el título del notebook y el archivo compose.

Soy Adrian Rojas Rivera y esta es mi Tarea 3. Comparo regresión logística y bosque aleatorio para predecir abandono de clientes con Spark ML. El entorno tiene dos servicios: Jupyter con Spark y PostgreSQL. Voy a mostrar el recorrido desde el CSV hasta las predicciones guardadas, siguiendo el procedimiento visto en clase.

## 0:35 a 1:25 Datos y limpieza

En pantalla: Mostrar las secciones 2 y 3 del notebook, el esquema y los conteos.

Utilizo el CSV de ejemplo de L5. Tiene diez mil registros y la etiqueta indica cero para permanencia y uno para abandono. El identificador no se usa como predictor. Declaro los tipos de forma explícita y reviso nulos, dominios, registros corruptos y duplicados. También rechazo identificadores con versiones contradictorias. En este archivo no hubo filas rechazadas. Luego guardo las siete columnas originales en tarea3 y vuelvo a leerlas desde PostgreSQL para continuar.

## 1:25 a 2:10 Exploración y reserva

En pantalla: Mostrar los conteos de la sección 4 y los gráficos de la sección 5.

La separación por hash del identificador deja ocho mil setenta y nueve registros para entrenamiento y mil novecientos veintiuno para reserva final. Compruebo que no se solapen. La exploración utiliza solo entrenamiento: incluye estadísticas, histogramas y correlaciones. Los tickets de soporte tienen la asociación lineal más marcada con la etiqueta, pero eso no demuestra causalidad. Como los atributos tienen escalas diferentes, incorporo una estandarización.

## 2:10 a 3:25 Pipeline y validación cruzada

En pantalla: Mostrar las secciones 6 y 7 y las grillas de resultados.

Cada pipeline contiene VectorAssembler, StandardScaler y el clasificador. El escalador se ajusta dentro de cada fold para evitar utilizar su validación al calcular medias y desviaciones. Construyo cuatro folds equilibrados por clase y los paso a CrossValidator. Pruebo cuatro combinaciones por modelo y selecciono por AUC ROC media. Esto implica treinta y dos ajustes de validación y el reajuste de los dos mejores pipelines. La reserva no participa en esta búsqueda. También muestro las métricas de entrenamiento por separado para reconocer un posible ajuste demasiado optimista.

## 3:25 a 4:45 Resultados y comparación

En pantalla: Mostrar la tabla final y las matrices de confusión de la sección 8.

En reserva, la regresión obtiene AUC ROC de cero punto siete dieciocho y el bosque de cero punto siete veinte. La diferencia es pequeña. La regresión tiene mayor recall y F1: detecta cuatrocientos dos abandonos, frente a trescientos cuarenta y dos del bosque. El bosque genera menos falsas alertas: ciento setenta y nueve frente a doscientas veintiocho. Ambos superan la referencia de predecir siempre permanencia. Si interesa detectar más abandonos, consideraría la regresión; si pesa más evitar contactos innecesarios, revisaría la precisión del bosque. No ajusto el umbral con estos resultados y no afirmo superioridad universal.

## 4:45 a 5:50 Persistencia y comprobaciones

En pantalla: Mostrar la sección 9 y la salida de sql/Verificacion.sql en terminal.

Las tablas modelo1 y modelo2 contienen la misma reserva final, las siete columnas originales y prediccion. No guardo vectores de características ni probabilidades en SQL. Esta consulta confirma diez mil filas en tarea3 y mil novecientas veintiuna por modelo. También verifica los tipos, la correspondencia de atributos y las matrices de confusión. Repito las tres cargas con overwrite y comparo sus contenidos para demostrar que no se duplican registros. Las cinco pruebas automatizadas comprueban además las reglas de limpieza y las particiones.

## 5:50 a 6:30 Reproducción y cierre

En pantalla: Mostrar README y la sección 10 del notebook.

El paquete incluye Dockerfile, compose, datos, código, notebook ejecutado y el manual PDF. Para reproducirlo se inicia el entorno y se ejecuta todo el notebook, o se utiliza el script que guarda sus salidas. La principal limitación es que este CSV de ejemplo no documenta una población real. Los resultados describen este archivo y la reserva utilizada. El análisis del notebook explica los errores de ambos modelos y las decisiones del procedimiento.
