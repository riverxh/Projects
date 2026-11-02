"""Fragmentación por tokens validada en la prueba piloto local."""
import re
import unicodedata
from collections import Counter, defaultdict

def normalizar_linea(linea: str) -> str:
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", linea).strip())

def detectar_encabezados(paginas):
    """Solo líneas repetidas en el margen superior; no elimina frases del cuerpo."""
    por_doc = defaultdict(Counter)
    n = Counter(p["documento_id"] for p in paginas)
    for p in paginas:
        lines = [s.strip() for s in p["texto"].splitlines() if s.strip()]
        por_doc[p["documento_id"]].update(set(normalizar_linea(x) for x in lines[:3]))
    return {d: {s for s, k in c.items() if k >= max(4, n[d] // 2)} for d, c in por_doc.items()}

def limpiar_pagina(texto: str, encabezados: set[str]):
    texto = unicodedata.normalize("NFC", texto).replace("\u00ad", "").replace("\uf0b7", "•")
    lines = texto.splitlines()
    eliminadas = []
    nonempty = [i for i, s in enumerate(lines) if s.strip()]
    for i in nonempty[:3]:
        if normalizar_linea(lines[i]) in encabezados:
            eliminadas.append(lines[i].strip())
            lines[i] = ""
    texto = "\n".join(lines)
    # Solo se une guion al final de línea entre letras; conservar copia cruda y registrar cantidad.
    texto, uniones = re.subn(r"([^\W\d_])-\s*\n\s*([^\W\d_])", r"\1\2", texto)
    texto = texto.replace("\u00a0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    # Los saltos simples son maquetación del PDF; los dobles conservan párrafos.
    texto = re.sub(r"(?<!\n)\n(?!\n)", " ", texto)
    return texto, eliminadas, uniones

def n_tokens(tokenizer, texto: str) -> int:
    return len(tokenizer(texto, add_special_tokens=True, truncation=False, verbose=False)["input_ids"])

def fragmentar(texto: str, tokenizer, max_tokens: int = 400, overlap: int = 40):
    """Ventanas de caracteres con offsets reales del tokenizador y límite comprobado.

    Prioriza final de párrafo/oración en la segunda mitad de la ventana. No cruza
    páginas. La cobertura se verifica sobre todo carácter no blanco del texto limpio.
    """
    if not texto.strip():
        return []
    overhead = n_tokens(tokenizer, "passage: ")
    if max_tokens <= overhead + 8 or overlap < 0 or overlap >= (max_tokens - overhead) // 2:
        raise ValueError("Tamaño de fragmento o solapamiento inválido")
    spans = []
    start = 0
    while start < len(texto):
        tail = texto[start:]
        encoded = tokenizer(tail, add_special_tokens=False, return_offsets_mapping=True, truncation=False, verbose=False)
        offsets = encoded["offset_mapping"]
        if not offsets:
            break
        take = min(len(offsets), max_tokens - overhead - 2)
        end = len(tail) if take == len(offsets) else offsets[take - 1][1]
        if take < len(offsets):
            floor = offsets[max(0, take // 2)][0]
            paragraph_ends = [m.end() for m in re.finditer(r"\n\n", tail[:end]) if m.end() >= floor]
            sentence_ends = [m.end() for m in re.finditer(r"(?<=[.!?;])\s+", tail[:end]) if m.end() >= floor]
            if paragraph_ends or sentence_ends:
                end = (paragraph_ends or sentence_ends)[-1]
        # El recuento definitivo incluye prefijo y tokens especiales. Nunca truncar.
        while end > 0 and n_tokens(tokenizer, "passage: " + tail[:end].strip()) > max_tokens:
            end -= 1
        if end <= 0:
            raise ValueError("No se puede avanzar al fragmentar")
        raw = tail[:end]
        left = len(raw) - len(raw.lstrip())
        right = len(raw.rstrip())
        if right > left:
            fragmento = raw[left:right]
            spans.append({"char_inicio": start + left, "char_fin": start + right,
                          "texto": fragmento, "tokens_entrada": n_tokens(tokenizer, "passage: " + fragmento)})
        if end == len(tail):
            break
        current_offsets = tokenizer(raw, add_special_tokens=False, return_offsets_mapping=True, truncation=False, verbose=False)["offset_mapping"]
        back = current_offsets[-overlap][0] if overlap and len(current_offsets) > overlap else end
        # No cortar palabras: ampliar el solapamiento hasta su inicio.
        while back > 0 and not tail[back - 1].isspace():
            back -= 1
        next_start = start + (back if back > 0 else end)
        if next_start <= start:
            raise ValueError("Fragmentación sin progreso")
        start = next_start
    cubierto = bytearray(len(texto))
    for f in spans:
        cubierto[f["char_inicio"]:f["char_fin"]] = b"\1" * (f["char_fin"] - f["char_inicio"])
    if any(not c.isspace() and not cubierto[i] for i, c in enumerate(texto)):
        raise AssertionError("La fragmentación perdió contenido")
    return spans
