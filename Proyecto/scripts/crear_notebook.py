from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
n = nbf.v4.new_notebook()
n.metadata = {"kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s))
def code(s): cells.append(nbf.v4.new_code_cell(s))
md("""# Construcción autorizada y dinámica poblacional en Costa Rica
**Adrian Rojas Rivera · Big Data · Proyecto final**

El flujo reproducible se ejecuta con `programa.py`: preparación de Excel en Spark, dos regresores, corpus PEN, Hugging Face, PostgreSQL y Elasticsearch. Este cuaderno muestra sus resultados y comprueba los destinos reales. Las explicaciones completas están en el manual y `doc/Analisis_resultados.md`.

Objetivo predictivo: estimar el área autorizada del año siguiente. Objetivo documental: recuperar fragmentos históricos en español y comparar BM25 con vectores sobre el mismo corpus. Los permisos no equivalen a obras terminadas.""")
code("""from pathlib import Path
import sys, json
ROOT = Path.cwd()
if not (ROOT / 'config').is_dir(): ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import numpy as np
from IPython.display import display, Image, Markdown
from functions.entorno import iniciar_spark
from functions.materializacion import es_request, JDBC, PROPS
O = ROOT / 'output'
spark = iniciar_spark()
spark.sparkContext.setLogLevel('ERROR')
print('Spark', spark.version)
print('Etapas del programa: preparar, entrenar, embeddings, cargar, buscar, dashboard, verificar')
""")
md("## 1. Fuentes, esquema y cruce en Spark\nConstrucción 2015–2024 y población C4 del INEC. Se agregan Grecia/Río Cuarto, Puntarenas/Monteverde y Golfito/Puerto Jiménez. Los signos se conservan como ausencia, sin imputación automática a cero.")
code("""etl = json.loads((O / 'etl.json').read_text())
display(pd.DataFrame(list(etl['filas'].items()), columns=['conjunto','filas']))
df = spark.read.parquet(str(ROOT/'data/preparados/integrado'))
df.printSchema()
display(df.filter('anio=2024').orderBy('codigo_agrupacion').limit(5).toPandas())
display(pd.read_csv(O/'reconciliacion_nacional.csv'))""")
code("display(Image(filename=str(O/'graficos/evolucion_area.png')))")
md("## 2. Diseño temporal y K-fold\nLos predictores usan únicamente los dos años anteriores al objetivo. K-fold agrupa territorios dentro de 2017–2021 y mezcla esos años: es un diagnóstico territorial, no una validación cronológica. La validación temporal es 2022 y la prueba reservada 2023–2024. Las versiones revisadas de las fuentes limitan la interpretación como pronóstico en tiempo real.")
code("""display(Image(filename=str(O/'graficos/evaluacion_temporal.png')))
display(pd.read_csv(O/'cv_particiones.csv'))
display(pd.read_csv(O/'casos_supervisados.csv', dtype={'codigo_agrupacion':str}).head())""")
md("## 3. Pipelines y selección\nVectorAssembler, StandardScaler, regresor y transformación inversa del objetivo logarítmico. El escalador se ajusta dentro de cada fold. Ambos regresores comparan cuatro configuraciones; se selecciona por RMSE en m². La referencia de persistencia usa el área del año anterior.")
code("""display(pd.read_csv(O/'validacion_cruzada.csv'))
display(pd.read_csv(O/'validacion_modelos.csv'))
display(Markdown('**Decisión previa a la prueba:** ' + json.loads((O/'decisiones_antes_prueba.json').read_text())['criterio']))""")
md("## 4. Prueba final y diferencias\nLa lineal obtiene menor MAE y RMSE global en 2023–2024. En 2022 la persistencia había superado a ambos regresores; en 2023 aún conserva menor MAE que la lineal. La comparación no acredita superioridad universal. El historial de áreas domina las dos representaciones; coeficientes e importancias no son efectos causales.")
code("""display(pd.read_csv(O/'metricas_modelos.csv'))
display(Image(filename=str(O/'graficos/errores_modelos.png')))
display(Image(filename=str(O/'graficos/observado_predicho.png')))
display(pd.read_csv(O/'errores_territorio.csv', dtype={'codigo_agrupacion':str}).head(10))""")
md("## 5. Feedback y corpus PEN\nLa preparación conserva referencias de documento, año y página. El límite de 400 tokens incluye prefijo y tokens especiales. El modelo E5 tiene 384 dimensiones; se usan passage: y query:. Se excluyen párrafos dudosos con un registro de cambios. Los anexos 2021 se conservan con maquetación textual por página y requieren revisar el PDF para interpretar filas municipales.")
code("""emb = json.loads((O/'embeddings.json').read_text())
display(pd.DataFrame({'documento':list(emb['por_documento']), 'fragmentos':list(emb['por_documento'].values())}))
print('Páginas:',emb['paginas_originales'],'incluidas:',emb['paginas_incluidas'],'máximo tokens:',emb['tokens_max'])
with np.load(O/'embeddings.npz', allow_pickle=False) as vv:
    print('Forma:',vv['vectores'].shape,'Normas:',np.linalg.norm(vv['vectores'],axis=1).min(),np.linalg.norm(vv['vectores'],axis=1).max())
frags = [json.loads(line) for line in (O/'fragmentos.jsonl').read_text().splitlines()]
f = next(x for x in frags if x['documento_id']=='PEN_2017_CIUDADES' and x['pagina_pdf']==40)
display(Markdown(f"**{f['documento_id']} · página PDF {f['pagina_pdf']}**\\n\\n{f['texto']}\\n\\n[Fuente]({f['url_fuente']})"))""")
md("## 6. Bases de datos reales\nSe releen las tablas SQL y se consultan ambos índices. La ejecución repetida conserva conteos y contenidos. Los nombres del esquema y de los índices pertenecen exclusivamente a este proyecto.")
code("""for table in ['construccion_cantonal','poblacion_cantonal','integrado','predicciones']:
    stored = spark.read.jdbc(JDBC, 'proyecto.'+table, properties=PROPS)
    print('PostgreSQL',table,stored.count())
print('Elasticsearch texto:',es_request('GET','cp-texto/_count')['count'])
print('Elasticsearch vectores:',es_request('GET','cp-vector/_count')['count'])
print('Mapping del vector:',es_request('GET','cp-vector/_mapping')['cp-vector']['mappings']['properties']['embedding'])""")
md("## 7. Comparación de búsquedas\nSe revisaron 110 pares consulta-fragmento sin método ni score durante la lectura. Grados: 2 respuesta directa, 1 contexto parcial, 0 no pertinente. Hay cuatro consultas de desarrollo, ocho de reserva y dos controles sin respuesta. No hay segundo anotador independiente ni etiquetas exhaustivas del corpus.")
code("""display(pd.read_csv(O/'resumen_busqueda.csv'))
display(Image(filename=str(O/'graficos/comparacion_busquedas.png')))
results = json.loads((O/'resultados_busqueda.json').read_text())
for r in results:
    if r['id'] in ['Q01','Q03','Q11']:
        display(pd.DataFrame([{'consulta':r['id'],'metodo':r['metodo'],'rango':x['rango'],'documento':x['documento_id'],'pagina':x['pagina_pdf'],'fragmento_id':x['fragmento_id']} for x in r['resultados']]))""")
md("En la reserva, ambos métodos alcanzan precisión@5 estricta de 0,30; el MRR es 0,650 para BM25 y 0,625 para vector. La ventaja semántica de desarrollo no se generaliza automáticamente. Ambos retornan vecinos para los controles sin evidencia; no hay abstención calibrada.")
md("## 8. Kibana y reproducción\nEl dashboard ofrece cinco visualizaciones con filtros de periodo y datos reales. Consultas reproducibles: `elastic/Consultas_Kibana.http`. El notebook no vuelve a entrenar al abrirse: los programas de cada etapa y sus instrucciones están en el README.")
code("""display(Image(filename=str(O/'graficos/arquitectura.png')))
display(Markdown('[Abrir dashboard local](http://127.0.0.1:5604/app/dashboards#/view/cp-dashboard)'))
spark.stop()
print('Recorrido y comprobaciones terminados.')""")
n.cells = cells
path=ROOT/'notebooks/Proyecto_Construccion_Poblacion.ipynb'; path.parent.mkdir(exist_ok=True)
nbf.write(n,path)
print('Notebook creado:',len(cells),'celdas')
