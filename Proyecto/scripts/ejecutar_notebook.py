from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'notebooks/Proyecto_Construccion_Poblacion.ipynb'
nb = nbformat.read(path, as_version=4)
NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
nbformat.write(nb, path)
print('Notebook ejecutado y guardado:', path)
