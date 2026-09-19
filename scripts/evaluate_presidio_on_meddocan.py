#!/usr/bin/env python3
"""
Evaluación de Presidio contra el dataset MEDDOCAN (1.000 informes clínicos en
español, anotados en formato BRAT).

Metodología idéntica a la usada con Carmen (scripts/evaluate_presidio_on_carmen.py):
para cada documento se construye una máscara binaria de caracteres (1 = PII,
0 = no PII) tanto para el ground truth como para la predicción de Presidio, y
se calculan Jaccard, Precision, Recall y F1. Además se calculan métricas a
nivel de span por tipo de entidad con umbral IoU ≥ 0.3.

Diferencia con Carmen: aquí el ground truth se lee de los spans BRAT exactos
(meddocan/gt_spans.json) en lugar de reconstruirlos por alineación de
marcadores, lo que elimina el error de alineación. Presidio se ejecuta igual,
out-of-the-box con spaCy es_core_news_md.
"""

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# ─── Configuration ───────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(BASE_DIR, "meddocan", "raw_data.json")
GT_SPANS_PATH = os.path.join(BASE_DIR, "meddocan", "gt_spans.json")
SAMPLE_SIZE = None  # e.g. 50 para prueba rápida, None para todo
REPORT_PATH = os.path.join(BASE_DIR, "meddocan_evaluation_report.md")
IOU_THRESHOLD = 0.3

# ─── Presidio ────────────────────────────────────────────────────────────


def create_analyzer(language: str = "es") -> AnalyzerEngine:
    """AnalyzerEngine de Presidio para español, out-of-the-box."""
    config_path = os.path.join(BASE_DIR, "scripts", "presidio_es_config.yaml")
    provider = NlpEngineProvider(conf_file=config_path)
    nlp_engine = provider.create_engine()
    return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[language])


def get_presidio_spans(analyzer: AnalyzerEngine, text: str) -> List[Tuple[int, int, str, float]]:
    results = analyzer.analyze(text=text, language="es")
    return [(r.start, r.end, r.entity_type, r.score) for r in results]


def spans_to_mask(spans, text_len: int) -> List[bool]:
    mask = [False] * text_len
    for start, end, *_ in spans:
        for i in range(max(0, start), min(end, text_len)):
            mask[i] = True
    return mask


# ─── Métricas ────────────────────────────────────────────────────────────


def span_iou(a_start, a_end, b_start, b_end) -> float:
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    union = max(a_end - a_start, b_end - b_start, 1)
    return inter / union


@dataclass
class PerTypeMetrics:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def __add__(self, other):
        return PerTypeMetrics(
            tp=self.tp + other.tp,
            fp=self.fp + other.fp,
            fn=self.fn + other.fn,
        )


@dataclass
class EvalResult:
    doc_id: str
    gt_n_spans: int
    pred_n_spans: int
    gt_chars: int
    pred_chars: int
    intersection: int
    union: int
    fp_chars: int
    fn_chars: int
    true_negatives: int
    per_type: dict
    fp_by_presidio_type: Counter

    @property
    def jaccard(self) -> float:
        return self.intersection / self.union if self.union > 0 else 1.0

    @property
    def precision(self) -> float:
        return self.intersection / self.pred_chars if self.pred_chars > 0 else 0.0

    @property
    def recall(self) -> float:
        return self.intersection / self.gt_chars if self.gt_chars > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def specificity(self) -> float:
        tn = self.true_negatives
        total_non_gt = tn + self.fp_chars
        return tn / total_non_gt if total_non_gt > 0 else 1.0


def compute_per_type_metrics(
    gt_spans: List[Tuple[int, int, str]],
    pred_spans: List[Tuple[int, int, str, float]],
    iou_threshold: float = IOU_THRESHOLD,
) -> Tuple[dict, Counter]:
    """TP/FN por tipo de entidad MEDDOCAN y FP por tipo de Presidio."""
    per_type = defaultdict(PerTypeMetrics)
    fp_by_presidio = Counter()

    pred_used = [False] * len(pred_spans)

    for gs, ge, gt in gt_spans:
        best_idx = None
        best_iou = 0
        for pi, (ps, pe, pt, sc) in enumerate(pred_spans):
            if pred_used[pi]:
                continue
            iou = span_iou(gs, ge, ps, pe)
            if iou > best_iou:
                best_iou = iou
                best_idx = pi
        if best_iou >= iou_threshold and best_idx is not None:
            per_type[gt].tp += 1
            pred_used[best_idx] = True
        else:
            per_type[gt].fn += 1

    for pi, (ps, pe, pt, sc) in enumerate(pred_spans):
        if not pred_used[pi]:
            fp_by_presidio[pt] += 1

    return dict(per_type), fp_by_presidio


def evaluate_document(
    doc_id: str,
    original: str,
    gt_spans: List[Tuple[int, int, str]],
    analyzer: AnalyzerEngine,
) -> EvalResult:
    gt_mask = spans_to_mask(gt_spans, len(original))

    pred_spans = get_presidio_spans(analyzer, original)
    pred_mask = spans_to_mask(pred_spans, len(original))

    text_len = len(original)
    intersection = gt_chars = pred_chars = fp_chars = fn_chars = tn = 0
    for i in range(text_len):
        is_gt = gt_mask[i]
        is_pred = pred_mask[i]
        if is_gt:
            gt_chars += 1
            if is_pred:
                intersection += 1
            else:
                fn_chars += 1
        elif is_pred:
            fp_chars += 1
        else:
            tn += 1
        if is_pred:
            pred_chars += 1

    union = gt_chars + fp_chars

    per_type, fp_by_presidio = compute_per_type_metrics(gt_spans, pred_spans)

    return EvalResult(
        doc_id=doc_id,
        gt_n_spans=len(gt_spans),
        pred_n_spans=len(pred_spans),
        gt_chars=gt_chars,
        pred_chars=pred_chars,
        intersection=intersection,
        union=union,
        fp_chars=fp_chars,
        fn_chars=fn_chars,
        true_negatives=tn,
        per_type=per_type,
        fp_by_presidio_type=fp_by_presidio,
    )


# ─── Evaluación principal ────────────────────────────────────────────────


def run_evaluation(sample_size: Optional[int] = None):
    print("=" * 70)
    print("Evaluación de Presidio contra el dataset MEDDOCAN")
    print("=" * 70)

    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(GT_SPANS_PATH, "r", encoding="utf-8") as f:
        gt_spans_data = json.load(f)

    doc_keys = list(data.keys())
    total_docs = len(doc_keys)
    if sample_size:
        import random
        random.seed(42)
        doc_keys = random.sample(doc_keys, min(sample_size, total_docs))

    print(f"   Documentos: {len(doc_keys)} (de {total_docs} totales)")

    print("\nInicializando Presidio Analyzer (español)...")
    analyzer = create_analyzer()
    print("   Analyzer listo")

    print(f"\nEvaluando {len(doc_keys)} documentos...")
    start_time = time.time()

    results: List[EvalResult] = []
    skipped = 0
    for i, doc_id in enumerate(doc_keys):
        original = data[doc_id]["original"]
        gt_spans = [tuple(s) for s in gt_spans_data.get(doc_id, [])]
        try:
            result = evaluate_document(doc_id, original, gt_spans, analyzer)
            results.append(result)
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"   Error en {doc_id}: {e}")

        if (i + 1) % 200 == 0:
            elapsed = time.time() - start_time
            print(f"   Procesados {i+1}/{len(doc_keys)} docs ({elapsed:.1f}s)")

    elapsed = time.time() - start_time
    print(f"\nEvaluación completada en {elapsed:.1f}s")
    if skipped:
        print(f"   Documentos omitidos: {skipped}")

    generate_report(gt_spans_data, results, elapsed, sample_size)
    return results


def generate_report(gt_spans_data, results, elapsed, sample_size):
    n_docs = len(results)
    if n_docs == 0:
        print("No results to report.")
        return

    total_gt_chars = sum(r.gt_chars for r in results)
    total_pred_chars = sum(r.pred_chars for r in results)
    total_intersection = sum(r.intersection for r in results)
    total_union = sum(r.union for r in results)
    total_fp = sum(r.fp_chars for r in results)
    total_fn = sum(r.fn_chars for r in results)
    total_tn = sum(r.true_negatives for r in results)
    total_gt_spans = sum(r.gt_n_spans for r in results)
    total_pred_spans = sum(r.pred_n_spans for r in results)

    jaccard_global = total_intersection / total_union if total_union > 0 else 1.0
    precision_global = total_intersection / total_pred_chars if total_pred_chars > 0 else 0.0
    recall_global = total_intersection / total_gt_chars if total_gt_chars > 0 else 0.0
    f1_global = (2 * precision_global * recall_global / (precision_global + recall_global)
                 if (precision_global + recall_global) > 0 else 0.0)
    specificity_global = total_tn / (total_tn + total_fp) if (total_tn + total_fp) > 0 else 1.0

    avg_jaccard = sum(r.jaccard for r in results) / n_docs
    avg_precision = sum(r.precision for r in results) / n_docs
    avg_recall = sum(r.recall for r in results) / n_docs
    avg_f1 = sum(r.f1 for r in results) / n_docs

    jaccard_buckets = Counter()
    for r in results:
        j = r.jaccard
        if j == 1.0:
            jaccard_buckets["1.0"] += 1
        elif j >= 0.8:
            jaccard_buckets["0.8-1.0"] += 1
        elif j >= 0.6:
            jaccard_buckets["0.6-0.8"] += 1
        elif j >= 0.4:
            jaccard_buckets["0.4-0.6"] += 1
        elif j >= 0.2:
            jaccard_buckets["0.2-0.4"] += 1
        elif j > 0:
            jaccard_buckets["0.0-0.2"] += 1
        else:
            jaccard_buckets["0.0"] += 1

    type_counter = Counter()
    for doc_id, spans in gt_spans_data.items():
        for _, _, etype in spans:
            type_counter[etype] += 1

    report = f"""# Informe de Evaluación: Presidio vs Dataset MEDDOCAN

**Fecha**: {time.strftime('%Y-%m-%d %H:%M')}
**Modelo**: spaCy `es_core_news_md` | **Umbral confianza**: 0.35 | **IoU**: ≥ {IOU_THRESHOLD}
**Documentos evaluados**: {n_docs} (train + dev + test)

---

## Resumen Global (a nivel de carácter)

| Métrica | Valor |
|---------|-------|
| Caracteres GT anonimizados | {total_gt_chars:,} |
| Caracteres detectados por Presidio | {total_pred_chars:,} |
| Intersección (TP chars) | {total_intersection:,} |
| Unión (GT ∪ Pred) | {total_union:,} |
| Falsos Positivos (chars) | {total_fp:,} |
| Falsos Negativos (chars) | {total_fn:,} |
| Verdaderos Negativos (chars) | {total_tn:,} |

### Métricas agregadas (acumuladas sobre todos los documentos)

| Métrica | Valor |
|---------|-------|
| **Jaccard** (global) | **{jaccard_global:.4f}** |
| **Precision** (global) | **{precision_global:.4f}** |
| **Recall** (global) | **{recall_global:.4f}** |
| **F1-Score** (global) | **{f1_global:.4f}** |
| **Specificity** (global) | **{specificity_global:.4f}** |

### Métricas promedio por documento

| Métrica | Valor |
|---------|-------|
| Jaccard promedio | {avg_jaccard:.4f} |
| Precision promedio | {avg_precision:.4f} |
| Recall promedio | {avg_recall:.4f} |
| F1 promedio | {avg_f1:.4f} |

---

## Distribución de Jaccard por documento

| Rango Jaccard | Documentos | % |
|---------------|-----------|---|
"""

    for bucket in ["1.0", "0.8-1.0", "0.6-0.8", "0.4-0.6", "0.2-0.4", "0.0-0.2", "0.0"]:
        count = jaccard_buckets.get(bucket, 0)
        pct = count / n_docs * 100
        report += f"| `{bucket}` | {count} | {pct:.1f}% |\n"

    aggregated_per_type = defaultdict(PerTypeMetrics)
    global_fp_by_presidio = Counter()
    for r in results:
        for etype, m in r.per_type.items():
            aggregated_per_type[etype] += m
        for ptype, count in r.fp_by_presidio_type.items():
            global_fp_by_presidio[ptype] += count

    report += f"""
---

## Métricas por Tipo de Entidad (MEDDOCAN, span-level, IoU ≥ {IOU_THRESHOLD})

| Tipo de Entidad | TP | FN | Precision | Recall | F1 |
|-----------------|----|----|-----------|--------|-----|
"""

    for etype in sorted(type_counter.keys(), key=lambda t: -type_counter[t]):
        m = aggregated_per_type.get(etype, PerTypeMetrics())
        report += (
            f"| `{etype}` | {m.tp} | {m.fn} "
            f"| {m.precision:.4f} | {m.recall:.4f} | {m.f1:.4f} |\n"
        )

    total_m = sum(aggregated_per_type.values(), PerTypeMetrics())
    report += (
        f"| **Total (todos)** | **{total_m.tp}** | **{total_m.fn}** "
        f"| **{total_m.precision:.4f}** | **{total_m.recall:.4f}** | **{total_m.f1:.4f}** |\n"
    )

    def fmt_filtered_row(label, types_dict):
        if not types_dict:
            return ""
        tm = sum(types_dict.values(), PerTypeMetrics())
        excluded = set(aggregated_per_type.keys()) - set(types_dict.keys())
        excl_names = ", ".join(sorted(excluded)) if excluded else ""
        note = f" *(excluye: {excl_names})*" if excl_names else ""
        return (
            f"| **{label}** | **{tm.tp}** | **{tm.fn}** | "
            f"**{tm.precision:.4f}** | **{tm.recall:.4f}** | **{tm.f1:.4f}** |{note}\n"
        )

    filtered_f1_0 = {t: m for t, m in aggregated_per_type.items() if m.f1 > 0}
    filtered_f1_20 = {t: m for t, m in aggregated_per_type.items() if m.f1 >= 0.20}
    filtered_f1_60 = {t: m for t, m in aggregated_per_type.items() if m.f1 >= 0.60}

    report += fmt_filtered_row("Total (solo F1>0)", filtered_f1_0)
    report += fmt_filtered_row("Total (solo F1≥0.20)", filtered_f1_20)
    report += fmt_filtered_row("Total (solo F1≥0.60)", filtered_f1_60)

    report += f"""
### Falsos Positivos por tipo de entidad detectado por Presidio

| Tipo Presidio | Spans FP |
|---------------|----------|
"""

    for ptype, count in global_fp_by_presidio.most_common():
        report += f"| `{ptype}` | {count} |\n"

    report += f"""
---

## Distribución de tipos de entidad en el dataset

| Tipo de Entidad (MEDDOCAN) | Frecuencia |
|--------------------------|-----------|
"""

    for etype, count in sorted(type_counter.items(), key=lambda x: -x[1]):
        report += f"| `{etype}` | {count} |\n"

    report += f"""
---

## Comparativa con otros estudios

| Estudio / Fuente | Dominio | Resultado Presidio |
|---|---|---|
| **Kotevski et al., 2022** | Oncología radioterápica, Australia, 300 docs | F1 strict **0.8471**; F1 relaxed **0.8980** |
| **Pilán et al., 2022** | Legal / European Court HR | F1 ≈ **0.733** |
| **Alrazihi et al., 2025** | Notas neuroquirúrgicas, UK, 200 docs | F1 **0.60** |
| **PIIBench, 2026** | Benchmark multi-fuente PII | F1 **0.1385** |
| **Este estudio (Carmen, 2026)** | Textos clínicos español, 2000 docs | F1 global **0.239** / tipos detectables **0.717** |
| **Este estudio (MEDDOCAN)** | Textos clínicos español, 1000 docs | F1 global **{f1_global:.4f}** |

---

## Estadísticas por Documento

| Estadística | Valor |
|-------------|-------|
| Promedio spans GT por doc | {total_gt_spans / n_docs:.1f} |
| Promedio detecciones por doc | {total_pred_spans / n_docs:.1f} |
| Tiempo total | {elapsed:.1f}s |
| Promedio por documento | {elapsed / n_docs:.3f}s |
| Documentos con Jaccard > 0 | {sum(1 for r in results if r.jaccard > 0)} |
| Documentos sin entidades GT | {sum(1 for r in results if r.gt_n_spans == 0)} |

---

## Metodología

1. **Dataset**: MEDDOCAN ({n_docs} informes clínicos en español; 1.000 casos de SPACCC con PHI anotado manualmente).
2. **Ground truth**: spans BRAT exactos (`meddocan/gt_spans.json`) convertidos desde `meddocan/corpus/{{train,dev,test}}/brat/*.ann`.
3. **Análisis**: Presidio Analyzer con spaCy `es_core_news_md`, out-of-the-box (misma configuración que Carmen).
4. **Métrica**: máscara binaria de caracteres (1 = anonimizado) → Jaccard, Precision, Recall, F1; y métricas a nivel de span por tipo con IoU ≥ {IOU_THRESHOLD}.
5. **Limitaciones**: Presidio no tiene recognizers para muchos tipos MEDDOCAN (PROFESION, FAMILIARES_SUJETO_ASISTENCIA, EDAD, etc.); opera sobre español general, no clínico.

---
"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReporte generado: {REPORT_PATH}")

    print(f"\n{'='*70}")
    print("RESUMEN GLOBAL (máscara de caracteres):")
    print(f"  Jaccard:   {jaccard_global:.4f}")
    print(f"  Precision: {precision_global:.4f}")
    print(f"  Recall:    {recall_global:.4f}")
    print(f"  F1:        {f1_global:.4f}")
    print(f"  Spans GT:  {total_gt_spans}  Pred: {total_pred_spans}")
    print(f"  TP chars: {total_intersection:,}  FP chars: {total_fp:,}  FN chars: {total_fn:,}")

    print(f"\nMÉTRICAS POR TIPO DE ENTIDAD (span-level, IoU≥{IOU_THRESHOLD}):")
    print(f"  {'Tipo':35s} {'TP':>5s} {'FN':>5s} {'Prec':>7s} {'Rec':>7s} {'F1':>7s}")
    print(f"  {'-'*35} {'-'*5} {'-'*5} {'-'*7} {'-'*7} {'-'*7}")
    for etype in sorted(type_counter.keys(), key=lambda t: -type_counter[t]):
        m = aggregated_per_type.get(etype, PerTypeMetrics())
        print(f"  {etype:35s} {m.tp:5d} {m.fn:5d} {m.precision:7.4f} {m.recall:7.4f} {m.f1:7.4f}")
    print(f"  {'-'*35} {'-'*5} {'-'*5} {'-'*7} {'-'*7} {'-'*7}")
    print(f"  {'TOTAL (todos)':35s} {total_m.tp:5d} {total_m.fn:5d} {total_m.precision:7.4f} {total_m.recall:7.4f} {total_m.f1:7.4f}")

    def print_filtered(label, types_dict):
        if not types_dict:
            return
        tm = sum(types_dict.values(), PerTypeMetrics())
        excluded = set(aggregated_per_type.keys()) - set(types_dict.keys())
        print(f"  {label:35s} {tm.tp:5d} {tm.fn:5d} {tm.precision:7.4f} {tm.recall:7.4f} {tm.f1:7.4f}  (excluye {len(excluded)} tipos)")

    print_filtered('TOTAL (solo F1>0)', {t: m for t, m in aggregated_per_type.items() if m.f1 > 0})
    print_filtered('TOTAL (solo F1≥0.20)', {t: m for t, m in aggregated_per_type.items() if m.f1 >= 0.20})
    print_filtered('TOTAL (solo F1≥0.60)', {t: m for t, m in aggregated_per_type.items() if m.f1 >= 0.60})

    print(f"{'='*70}")


if __name__ == "__main__":
    sample = SAMPLE_SIZE
    if '--sample' in sys.argv:
        idx = sys.argv.index('--sample')
        sample = int(sys.argv[idx + 1])
    if '--full' in sys.argv:
        sample = None

    run_evaluation(sample_size=sample)
