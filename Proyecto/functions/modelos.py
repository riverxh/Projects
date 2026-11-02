"""Dos regresores Spark con K-fold por territorio y reservas cronológicas."""
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler, SQLTransformer
from pyspark.ml.regression import LinearRegression, RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import functions as F
from .datos import casos_supervisados, exigir_clave
from .entorno import ROOT, guardar_json

ATRIBUTOS = ["log_area_t", "log_area_t_menos1", "log_obras_t", "log_poblacion_t", "crecimiento_poblacion"]


def evaluar(df):
    if df.filter("prediction IS NULL OR isnan(prediction) OR abs(prediction)>1e100").count():
        raise ValueError("Predicciones inválidas")
    row = df.select((F.col("prediction") - F.col("area_m2")).alias("e")).agg(
        F.count("e").alias("n"), F.avg(F.abs("e")).alias("mae_m2"),
        F.sqrt(F.avg(F.col("e") ** 2)).alias("rmse_m2"), F.avg("e").alias("sesgo_m2")).first()
    return row.asDict()


def entrenar(spark):
    start = time.perf_counter()
    out = ROOT / "output"; (out / "graficos").mkdir(exist_ok=True)
    integrated = spark.read.parquet(str(ROOT / "data/preparados/integrado"))
    ds = casos_supervisados(integrated).cache()
    exigir_clave(ds, ["codigo_agrupacion", "anio_objetivo"])
    train = ds.filter("anio_objetivo <= 2021").withColumn("fold", F.pmod(F.xxhash64("codigo_agrupacion", F.lit(27)), F.lit(3)).cast("int")).cache()
    valid = ds.filter("anio_objetivo = 2022").cache()
    test = ds.filter("anio_objetivo >= 2023").cache()
    counts = {"entrenamiento": train.count(), "validacion_2022": valid.count(), "prueba_2023_2024": test.count()}
    if counts != {"entrenamiento": 405, "validacion_2022": 81, "prueba_2023_2024": 162}:
        raise ValueError(f"Particiones inesperadas: {counts}")
    folds = train.groupBy("fold").agg(F.count("*").alias("filas"), F.countDistinct("codigo_agrupacion").alias("territorios")).orderBy("fold").toPandas()
    if len(folds) != 3 or train.groupBy("codigo_agrupacion").agg(F.countDistinct("fold").alias("n")).filter("n!=1").count():
        raise ValueError("Folds territoriales inconsistentes")
    folds.to_csv(out / "cv_particiones.csv", index=False)
    ds.select("codigo_agrupacion", "agrupacion", "provincia", "anio_objetivo", "anio_datos", "area_m2", "area_t", "area_t_menos1", "poblacion_t", "crecimiento_poblacion", *ATRIBUTOS[:-1]).orderBy("anio_objetivo", "codigo_agrupacion").toPandas().to_csv(out / "casos_supervisados.csv", index=False)
    models = {}
    cvrows = []
    validation = []
    evaluator = RegressionEvaluator(labelCol="area_m2", predictionCol="prediction", metricName="rmse")
    for name in ["lineal", "bosque"]:
        asm = VectorAssembler(inputCols=ATRIBUTOS, outputCol="features_sin_escalar", handleInvalid="error")
        scaler = StandardScaler(inputCol="features_sin_escalar", outputCol="features", withMean=True, withStd=True)
        if name == "lineal":
            reg = LinearRegression(featuresCol="features", labelCol="label_log", predictionCol="prediccion_log", maxIter=100, standardization=False)
            grid = ParamGridBuilder().addGrid(reg.regParam, [0.01, 0.1]).addGrid(reg.elasticNetParam, [0.0, 0.5]).build()
        else:
            reg = RandomForestRegressor(featuresCol="features", labelCol="label_log", predictionCol="prediccion_log", numTrees=40, seed=27, featureSubsetStrategy="sqrt")
            grid = ParamGridBuilder().addGrid(reg.maxDepth, [3, 5]).addGrid(reg.minInstancesPerNode, [4, 8]).build()
        back = SQLTransformer(statement="SELECT *, greatest(CAST(0 AS DOUBLE), expm1(prediccion_log)) AS prediction FROM __THIS__")
        pipeline = Pipeline(stages=[asm, scaler, reg, back])
        cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid, evaluator=evaluator,
                            numFolds=3, foldCol="fold", seed=27, parallelism=1, collectSubModels=False)
        fit = cv.fit(train)
        best_idx = int(np.argmin(fit.avgMetrics)); best_params = grid[best_idx]
        for i, params in enumerate(grid):
            cvrows.append({"modelo": name, "configuracion": i,
                           "parametros": json.dumps({k.name: v for k, v in params.items()}),
                           "rmse_cv_m2": float(fit.avgMetrics[i]), "std_rmse_folds": float(fit.stdMetrics[i]),
                           "seleccionado": i == best_idx})
        # Decisiones registradas antes de evaluar la prueba final.
        validation.append({"modelo": name, "particion": "validacion_2022", **evaluar(fit.bestModel.transform(valid))})
        validation.append({"modelo": name, "particion": "entrenamiento_2017_2021", **evaluar(fit.bestModel.transform(train))})
        models[name] = {"pipeline": pipeline, "params": best_params, "best": fit.bestModel,
                        "parametros": {k.name: v for k, v in best_params.items()}}
        print("CV completada", name, models[name]["parametros"], flush=True)
    pd.DataFrame(cvrows).to_csv(out / "validacion_cruzada.csv", index=False)
    validation.append({"modelo": "persistencia", "particion": "validacion_2022", **evaluar(valid.withColumn("prediction", F.col("area_t")))})
    pd.DataFrame(validation).to_csv(out / "validacion_modelos.csv", index=False)
    choice = min([r for r in validation if r["particion"] == "validacion_2022" and r["modelo"] != "persistencia"], key=lambda x: x["rmse_m2"])["modelo"]
    decision = {"seleccion_familia_solo_2022": choice, "hiperparametros": {k: v["parametros"] for k, v in models.items()},
                "criterio": "RMSE m²; CV por territorios 2017-2021 para hiperparámetros; 2022 para familia; prueba 2023-2024 intacta",
                "refit": "Ambos pipelines se reajustan con objetivos 2017-2022 antes de consultar la prueba final"}
    guardar_json(out / "decisiones_antes_prueba.json", decision)
    develop = ds.filter("anio_objetivo <= 2022").cache(); develop.count()
    predictions = []
    metrics = []
    importances = []
    for name, info in models.items():
        final_model = info["pipeline"].fit(develop, info["params"])
        final_model.write().overwrite().save(str(out / "modelos" / name))
        pred = final_model.transform(test).cache(); pred.count()
        metrics.append({"modelo": name, "particion": "prueba_2023_2024", **evaluar(pred)})
        for year in [2023, 2024]:
            metrics.append({"modelo": name, "particion": str(year), **evaluar(pred.filter(F.col("anio_objetivo") == year))})
        sub = pred.select("codigo_agrupacion", "agrupacion", "provincia", "anio_objetivo", "anio_datos",
                          F.col("area_m2").alias("observado_m2"), F.col("prediction").alias("prediccion_m2"),
                          F.col("area_t").alias("persistencia_m2")).withColumn("modelo", F.lit(name))
        sub = sub.withColumn("error_m2", F.col("prediccion_m2") - F.col("observado_m2")).withColumn("error_absoluto_m2", F.abs("error_m2"))
        predictions.append(sub)
        reg = final_model.stages[2]
        values = reg.coefficients.toArray() if name == "lineal" else reg.featureImportances.toArray()
        importances.extend({"modelo": name, "atributo": k, "valor": float(v), "tipo": "coeficiente_log_escalado" if name == "lineal" else "importancia_impureza"} for k, v in zip(ATRIBUTOS, values))
        pred.unpersist()
    baseline = test.withColumn("prediction", F.col("area_t"))
    metrics.append({"modelo": "persistencia", "particion": "prueba_2023_2024", **evaluar(baseline)})
    for year in [2023, 2024]:
        metrics.append({"modelo": "persistencia", "particion": str(year), **evaluar(baseline.filter(F.col("anio_objetivo") == year))})
    all_predictions = predictions[0].unionByName(predictions[1])
    all_predictions.write.mode("overwrite").parquet(str(ROOT / "data/preparados/predicciones"))
    pdf = all_predictions.orderBy("modelo", "anio_objetivo", "codigo_agrupacion").toPandas()
    pdf.to_csv(out / "predicciones.csv", index=False)
    pd.DataFrame(metrics).to_csv(out / "metricas_modelos.csv", index=False)
    pd.DataFrame(importances).to_csv(out / "atributos_modelos.csv", index=False)
    report = {"filas_supervisadas": ds.count(), "particiones": counts, "folds": folds.to_dict("records"),
              "seleccion": decision, "metricas": metrics, "segundos": time.perf_counter() - start,
              "escala_objetivo_ajuste": "log1p(m²)", "escala_seleccion_y_metricas": "m²",
              "limitacion_cv": "K-fold por territorio mezcla años dentro de 2017-2021; no es validación de pronóstico temporal. La evaluación cronológica es 2022 y la prueba 2023-2024.",
              "limitacion_versiones": "Retrospectiva con versiones revisadas, no reconstruye las publicaciones disponibles en cada fecha"}
    guardar_json(out / "modelos.json", report)
    # Gráficos con unidades originales y la misma reserva para ambos regresores.
    fig, ax = plt.subplots(figsize=(8, 4.2))
    met = pd.DataFrame([m for m in metrics if m["particion"] == "prueba_2023_2024"])
    x = np.arange(len(met)); ax.bar(x - .18, met.mae_m2, .36, label="MAE"); ax.bar(x + .18, met.rmse_m2, .36, label="RMSE")
    ax.set_xticks(x, met.modelo); ax.set_ylabel("m²"); ax.set_title("Errores en la reserva 2023–2024"); ax.legend(); fig.tight_layout(); fig.savefig(out / "graficos/errores_modelos.png", dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, name in zip(axes, ["lineal", "bosque"]):
        p = pdf[pdf.modelo == name]; ax.scatter(p.observado_m2, p.prediccion_m2, alpha=.65, s=16)
        mx = max(p.observado_m2.max(), p.prediccion_m2.max()); ax.plot([0, mx], [0, mx], "--", color="gray")
        ax.set(title=name, xlabel="Observado (m²)", ylabel="Predicción (m²)")
    fig.tight_layout(); fig.savefig(out / "graficos/observado_predicho.png", dpi=160); plt.close(fig)
    annual = integrated.groupBy("anio").agg(F.sum("area_m2").alias("area_m2"), F.sum("obras_total").alias("obras"), F.sum("poblacion").alias("poblacion")).orderBy("anio").toPandas()
    annual.to_csv(out / "resumen_anual.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4)); ax.plot(annual.anio, annual.area_m2 / 1e6, marker="o"); ax.set(xlabel="Año", ylabel="Millones de m²", title="Área autorizada nacional, 2015–2024"); fig.tight_layout(); fig.savefig(out / "graficos/evolucion_area.png", dpi=160); plt.close(fig)
    return report
