# Lista de entrega del proyecto

Fecha del curso: lunes 2 de noviembre de 2026 antes de las 19:00, hora de Costa Rica. Presentación: 20 minutos más preguntas.

| Requisito | Archivo o evidencia preparada |
|---|---|
| Dos fuentes cruzables y texto adicional | config/fuentes.json; 15 originales incluidos |
| Extracción y transformaciones Spark | functions/datos.py; output/etl.json |
| Pruebas antes de materializar | tests/test_proyecto.py; 15 pruebas aprobadas |
| Fuentes antes y después del cruce en dos motores | functions/materializacion.py; output/verificacion_bases.json |
| Diagramas, esquemas y mappings | doc/Esquemas.md; sql/Esquema.sql; elastic/*mapping.json |
| Dos modelos Spark con validación | functions/modelos.py; output/modelos.json; particiones y decisiones previas |
| Análisis de cada modelo y comparación | doc/Analisis_resultados.md; CSV y gráficos en output/ |
| Búsquedas con y sin vectores en Kibana | elastic/Consultas_Kibana.http; capturas y métricas; 110 juicios |
| Dashboard con cinco visualizaciones | kibana/dashboard.ndjson; capturas y acceso local |
| Notebook con resultados | notebooks/Proyecto_Construccion_Poblacion.ipynb, ejecutado |
| PDF con ejecución y documentación | output/pdf/Manual_proyecto.pdf, 12 páginas |
| Presentación | doc/Presentacion_proyecto.pptx, 15 diapositivas; guion de 20 minutos |
| Paquete reproducible | ZIP con fuentes, código, resultados y manifiesto SHA-256 |

## Pasos externos y personales

1. Publicar esta entrega en la carpeta del proyecto del repositorio del curso y verificar su contenido.
2. Subir el ZIP a Drive u OneDrive y comprobar el acceso de los destinatarios.
3. Completar el correo con ambos enlaces usando el formato indicado en la primera lección y enviarlo antes de la fecha límite.
4. Revisar los juicios de relevancia y ensayar el guion, especialmente los límites de la validación, la persistencia y los casos donde BM25 supera a vectores.
5. Antes de exponer, iniciar el entorno, restaurar el periodo completo y quitar filtros del ensayo. La exposición ocurre en clase; el proyecto no exige el video de siete minutos que correspondía a T3.

Esta lista distingue material preparado de acciones externas. No certifica un envío de correo ni una presentación ya realizados.
