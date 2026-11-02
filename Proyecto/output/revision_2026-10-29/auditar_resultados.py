"""Auditoría independiente de los archivos, casos, modelos guardados y bases locales."""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,hashlib,math,sqlite3,re
import numpy as np
import openpyxl
from pyspark.ml import PipelineModel
from functions.entorno import iniciar_spark
from functions.materializacion import es_request,conectar_pg,pares_dataframe,INDEX
from functions.datos import METRICAS
R=Path('/src');O=R/'output';A=R/'tmp/revision_2026-10-29';A.mkdir(parents=True,exist_ok=True)
report={}
def csvrows(name):return list(csv.DictReader((O/name).open()))
def readj(name):return json.loads((O/name).read_text())
def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-6)
def save(): (A/'Auditoria_resultados.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
manifest=json.loads((R/'config/fuentes.json').read_text());all_sources=manifest['construccion']+[manifest['poblacion']]+manifest['textos']
assert all(hashlib.sha256((R/x['archivo']).read_bytes()).hexdigest()==x['sha256'] for x in all_sources);report['originales_hash_validado']=len(all_sources)
con=[json.loads(s) for s in (R/'data/preparados/construccion_extraida.jsonl').read_text().splitlines()];det=[json.loads(s) for s in (R/'data/preparados/destinos_extraidos.jsonl').read_text().splitlines()];pop=[json.loads(s) for s in (R/'data/preparados/poblacion_extraida.jsonl').read_text().splitlines()]
checked=0
for source in manifest['construccion']:
 wb=openpyxl.load_workbook(R/source['archivo'],read_only=True,data_only=True);ws=wb.worksheets[0];rows=list(ws.values)
 for row in [r for r in con+det if r['anio']==source['anio']]:
  for key,col in json.loads(row['columnas_metricas']).items():
   value=rows[row['fila']-1][openpyxl.utils.column_index_from_string(col)-1];expected=None if value is None else str(value).strip();assert row[key]==expected,(source['anio'],row['fila'],key)
   checked+=1
 wb.close()
wb=openpyxl.load_workbook(R/manifest['poblacion']['archivo'],read_only=True,data_only=True);rows=list(wb['C4'].values)
for row in pop:
 for label,key in [('total','poblacion'),('hombres','hombres'),('mujeres','mujeres')]:
  col,n=openpyxl.utils.cell.coordinate_from_string(row['celda_'+label]);assert str(rows[n-1][openpyxl.utils.column_index_from_string(col)-1])==row[key];checked+=1
wb.close();report['celdas_releidas_y_comparadas']=checked
# Reconstruir agregados numéricos sin llamar al join del programa.
renames={'216':'203','612':'601','613':'607'};cc=defaultdict(lambda:defaultdict(list));pp=defaultdict(lambda:defaultdict(list))
for row in con:
 for k in METRICAS:
  if row[k] not in [None,'','-','.','N.D']:cc[(renames.get(row['codigo_canton'],row['codigo_canton']),str(row['anio']))][k].append(float(row[k]))
for row in pop:
 for k in ['poblacion','hombres','mujeres']:pp[(renames.get(row['codigo_canton'],row['codigo_canton']),str(row['anio']))][k].append(float(row[k]))
integrated=csvrows('integrado.csv');lookup={(r['codigo_agrupacion'],r['anio']):r for r in integrated};assert len(lookup)==810 and set(lookup)==set(cc)==set(pp)
for key,row in lookup.items():
 for k in METRICAS+['poblacion','hombres','mujeres']:
  values=cc[key][k] if k in METRICAS else pp[key][k]
  if values:assert close(sum(values),row[k]),(key,k)
  else:assert row[k] in ['',None]
 assert close(float(row['area_m2'])/float(row['poblacion']),row['area_por_habitante'])
assert Counter(r['anio'] for r in integrated)=={str(y):81 for y in range(2015,2025)};report['integrados_reconstruidos_independientemente']=810
cases=csvrows('casos_supervisados.csv');assert len(cases)==648
for row in cases:
 c=row['codigo_agrupacion'];y=int(row['anio_objetivo']);assert int(row['anio_datos'])==y-1;p=lookup[(c,str(y-1))];q=lookup[(c,str(y-2))]
 assert close(row['area_m2'],lookup[(c,str(y))]['area_m2']) and close(row['area_t'],p['area_m2']) and close(row['area_t_menos1'],q['area_m2'])
 assert close(row['poblacion_t'],p['poblacion'])
 assert close(row['crecimiento_poblacion'],float(p['poblacion'])/float(q['poblacion'])-1)
 for logkey,key,raw in [('log_area_t','area_m2',p),('log_area_t_menos1','area_m2',q),('log_obras_t','obras_total',p),('log_poblacion_t','poblacion',p)]:assert close(row[logkey],math.log1p(float(raw[key])))
report['casos_rezagados_sin_datos_contemporaneos']=648
pred=csvrows('predicciones.csv');assert len(pred)==324;met=readj('modelos.json')['metricas']
for name in ['lineal','bosque']:
 sub=[r for r in pred if r['modelo']==name];assert len(sub)==162
 for r in sub:assert int(r['anio_datos'])+1==int(r['anio_objetivo']) and close(r['observado_m2'],lookup[(r['codigo_agrupacion'],r['anio_objetivo'])]['area_m2'])
 errors=np.array([float(r['prediccion_m2'])-float(r['observado_m2']) for r in sub]);ref=next(m for m in met if m['modelo']==name and m['particion']=='prueba_2023_2024');assert close(np.abs(errors).mean(),ref['mae_m2']) and close(np.sqrt((errors**2).mean()),ref['rmse_m2']) and close(errors.mean(),ref['sesgo_m2'])
report['metricas_recalculadas_numpy']=True
queries=json.loads((R/'config/consultas.json').read_text());labels=json.loads((R/'config/relevancia.json').read_text());lab={(x['consulta_id'],x['fragmento_id']):x for x in labels};assert len(lab)==len(labels)==110 and all(type(x['grado'])==int and 0<=x['grado']<=2 and x.get('justificacion','').strip() for x in labels)
results=readj('resultados_busqueda.json');assert len(results)==28;pool={(r['id'],h['fragmento_id']) for r in results for h in r['resultados']};assert pool==set(lab)
report['consultas_y_juicios']={'consultas':len(queries),'busquedas':len(results),'pares_unicos':len(pool),'sin_juicios_nuevos':True}
frags=[json.loads(s) for s in (O/'fragmentos.jsonl').read_text().splitlines()];vec=np.load(O/'embeddings.npz',allow_pickle=False);qvec=np.load(O/'consultas_vectores.npz',allow_pickle=False)
assert vec['vectores'].shape==(298,384) and qvec['vectores'].shape==(14,384);assert list(vec['fragmento_id'])==[c['fragmento_id'] for c in frags]
assert np.isfinite(vec['vectores']).all() and np.isfinite(qvec['vectores']).all() and np.allclose(np.linalg.norm(vec['vectores'],axis=1),1,atol=1e-4)
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
model=json.loads((R/'config/modelo.json').read_text());snap=snapshot_download(model['modelo'],revision=model['revision'],cache_dir=str(R/'.cache/huggingface/hub'),local_files_only=True);tok=AutoTokenizer.from_pretrained(snap,local_files_only=True,trust_remote_code=False)
lens=[len(tok('passage: '+c['texto'],add_special_tokens=True,truncation=False)['input_ids']) for c in frags];assert max(lens)==397 and all(n==c['tokens_entrada'] and n<=400 for n,c in zip(lens,frags));assert all(len(tok('query: '+q['texto'],truncation=False)['input_ids'])<=512 for q in queries)
report['vectores_y_tokens']={'pasajes':298,'consultas':14,'dimensiones':384,'max_tokens':max(lens),'vectores_finitos_normalizados':True}
# Cache y archivo NPZ deben contener exactamente el mismo vector para cada clave.
versions=readj('embeddings.json')['versiones'];cachechecked=0
with sqlite3.connect(O/'cache_vectores.sqlite') as db:
 for texts,prefix,arr in [([c['texto'] for c in frags],'passage: ',vec['vectores']),([q['texto'] for q in queries],'query: ',qvec['vectores'])]:
  for t,v in zip(texts,arr):
   key=hashlib.sha256(json.dumps([t,prefix,model,versions],ensure_ascii=False,sort_keys=True).encode()).hexdigest();row=db.execute('SELECT vector FROM vectores WHERE clave=?',(key,)).fetchone();assert row is not None and np.array_equal(np.frombuffer(row[0],dtype='<f4'),v);cachechecked+=1
report['cache_comparada_vector_por_vector']=cachechecked;save()
# Comprobar modelos finales guardados y contenido completo de cinco índices tabulares.
spark=iniciar_spark();spark.sparkContext.setLogLevel('ERROR')
try:
 feats=['log_area_t','log_area_t_menos1','log_obras_t','log_poblacion_t','crecimiento_poblacion'];train=np.array([[float(r[f]) for f in feats] for r in cases if int(r['anio_objetivo'])<=2022]);test=[r for r in cases if int(r['anio_objetivo'])>=2023];X=np.array([[float(r[f]) for f in feats] for r in test]);saved={}
 for name in ['lineal','bosque']:
  m=PipelineModel.load(str(O/'modelos'/name));assert m.stages[0].getInputCols()==feats;sc=m.stages[1];np.testing.assert_allclose(sc.mean.toArray(),train.mean(0),rtol=1e-10,atol=1e-10);np.testing.assert_allclose(sc.std.toArray(),train.std(0,ddof=1),rtol=1e-10,atol=1e-10)
  if name=='lineal':
   reg=m.stages[2];assert reg.getRegParam()==.01 and reg.getElasticNetParam()==0;raw=np.maximum(0,np.expm1(((X-sc.mean.toArray())/sc.std.toArray())@reg.coefficients.toArray()+reg.intercept));predlookup={(r['codigo_agrupacion'],r['anio_objetivo']):float(r['prediccion_m2']) for r in pred if r['modelo']==name};np.testing.assert_allclose(raw,[predlookup[(r['codigo_agrupacion'],r['anio_objetivo'])] for r in test],rtol=1e-10,atol=1e-6)
  else:assert m.stages[2].getNumTrees==40 and m.stages[2].getMaxDepth()==5 and m.stages[2].getMinInstancesPerNode()==4
  saved[name]={'atributos_correctos':True,'escalador_solo_486_casos_2017_2022':True}
 report['modelos_finales_inspeccionados']=saved;checked_indices={}
 for table,index in INDEX.items():
  response=es_request('POST',index+'/_search?scroll=1m',json={'size':1000,'sort':['_doc'],'query':{'match_all':{}}});hits=response['hits']['hits'];sid=response.get('_scroll_id')
  while response['hits']['hits']:
   response=es_request('POST','_search/scroll',json={'scroll':'1m','scroll_id':sid});sid=response.get('_scroll_id',sid);hits.extend(response['hits']['hits'])
  if sid:es_request('DELETE','_search/scroll',json={'scroll_id':[sid]})
  actual={h['_id']:h['_source'] for h in hits};df=spark.read.parquet(str(R/'data/preparados'/table));expected=dict(pares_dataframe(df,table));assert actual==expected,(table,len(actual),len(expected));checked_indices[index]=len(actual)
 report['contenido_completo_indices_tabulares']=checked_indices
 with conectar_pg() as db:
  with db.cursor() as cur:
   cur.execute("SELECT contype,count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='proyecto' GROUP BY contype");cons=dict(cur.fetchall());assert cons.get('p')==8 and cons.get('f')==4 and cons.get('c')==2;report['restricciones_sql']=cons
   cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'stage_%'");assert cur.fetchone()[0]==0
   cur.execute("SELECT sum(area_m2) FROM proyecto.destinos_cantonales WHERE provincia='Heredia' AND anio=2024 AND nivel='subtotal_categoria'");sqlarea=cur.fetchone()[0]
 expected_area=sum(float(r['area_m2']) for r in integrated if r['provincia']=='Heredia' and r['anio']=='2024');res=es_request('POST','cp-destinos/_search',json={'size':0,'query':{'bool':{'filter':[{'term':{'provincia':'Heredia'}},{'term':{'anio':2024}},{'term':{'nivel':'subtotal_categoria'}}]}},'aggs':{'area':{'sum':{'field':'area_m2'}}}});assert close(sqlarea,expected_area) and close(res['aggregations']['area']['value'],expected_area);report['filtro_destinos_Heredia_2024']={'area_m2':expected_area,'sql_y_elasticsearch_coinciden':True,'resultados':res['hits']['total']['value']}
finally:spark.stop()
save();print(json.dumps(report,ensure_ascii=False,indent=2))
