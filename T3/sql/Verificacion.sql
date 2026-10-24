\set ON_ERROR_STOP on
\pset pager off
-- Ejecutar después del notebook. Todas las consultas son de lectura.
SELECT 'tarea3' AS tabla, count(*) AS filas, count(DISTINCT id) AS ids_unicos FROM tarea3
UNION ALL SELECT 'modelo1', count(*), count(DISTINCT id) FROM modelo1
UNION ALL SELECT 'modelo2', count(*), count(DISTINCT id) FROM modelo2;

SELECT table_name, ordinal_position, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name IN ('tarea3','modelo1','modelo2')
ORDER BY table_name, ordinal_position;

-- Debe ser cero: atributos originales de cada predicción que no coinciden con tarea3.
SELECT 'modelo1' AS tabla, count(*) AS filas_sin_correspondencia FROM
(SELECT id,edad,gasto_mensual,tickets_soporte,meses_cliente,usa_app,etiqueta FROM modelo1
 EXCEPT ALL SELECT id,edad,gasto_mensual,tickets_soporte,meses_cliente,usa_app,etiqueta FROM tarea3) AS d
UNION ALL SELECT 'modelo2', count(*) FROM
(SELECT id,edad,gasto_mensual,tickets_soporte,meses_cliente,usa_app,etiqueta FROM modelo2
 EXCEPT ALL SELECT id,edad,gasto_mensual,tickets_soporte,meses_cliente,usa_app,etiqueta FROM tarea3) AS d;

-- Debe ser cero: los dos modelos deben evaluar los mismos ID.
SELECT count(*) AS ids_distintos_entre_modelos FROM
((SELECT id FROM modelo1 EXCEPT SELECT id FROM modelo2)
 UNION ALL (SELECT id FROM modelo2 EXCEPT SELECT id FROM modelo1)) AS d;

-- Debe ser cero: predicciones nulas o fuera del dominio.
SELECT 'modelo1' AS tabla, count(*) AS predicciones_invalidas FROM modelo1 WHERE prediccion IS NULL OR prediccion NOT IN (0,1)
UNION ALL SELECT 'modelo2', count(*) FROM modelo2 WHERE prediccion IS NULL OR prediccion NOT IN (0,1);

-- Matrices de confusión en filas. Coinciden con las salidas del notebook.
SELECT 'modelo1' AS modelo, etiqueta, prediccion, count(*) AS registros FROM modelo1 GROUP BY etiqueta,prediccion
UNION ALL SELECT 'modelo2', etiqueta, prediccion, count(*) FROM modelo2 GROUP BY etiqueta,prediccion
ORDER BY modelo,etiqueta,prediccion;

SELECT * FROM tarea3 ORDER BY id LIMIT 5;
SELECT * FROM modelo1 ORDER BY id LIMIT 5;
SELECT * FROM modelo2 ORDER BY id LIMIT 5;
