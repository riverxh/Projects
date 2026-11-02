\set ON_ERROR_STOP on
\pset pager off
-- Solo consultas; se ejecutan después de programa.py cargar.
SELECT 'territorios' AS tabla,count(*) AS filas FROM proyecto.territorios
UNION ALL SELECT 'construccion_cantonal',count(*) FROM proyecto.construccion_cantonal
UNION ALL SELECT 'poblacion_cantonal',count(*) FROM proyecto.poblacion_cantonal
UNION ALL SELECT 'destinos_cantonales',count(*) FROM proyecto.destinos_cantonales
UNION ALL SELECT 'integrado',count(*) FROM proyecto.integrado
UNION ALL SELECT 'predicciones',count(*) FROM proyecto.predicciones;

SELECT anio,count(*) AS agrupaciones,sum(obras_total) AS obras,sum(area_m2) AS area_m2,
       round(sum(poblacion)::numeric,2) AS poblacion
FROM proyecto.integrado GROUP BY anio ORDER BY anio;

SELECT codigo_agrupacion,agrupacion,anio,area_m2,poblacion,origen_construccion,origen_poblacion
FROM proyecto.integrado WHERE codigo_agrupacion IN ('101','203','601','607') AND anio=2024
ORDER BY codigo_agrupacion;

-- Cero filas: cruce inconsistente.
SELECT i.codigo_agrupacion,i.anio FROM proyecto.integrado i
JOIN proyecto.construccion_agrupada c USING(codigo_agrupacion,anio)
JOIN proyecto.poblacion_agrupada p USING(codigo_agrupacion,anio)
WHERE abs(i.area_m2-c.area_m2)>0.001 OR abs(i.poblacion-p.poblacion)>0.001;

SELECT modelo,count(*) AS n,round(avg(error_absoluto_m2)::numeric,2) AS mae_m2,
       round(sqrt(avg(error_m2*error_m2))::numeric,2) AS rmse_m2
FROM proyecto.predicciones GROUP BY modelo ORDER BY modelo;

SELECT modelo,anio_objetivo,count(*) AS n,
       round(avg(error_absoluto_m2)::numeric,2) AS mae_m2
FROM proyecto.predicciones GROUP BY modelo,anio_objetivo ORDER BY modelo,anio_objetivo;

SELECT table_name,column_name,data_type FROM information_schema.columns
WHERE table_schema='proyecto' ORDER BY table_name,ordinal_position;
