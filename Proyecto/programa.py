"""Entradas reproducibles del proyecto. Cada etapa deja evidencia en output/."""
import argparse
from functions.entorno import iniciar_spark


def main():
    p = argparse.ArgumentParser()
    p.add_argument("etapa", choices=["preparar", "entrenar", "embeddings", "cargar", "buscar", "dashboard", "verificar", "todo"])
    args = p.parse_args()
    stages = ["preparar", "entrenar", "embeddings", "cargar", "buscar", "dashboard", "verificar"] if args.etapa == "todo" else [args.etapa]
    for stage in stages:
        print("ETAPA", stage, flush=True)
        if stage in ["preparar", "entrenar"]:
            spark = iniciar_spark(); spark.sparkContext.setLogLevel("ERROR")
            try:
                if stage == "preparar":
                    from functions.datos import preparar
                    print(preparar(spark), flush=True)
                else:
                    from functions.modelos import entrenar
                    print(entrenar(spark), flush=True)
            finally:
                spark.stop()
        elif stage == "embeddings":
            from functions.textos import procesar
            procesar()
        elif stage == "cargar":
            from functions.materializacion import cargar
            cargar()
        elif stage == "buscar":
            from functions.busquedas import ejecutar
            ejecutar()
        elif stage == "dashboard":
            from functions.dashboard import crear
            crear()
        elif stage == "verificar":
            from functions.materializacion import verificar
            verificar()


if __name__ == "__main__":
    main()
