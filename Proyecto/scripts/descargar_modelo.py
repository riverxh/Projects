from pathlib import Path
import json
import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / "config/modelo.json").read_text())
snapshot_download(m["modelo"], revision=m["revision"], token=False, max_workers=2,
                  cache_dir=str(ROOT / ".cache/huggingface/hub"),
                  allow_patterns=["*.json", "sentencepiece.bpe.model", "model.safetensors", "README.md"])
print("Modelo público disponible en caché local:", m["modelo"], m["revision"])
