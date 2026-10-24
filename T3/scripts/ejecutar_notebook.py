"""Ejecuta el mismo cuaderno que se abre en Jupyter y conserva sus salidas."""
import os
import time
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
archivo = ROOT / "notebooks/Tarea_3.ipynb"
cuaderno = nbformat.read(archivo, as_version=4)
for celda in cuaderno.cells:
    if celda.cell_type == "code":
        celda.outputs = []
        celda.execution_count = None
inicio = time.monotonic()
def informar_avance(cell_index, **kwargs):
    print(f"Celda {cell_index + 1}/{len(cuaderno.cells)} ejecutada", flush=True)

cliente = NotebookClient(cuaderno, timeout=3600, kernel_name="python3",
                         resources={"metadata": {"path": str(ROOT)}},
                         on_cell_executed=informar_avance)
try:
    cliente.execute()
finally:
    nbformat.write(cuaderno, archivo)
print(f"Notebook ejecutado: {archivo}; {time.monotonic() - inicio:.1f} segundos", flush=True)
