"""Tablas, gráficos y análisis apoyados en las ejecuciones registradas."""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
G = OUT / "graficos"; G.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def main():
    models = json.loads((OUT / "modelos.json").read_text())
    emb = json.loads((OUT / "embeddings_inicial.json").read_text())
    eval_search = json.loads((OUT / "evaluacion_busqueda.json").read_text())
    m = pd.read_csv(OUT / "metricas_modelos.csv")
    p = pd.read_csv(OUT / "predicciones.csv", dtype={"codigo_agrupacion": str})
    territories = p.groupby(["modelo", "codigo_agrupacion", "agrupacion", "provincia"]).agg(n=("error_m2", "size"), mae_m2=("error_absoluto_m2", "mean"), sesgo_m2=("error_m2", "mean")).reset_index()
    territories.sort_values(["modelo", "mae_m2"], ascending=[True, False]).to_csv(OUT / "errores_territorio.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, name in zip(axes, ["lineal", "bosque"]):
        sub = territories[territories.modelo == name].nlargest(7, "mae_m2").sort_values("mae_m2")
        ax.barh(sub.agrupacion, sub.mae_m2, color="#176d8a"); ax.set(title=name, xlabel="MAE en 2023–2024 (m²)")
    fig.tight_layout(); fig.savefig(G / "errores_territorio.png", dpi=160); plt.close(fig)
    search = pd.read_csv(OUT / "resumen_busqueda.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    groups = ["desarrollo", "reserva"]; x = np.arange(2)
    for j, metric in enumerate(["precision_5_estricta", "reciproco_primer_relevante"]):
        for i, method in enumerate(["texto", "vector"]):
            vals = [float(search[(search.grupo == group) & (search.metodo == method)][metric].iloc[0]) for group in groups]
            axes[j].bar(x + (i - .5) * .34, vals, .34, label="BM25" if method == "texto" else "Vector", color=["#176d8a", "#d78736"][i])
        axes[j].set_xticks(x, ["Desarrollo (4)", "Reserva (8)"]); axes[j].set_ylim(0, 1.08)
        axes[j].set_title("Precisión@5 estricta" if j == 0 else "Recíproco del primer relevante"); axes[j].legend()
    fig.tight_layout(); fig.savefig(G / "comparacion_busquedas.png", dpi=160); plt.close(fig)
    attrs = pd.read_csv(OUT / "atributos_modelos.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, name in zip(axes, ["lineal", "bosque"]):
        sub = attrs[attrs.modelo == name].sort_values("valor")
        ax.barh(sub.atributo, sub.valor, color="#176d8a")
        ax.set_title("Coeficientes sobre variables escaladas" if name == "lineal" else "Importancias del bosque")
        ax.set_xlabel("Coeficiente (objetivo log)" if name == "lineal" else "Reducción de impureza relativa")
    fig.tight_layout(); fig.savefig(G / "atributos_modelos.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(11, 2.5)); ax.set_xlim(2016.5, 2024.5); ax.set_ylim(0, 1); ax.axis("off")
    for a, b, color, title in [(2016.6, 2021.4, "#176d8a", "2017–2021 · 405 casos\nK-fold por territorio"),
                                (2021.6, 2022.4, "#d78736", "2022\n81 casos"), (2022.6, 2024.4, "#577e60", "2023–2024 · 162 casos\nPrueba reservada")]:
        ax.add_patch(FancyBboxPatch((a, .25), b-a, .48, boxstyle="round,pad=0.015", facecolor=color, edgecolor="none"))
        ax.text((a+b)/2, .49, title, ha="center", va="center", color="white", fontsize=12)
    ax.text(2020.5, .03, "Reajuste final con 2017–2022. Predictores siempre anteriores al año objetivo.", ha="center", fontsize=11)
    fig.tight_layout(); fig.savefig(G / "evaluacion_temporal.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(11, 5)); ax.set_xlim(0, 11); ax.set_ylim(0, 5); ax.axis("off")
    boxes = [(0.1,3.4,2.0,1.0,"INEC\nConstrucción + población"), (2.8,3.4,2.1,1.0,"Spark\nETL y cruce territorial"),
             (5.6,3.4,2.0,1.0,"PostgreSQL\nFuentes e integrado"), (8.3,3.4,2.4,1.0,"Spark ML\nDos regresores y prueba"),
             (.1,.8,2.0,1.0,"PEN / CONARE\nCuatro PDF"), (2.8,.8,2.1,1.0,"Texto + E5\nFragmentos y caché"),
             (5.6,.8,2.0,1.0,"Elasticsearch\nTexto y vectores"), (8.3,.8,2.4,1.0,"Kibana\nConsultas y 5 gráficos")]
    for x0,y,w,h,label in boxes:
        ax.add_patch(FancyBboxPatch((x0,y),w,h,boxstyle="round,pad=.05",facecolor="#edf4f6",edgecolor="#176d8a",linewidth=1.5)); ax.text(x0+w/2,y+h/2,label,ha="center",va="center",fontsize=11)
    for y in [1.3,3.9]:
        for a,b in [(2.15,2.7),(4.95,5.5),(7.65,8.2)]:ax.annotate("",xy=(b,y),xytext=(a,y),arrowprops={"arrowstyle":"->","color":"#176d8a","lw":1.7})
    ax.annotate("",xy=(9.4,1.9),xytext=(9.4,3.3),arrowprops={"arrowstyle":"->","color":"#d78736","lw":1.7})
    ax.text(9.5,2.6,"Datos y errores\na índices numéricos",ha="left",va="center",fontsize=9)
    fig.tight_layout(); fig.savefig(G / "arquitectura.png", dpi=180); plt.close(fig)

    final = {r["modelo"]: r for r in models["metricas"] if r["particion"] == "prueba_2023_2024"}
    gain_mae = 100 * (1 - final["lineal"]["mae_m2"] / final["persistencia"]["mae_m2"])
    gain_rmse = 100 * (1 - final["lineal"]["rmse_m2"] / final["persistencia"]["rmse_m2"])
    rows = "\n".join(f"| {name} | {final[name]['mae_m2']:,.2f} | {final[name]['rmse_m2']:,.2f} | {final[name]['sesgo_m2']:,.2f} |" for name in ["lineal", "bosque", "persistencia"])
    report = f'''# Análisis de resultados

## Datos y objetivo

Se reconstruyeron 818 totales cantonales anuales de construcción y 840 registros de población de la hoja C4, para 2015–2024. Las tres segregaciones se agregaron a sus territorios de origen, produciendo 81 agrupaciones por año y 810 registros integrados. La suma del área coincide con el total nacional de cada Excel y con los subtotales de categoría de destino; estos últimos se analizan sin sumar también sus filas de detalle. Las ausencias y signos no se imputaron como cero.

El objetivo es el área autorizada del año siguiente, en m², para obras nuevas y ampliaciones. Obras autorizadas no equivalen a obras terminadas, cantidad de viviendas ni necesidad habitacional. El valor nominal en miles de colones se conserva, pero no se usa como objetivo ni predictor del modelo.

## Evaluación predictiva

Los 648 casos supervisados usan área de los dos años anteriores, obras y población del anterior, y crecimiento poblacional. Los niveles se transforman con log1p; el crecimiento conserva su escala. El objetivo de ajuste también usa log1p(m²), y la predicción vuelve a m² con expm1 y piso cero definido antes de evaluar. El escalador se ajusta dentro de cada fold.

Se comparan regresión lineal regularizada y bosque de 40 árboles. Para cada uno se probaron cuatro configuraciones con CrossValidator de tres folds: 24 ajustes de validación, dos reajustes de los ganadores y dos reajustes finales. Los folds agrupan territorios completos; tienen 31, 32 y 18 territorios. Mezclan años de 2017–2021 y **no constituyen validación temporal**. Se evalúan como diagnóstico de transferencia entre territorios del periodo de desarrollo.

La validación cronológica es 2022 (81 casos); la prueba reservada es 2023–2024 (162 casos). Los hiperparámetros se eligen con CV, y la familia entre los dos modelos requeridos se compara en 2022, antes de consultar la prueba. Ambos se reajustan con objetivos 2017–2022. En 2024 se usan atributos observados hasta 2023, pero no se incorpora el objetivo 2023 al reajuste del modelo. Es una evaluación retrospectiva de un paso con versiones revisadas, no una reconstrucción exacta de la información publicada en cada fecha.

Los mejores parámetros fueron regParam=0.01, elasticNetParam=0 para la lineal y maxDepth=5, minInstancesPerNode=4 para el bosque. En validación 2022, la lineal obtuvo RMSE 37 627,28 m² frente a 38 911,73 del bosque; **persistencia fue mejor que ambos, con 34 378,25 m²**. Por ello, la selección entre regresores no prueba que un modelo aprendido sea siempre preferible a la referencia simple.

## Prueba final 2023–2024

| Método | MAE (m²) | RMSE (m²) | Sesgo medio (m²) |
|---|---:|---:|---:|
{rows}

En la prueba final, la lineal reduce MAE en {gain_mae:.2f}% y RMSE en {gain_rmse:.2f}% frente a persistencia. El bosque tiene mayor error que ambos. Esto corresponde exclusivamente a estas 162 observaciones y a la decisión previa de parámetros; no demuestra superioridad universal ni causalidad de la población sobre construcción.

La ventaja cambia por año: en 2023 persistencia tiene menor MAE que la lineal (13 127,54 frente a 13 987,32 m²), aunque la lineal logra menor RMSE. En 2024 la lineal mejora ambas métricas respecto a persistencia. El análisis por territorio se guarda en `output/errores_territorio.csv`; los errores de grandes territorios influyen especialmente sobre RMSE.

## Diferencias entre modelos

El historial reciente domina: las importancias de las dos áreas previas suman aproximadamente 0,844 en el bosque. En la lineal, los coeficientes positivos más grandes también corresponden al área reciente y previa, sobre variables escaladas. Los coeficientes y las importancias de impureza tienen interpretaciones distintas y no son efectos causales.

La lineal regularizada ofrece un ajuste suave en un conjunto pequeño; el bosque crea regiones y promedia hojas, con capacidad limitada de extrapolar extremos. El bosque tiene menor error de entrenamiento y mayor error cronológico que la lineal, compatible con un ajuste más específico del periodo de desarrollo. Ambos muestran sesgo negativo en la prueba. Una explicación posible es el ajuste sobre logaritmos y posterior exponenciación sin corrección de sesgo, que no estima necesariamente la media del área original; también intervienen cambios temporales y territorios con valores extremos. Estas son explicaciones compatibles con la evidencia, no un experimento causal. No se corrigió el modelo después de observar la prueba.

## Corpus y feedback

Se procesaron 232 páginas originales. Tras separar portadas, referencias, anexos ajenos al alcance narrativo y párrafos dudosos, se conservaron {emb['paginas_incluidas']} páginas con {emb['fragmentos']} fragmentos: {emb['por_tipo']['narrativo']} narrativos y {emb['por_tipo']['tabla_layout']} de tablas con maquetación de las páginas PDF 76–82 del informe de 2021. Las exclusiones y sus textos se registran en `output/revision_corpus.json`.

El tokenizador de E5 comprobó un máximo de {emb['tokens_max']} tokens por entrada, incluidos prefijo y especiales, por debajo del límite configurado 400 y del límite del modelo 512. Cada vector tiene 384 componentes, se normaliza y conserva referencia de documento, año, página y fuente. Se guardan lotes y caché para reanudar. La pasada inicial de los {emb['fragmentos']} pasajes tardó {emb['cache']['segundos']:.2f} segundos en el contenedor; el tiempo del piloto macOS no se traslada como garantía a Docker. El tiempo de consultas se registra por separado.

Las tablas se recuperan como texto con maquetación y página, no como filas relacionales validadas ni como una base de vigencia jurídica. Una fila municipal requiere inspeccionar el PDF. El corpus textual usa investigaciones PEN, con datos de CFIA y otras fuentes, mientras la serie predictiva es INEC: sus coberturas no son equivalentes y no se mezclan sus cifras.

## Búsqueda textual y vectorial

El índice textual usa BM25 con analizador español. El vectorial usa E5 con prefijos passage/query y kNN coseno. Se emplean exactamente los mismos {emb['fragmentos']} fragmentos y filtros. Se ejecutaron 14 consultas: cuatro de desarrollo, ocho reservadas y dos controles sin respuesta. Se anotaron {eval_search['juicios']} pares del pool top5, sin método ni score durante la lectura; cada grado y justificación está disponible. Es una evaluación interna sin segundo anotador independiente.

| Grupo | BM25 precisión@5 | Vector precisión@5 | BM25 MRR | Vector MRR |
|---|---:|---:|---:|---:|
| Desarrollo, 4 consultas | 0,35 | 0,60 | 0,625 | 1,000 |
| Reserva, 8 consultas | 0,30 | 0,30 | 0,650 | 0,625 |
| Controles, 2 consultas | 0,00 | 0,00 | 0,000 | 0,000 |

Las métricas estrictas requieren grado 2: una respuesta directa. Los vectores mejoran el grupo de desarrollo, pero **no superan BM25 en las ocho consultas reservadas**: empatan en precisión@5 y BM25 tiene MRR ligeramente mayor. La muestra es pequeña y la diferencia de MRR no demuestra significancia estadística. Con estos resultados no se justifica reemplazar toda búsqueda textual por vectorial.

Q01 es un acierto vectorial: el primer resultado responde sobre restricciones urbanas, mientras BM25 encuentra su primer resultado directamente relevante en cuarto lugar. En Q03 ambos métodos recuperan primero la evidencia de Pococí; también aparecen fragmentos de Ciudad Quesada que se califican como no pertinentes al territorio pedido. Q07 es una limitación de ambos: ninguno de sus cinco primeros resultados explica completamente la relación entre congestión y viajes hacia San José. En Q11 BM25 ubica la renovación urbana primero y el vectorial en cuarto lugar. Los controles sobre Marte y permisos de 2035 devuelven vecinos sin respuesta; el sistema no tiene abstención calibrada.

Las latencias son observaciones de una pasada, con calentamiento y red local variables; no constituyen un benchmark concluyente de rendimiento. Las métricas evalúan fragmentos y pueden incluir solapamientos de una misma página. No hay etiquetas exhaustivas de todo el corpus, por lo que no se informa recall global.

## Bases y dashboard

PostgreSQL conserva ocho tablas con claves, relaciones y atributos escalares; Elasticsearch conserva fuentes tabulares, integrado, predicciones y los dos índices de texto. La relectura SQL compara todas las columnas con los DataFrames y las métricas se recalculan con SQL. Los identificadores y textos de los dos índices coinciden. La carga reemplaza solo el esquema `proyecto` y los índices `cp-*`, conservando los originales.

El dashboard contiene cinco visualizaciones conectadas a los índices reales: área anual, obras por provincia, área anual por habitante ponderada, categorías de destino y MAE de los modelos. La razón de área por habitante es suma de área entre suma de población en el periodo; no suma ratios ni población como si fuera un flujo. Los datos son anuales; el campo fecha es el inicio del año de referencia en hora de Costa Rica para filtrar, no la fecha de cada permiso.

## Limitaciones y uso

810 agregados históricos son útiles para este ejercicio, pero no constituyen microdatos ni una muestra suficiente para evaluar decisiones individuales. Las agrupaciones cubren tres segregaciones identificadas y no certifican ausencia de otros cambios de límites. Las versiones revisadas, cambios operativos alrededor de 2020, el periodo corto y la heterogeneidad territorial limitan generalización. Las publicaciones textuales son históricas. El sistema permite explorar y comparar resultados con trazabilidad; no estima causalidad ni acredita vigencia normativa.
'''
    (ROOT / "doc/Analisis_resultados.md").write_text(report)
    print("Análisis y gráficos generados con resultados reales")


if __name__ == "__main__":
    main()
