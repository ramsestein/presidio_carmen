#!/usr/bin/env python3
"""
Convierte el corpus MEDDOCAN (formato BRAT: .txt + .ann) al mismo formato
que el dataset Carmen usado en este repositorio.

Formato Carmen (carmen/raw_data.json):
    {
      "<doc_id>": {
        "original":  "<texto clínico íntegro>",
        "gt_masked": "<texto con cada span PHI reemplazado por [**TIPO**]>"
      }
    }

El ground truth de MEDDOCAN viene en BRAT standoff: las anotaciones están en
un fichero .ann (T1\\tTIPO start end\\ttexto) y el texto en un .txt con el
mismo nombre base. Aquí leemos ambos, y generamos `gt_masked` reemplazando
cada span anotado por el marcador `[**TIPO**]`, exactamente igual que Carmen.
"""

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path

BRAT_LINE = re.compile(r'^(T\d+)\t(\S+)\s+(\d+)\s+(\d+)(?:\s+(\d+)\s+(\d+))*\t?(.*)$')

BASE_DIR = Path(__file__).resolve().parent.parent
MEDDOCAN_BRAT = BASE_DIR / "meddocan" / "corpus"
OUTPUT_PATH = BASE_DIR / "meddocan" / "raw_data.json"
GT_SPANS_PATH = BASE_DIR / "meddocan" / "gt_spans.json"

SPLITS = ["train", "dev", "test"]


def parse_brat_ann(ann_path: Path):
    """
    Parsea un fichero .ann de BRAT.

    Devuelve una lista de spans (start, end, entity_type) ordenada por start.
    Soporta spans discontinuos (varios pares start-end separados por ';').
    """
    spans = []
    with open(ann_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # En MEDDOCAN todas las líneas empiezan por T
            if not line.startswith("T"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            head = parts[1].split()
            etype = head[0]
            coords = head[1:]
            # Pares (start, end) contiguos; para spans discontinuos usamos
            # el start mínimo y el end máximo.
            pairs = []
            i = 0
            while i + 1 < len(coords):
                try:
                    s = int(coords[i])
                    e = int(coords[i + 1])
                except ValueError:
                    break
                pairs.append((s, e))
                i += 2
            if not pairs:
                continue
            start = min(s for s, _ in pairs)
            end = max(e for _, e in pairs)
            spans.append((start, end, etype))
    spans.sort(key=lambda x: (x[0], x[1]))
    return spans


def build_gt_masked(text: str, spans) -> str:
    """Reemplaza cada span por el marcador [**TIPO**], de derecha a izquierda."""
    masked = text
    for start, end, etype in sorted(spans, key=lambda s: s[0], reverse=True):
        masked = masked[:start] + f"[**{etype}**]" + masked[end:]
    return masked


def convert(splits=None, output_path=None):
    splits = splits or SPLITS
    output_path = output_path or OUTPUT_PATH

    data = {}
    gt_spans_data = {}
    type_counter = Counter()
    span_counter = 0
    n_docs = 0
    warnings = 0

    for split in splits:
        brat_dir = MEDDOCAN_BRAT / split / "brat"
        if not brat_dir.is_dir():
            print(f"   ⚠ No existe {brat_dir}")
            continue
        for ann_path in sorted(brat_dir.glob("*.ann")):
            txt_path = ann_path.with_suffix(".txt")
            if not txt_path.exists():
                print(f"   ⚠ Falta .txt para {ann_path.name}")
                continue
            text = txt_path.read_text(encoding="utf-8")
            spans = parse_brat_ann(ann_path)

            # Validación de offsets contra el texto (solo advertencia)
            for start, end, etype in spans:
                if not (0 <= start <= end <= len(text)):
                    warnings += 1
                    print(f"   ⚠ Span fuera de rango en {ann_path.name}: {etype} {start}-{end} (len={len(text)})")

            gt_masked = build_gt_masked(text, spans)
            doc_id = ann_path.stem
            data[doc_id] = {
                "original": text,
                "gt_masked": gt_masked,
            }
            gt_spans_data[doc_id] = [[s, e, t] for s, e, t in spans]
            for _, _, etype in spans:
                type_counter[etype] += 1
            span_counter += len(spans)
            n_docs += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(GT_SPANS_PATH, "w", encoding="utf-8") as f:
        json.dump(gt_spans_data, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("Conversión MEDDOCAN (BRAT) → formato Carmen")
    print("=" * 60)
    print(f"   Documentos: {n_docs}")
    print(f"   Spans PHI totales: {span_counter:,}")
    print(f"   Advertencias: {warnings}")
    print(f"\n   Tipos de entidad ({len(type_counter)}):")
    for etype, count in type_counter.most_common():
        print(f"     {etype:35s} {count:6d}")
    print(f"\n   Salida Carmen: {output_path}")
    print(f"   Salida GT spans exactos: {GT_SPANS_PATH}")
    return data, type_counter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convierte MEDDOCAN a formato Carmen")
    parser.add_argument("--splits", nargs="+", default=SPLITS,
                        help="Splits a convertir (default: train dev test)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help="Ruta del JSON de salida")
    args = parser.parse_args()
    convert(args.splits, args.output)
