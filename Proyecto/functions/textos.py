"""Preparación del corpus y embeddings locales con límite medido en tokens."""
import hashlib
import importlib.metadata
import json
import re
import sqlite3
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
from .entorno import ROOT, guardar_json
from .fragmentacion import detectar_encabezados, limpiar_pagina, fragmentar, n_tokens


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def texto_narrativo(texto):
    """Excluir párrafos numéricos/formulares dudosos, registrando cada exclusión."""
    kept, removed = [], []
    for paragraph in re.split(r"\n\n+", texto):
        letters = sum(c.isalpha() for c in paragraph)
        ratio = sum(c.isdigit() for c in paragraph) / max(1, len(paragraph))
        private = any(unicodedata.category(c) == "Co" for c in paragraph)
        reason = "glifos_de_formula" if private else "tabla_numerica" if ratio > .18 else "rotulo_sin_desarrollo" if letters < 45 else None
        if reason:
            removed.append({"motivo": reason, "texto": paragraph})
        else:
            kept.append(paragraph)
    return "\n\n".join(kept), removed


def procesar():
    from pypdf import PdfReader
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    from sentence_transformers import SentenceTransformer
    import torch
    start = time.perf_counter()
    torch.set_num_threads(2)
    sources = json.loads((ROOT / "config/fuentes.json").read_text())["textos"]
    cfg = json.loads((ROOT / "config/textos.json").read_text())
    model = json.loads((ROOT / "config/modelo.json").read_text())
    snapshot = snapshot_download(model["modelo"], revision=model["revision"], token=False,
                                 cache_dir=str(ROOT / ".cache/huggingface/hub"),
                                 allow_patterns=["*.json", "sentencepiece.bpe.model", "model.safetensors", "README.md"])
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    pages, layouts = [], {}
    for source in sources:
        path = ROOT / source["archivo"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("PDF original modificado")
        reader = PdfReader(path)
        for num, p in enumerate(reader.pages, 1):
            text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", p.extract_text() or "")
            record = {"documento_id": source["id"], "titulo": source["titulo"], "autor": source["autor"],
                      "anio": source["anio"], "idioma": "es", "pagina_pdf": num, "url_fuente": source["ficha"],
                      "url_pdf": source["url"], "pdf_sha256": source["sha256"], "texto": text}
            pages.append(record)
            if source["id"] == "PEN_2021_TERRITORIO" and 76 <= num <= 82:
                layouts[num] = p.extract_text(extraction_mode="layout")
    if len(pages) != 232:
        raise ValueError("Cantidad de páginas del corpus diferente")
    heads = detectar_encabezados(pages)
    chunks, audit = [], []
    for page in pages:
        d, num = page["documento_id"], page["pagina_pdf"]
        rule = cfg["documentos"][d]
        included = any(a <= num <= b for a, b in rule["paginas_cuerpo"])
        is_table = d == "PEN_2021_TERRITORIO" and num in layouts
        clean, removed_headers, joins = limpiar_pagina(page["texto"], heads[d])
        marker = rule.get("cortar_desde", {}).get(str(num))
        if marker:
            clean = clean.split(marker, 1)[0].strip()
        if is_table:
            # Conservar orden de columnas y texto de la página. No se infieren filas
            # relacionales ni se atribuye vigencia actual a la tabla de 2021.
            clean = layouts[num].strip()
            clean = re.sub(r" *\n *\n(?: *\n)+", "\n\n", clean)
            clean = "Anexo 1. Tenencia de planes reguladores y viabilidad ambiental según cantón, 2021. Página PDF " + str(num) + ".\n\n" + clean
            removed = []
        else:
            clean, removed = texto_narrativo(clean)
        accept = (included or is_table) and bool(clean.strip())
        audit.append({"documento_id": d, "pagina_pdf": num, "incluida": accept,
                      "tipo": "tabla_layout" if is_table else "narrativo", "encabezados_retirados": removed_headers,
                      "uniones_guion": joins, "parrafos_excluidos": removed if included else [],
                      "motivo_pagina_excluida": "" if accept else rule["motivo_fuera_cuerpo"]})
        if not accept:
            continue
        # El título/año se conserva en metadatos; no se repite en el vector de cada
        # pasaje narrativo. Tabla conserva su encabezado de contexto documental.
        for i, part in enumerate(fragmentar(clean, tokenizer, 400, 40), 1):
            part.update({k: v for k, v in page.items() if k != "texto"})
            part.update({"tipo": "tabla_layout" if is_table else "narrativo",
                         "fragmento_en_pagina": i, "texto_sha256": sha(part["texto"]),
                         "pagina_limpia_sha256": sha(clean)})
            part["fragmento_id"] = f"{d}_p{num:03d}_{sha(json.dumps([part['char_inicio'],part['char_fin'],part['texto']],ensure_ascii=False))[:16]}"
            chunks.append(part)
    if len(set(c["fragmento_id"] for c in chunks)) != len(chunks):
        raise ValueError("Identificadores de fragmento duplicados")
    out = ROOT / "output"
    (out / "fragmentos.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks))
    guardar_json(out / "revision_corpus.json", audit)
    # Conteo de 400 incluye prefijo y especiales; nada se corta silenciosamente.
    assert max(n_tokens(tokenizer, "passage: " + c["texto"]) for c in chunks) <= 400
    prep_end = time.perf_counter()
    encoder = SentenceTransformer(snapshot, device="cpu", local_files_only=True, trust_remote_code=False,
                                  model_kwargs={"use_safetensors": True})
    encoder.max_seq_length = 512
    versions = {k: importlib.metadata.version(k) for k in ["torch", "transformers", "sentence-transformers", "tokenizers"]}
    vectors, info = codificar_cache([c["texto"] for c in chunks], "passage: ", encoder, tokenizer, model, versions)
    np.savez_compressed(out / "embeddings.npz", fragmento_id=np.array([c["fragmento_id"] for c in chunks]), vectores=vectors)
    queries = json.loads((ROOT / "config/consultas.json").read_text())
    qvectors, qinfo = codificar_cache([q["texto"] for q in queries], "query: ", encoder, tokenizer, model, versions)
    np.savez_compressed(out / "consultas_vectores.npz", consulta_id=np.array([q["id"] for q in queries]), vectores=qvectors)
    report = {"modelo": model, "versiones": versions, "paginas_originales": len(pages),
              "paginas_incluidas": sum(a["incluida"] for a in audit), "fragmentos": len(chunks),
              "por_documento": dict(Counter(c["documento_id"] for c in chunks)),
              "por_tipo": dict(Counter(c["tipo"] for c in chunks)), "tokens_max": max(c["tokens_entrada"] for c in chunks),
              "preparacion_segundos": prep_end - start, "modelo_y_codificacion_segundos": time.perf_counter() - prep_end,
              "cache": info, "cache_consultas": qinfo, "dimensiones": list(vectors.shape),
              "limitacion_tablas": "Las páginas 76-82 conservan maquetación textual por página; no se usan para atribuir un estado regulatorio municipal sin inspeccionar el PDF. Los fragmentos no son filas estructuradas."}
    report["ejecucion_firma"] = sha(json.dumps({"fragmentos": [c["texto_sha256"] for c in chunks],
                                              "modelo": model, "versiones": versions}, sort_keys=True))
    initial = out / "embeddings_inicial.json"
    if not initial.exists() or json.loads(initial.read_text()).get("ejecucion_firma") != report["ejecucion_firma"]:
        guardar_json(initial, report)
    guardar_json(out / "embeddings.json", report)
    print(report, flush=True)


def codificar_cache(textos, prefix, encoder, tokenizer, model, versions):
    import numpy as np
    if any(n_tokens(tokenizer, prefix + t) > 512 for t in textos):
        raise ValueError("Entrada excesiva antes de inferencia")
    keys = [sha(json.dumps([t, prefix, model, versions], ensure_ascii=False, sort_keys=True)) for t in textos]
    existing = {}; dim = model["dimensiones"]
    with sqlite3.connect(ROOT / "output/cache_vectores.sqlite") as db:
        db.execute("CREATE TABLE IF NOT EXISTS vectores (clave TEXT PRIMARY KEY, vector BLOB NOT NULL)")
        for key in set(keys):
            row = db.execute("SELECT vector FROM vectores WHERE clave=?", (key,)).fetchone()
            if row:
                v = np.frombuffer(row[0], dtype="<f4").copy()
                if v.shape != (dim,) or not np.isfinite(v).all() or abs(np.linalg.norm(v) - 1) > 1e-4:
                    raise ValueError("Caché dañada")
                existing[key] = v
        missing = list(dict.fromkeys(k for k in keys if k not in existing)); lookup = dict(zip(keys, textos))
        begin = time.perf_counter()
        # Lotes pequeños: el piloto local no mostró ventaja de grupos grandes.
        for start in range(0, len(missing), 4):
            ks = missing[start:start + 4]
            vv = np.asarray(encoder.encode([prefix + lookup[k] for k in ks], batch_size=4, normalize_embeddings=True, show_progress_bar=False), dtype="<f4")
            if vv.shape != (len(ks), dim) or not np.isfinite(vv).all() or not np.allclose(np.linalg.norm(vv, axis=1), 1, atol=1e-4):
                raise ValueError("Vectores inválidos")
            for k, v in zip(ks, vv):
                db.execute("INSERT INTO vectores VALUES (?,?)", (k, v.tobytes())); existing[k] = v
            db.commit()
        return np.stack([existing[k] for k in keys]), {"entradas": len(textos), "nuevos": len(missing),
                                                       "reutilizados": sum(k not in missing for k in keys), "segundos": time.perf_counter() - begin, "lote": 4}
