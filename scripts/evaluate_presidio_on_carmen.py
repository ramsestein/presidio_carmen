#!/usr/bin/env python3
"""
Evaluación de Presidio contra el dataset Carmen (2000 documentos clínicos en español).

Enfoque: para cada documento se construye una máscara binaria de caracteres
(1 = anonimizado, 0 = no anonimizado) tanto para el ground truth como para
la predicción de Presidio, y se calculan métricas (Jaccard, Precision, Recall, F1).

Esto evita la complejidad de alinear spans exactos y permite una comparación
robusta aunque los formatos de anonimización diffieran.
"""

import json
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# ─── Configuration ───────────────────────────────────────────────────────

DATASET_PATH = "carmen/raw_data.json"
SAMPLE_SIZE = None  # Set to e.g. 50 for a quick test, None for full run
REPORT_PATH = "evaluation_report.md"

# ─── Ground truth parsing ────────────────────────────────────────────────

MARKER_PATTERN = re.compile(r'\[\*\*(\w+)\*\*\]')


def normalize_ws(text: str) -> str:
    """Colapsa cualquier whitespace a un solo espacio."""
    return re.sub(r'\s+', ' ', text).strip()


def _norm_to_orig_mapping(original: str) -> List[int]:
    """Construye mapping: norm_orig index -> posición en original."""
    mapping = []
    in_ws = False
    for oi, ch in enumerate(original):
        if ch in ' \t\n\r\f\v':
            if not in_ws:
                mapping.append(oi)
                in_ws = True
        else:
            mapping.append(oi)
            in_ws = False
    return mapping


def get_gt_mask(original: str, gt_masked: str) -> List[bool]:
    """Máscara binaria de GT (True = PII)."""
    if not MARKER_PATTERN.search(gt_masked):
        return [False] * len(original)
    spans = get_gt_spans(original, gt_masked)
    mask = [False] * len(original)
    for s, e, _ in spans:
        for i in range(s, e):
            if 0 <= i < len(mask):
                mask[i] = True
    return mask


def get_gt_spans(original: str, gt_masked: str) -> List[Tuple[int, int, str]]:
    """
    Extrae spans PII del ground truth con su tipo de entidad.

    Usa la alineación entre original y gt_masked (sin marcadores)
    para localizar qué texto fue reemplazado por cada [**TYPE**].

    Returns: lista de (start, end, entity_type) en el texto original.
    """
    if not MARKER_PATTERN.search(gt_masked):
        return []

    import difflib

    # 1. Extraer marcadores con sus tipos
    markers = list(MARKER_PATTERN.finditer(gt_masked))
    marker_types = [m.group(1) for m in markers]

    # 2. Construir texto "tokenizado": reemplazar cada marcador con \x00ID\x00
    tokens_seq = []
    last_end = 0
    for i, m in enumerate(markers):
        tokens_seq.append(gt_masked[last_end:m.start()])
        tokens_seq.append(f"\x00{i:X}\x00")
        last_end = m.end()
    tokens_seq.append(gt_masked[last_end:])
    tokenized_masked = "".join(tokens_seq)

    # 3. Normalizar ambos
    norm_orig = re.sub(r'\s+', ' ', original).strip()
    norm_tok = re.sub(r'\s+', ' ', tokenized_masked).strip()

    # 4. Alinear norm_tok con norm_orig
    matcher = difflib.SequenceMatcher(None, norm_tok, norm_orig, autojunk=False)

    # 5. Construir mapping norm_orig -> original
    no2orig = _norm_to_orig_mapping(original)

    # 6. Para cada opcode 'replace' que contenga un token, extraer el span en original
    gt_spans = []

    for op, a1, a2, b1, b2 in matcher.get_opcodes():
        if op != 'replace':
            continue
        # Buscar si alguna posición en [a1, a2) contiene un token
        tok_span = norm_tok[a1:a2]
        for i, marker_type in enumerate(marker_types):
            tok = f"\x00{i:X}\x00"
            pos = tok_span.find(tok)
            if pos >= 0:
                # Este reemplazo corresponde al marcador i
                # El span PII en norm_orig es [b1, b2)
                orig_start = no2orig[b1] if b1 < len(no2orig) else 0
                orig_end = no2orig[b2 - 1] + 1 if b2 - 1 < len(no2orig) else len(original)
                gt_spans.append((orig_start, orig_end, marker_type))
                break

    # Fallback para marcadores no encontrados en replace: búsqueda contextual
    found_mask = [False] * len(marker_types)
    for _, _, etype in gt_spans:
        for i, mt in enumerate(marker_types):
            if mt == etype and not found_mask[i]:
                found_mask[i] = True
                break

    # Para marcadores no encontrados, intentar búsqueda por contexto
    for i, (m, etype) in enumerate(zip(markers, marker_types)):
        if found_mask[i]:
            continue
        # Buscar contexto antes/después del marcador en gt_masked
        ctx_before = gt_masked[max(0, m.start() - 40):m.start()]
        ctx_after = gt_masked[m.end():min(len(gt_masked), m.end() + 40)]
        ctx_before_norm = re.sub(r'\s+', ' ', ctx_before).strip()
        ctx_after_norm = re.sub(r'\s+', ' ', ctx_after).strip()

        # Buscar en original
        search_from = 0
        for prev_s, prev_e, _ in gt_spans:
            search_from = max(search_from, prev_e)

        idx_before = norm_orig.find(ctx_before_norm, _norm_to_orig_mapping(original).index(search_from) if search_from < len(no2orig) else 0)
        if idx_before >= 0:
            orig_start = no2orig[idx_before + len(ctx_before_norm.split())] if idx_before + len(ctx_before_norm.split()) < len(no2orig) else 0
            # mejor: usar len del ctx_before en norm_orig
            orig_start_pos = idx_before + len(ctx_before_norm)
            if orig_start_pos < len(no2orig):
                orig_start = no2orig[orig_start_pos]
                # estimar end por ctx_after
                if ctx_after_norm:
                    idx_after = norm_orig.find(ctx_after_norm, orig_start_pos)
                    if idx_after >= 0:
                        orig_end = no2orig[idx_after - 1] + 1 if idx_after - 1 < len(no2orig) else len(original)
                    else:
                        orig_end = min(orig_start + 20, len(original))
                else:
                    orig_end = min(orig_start + 20, len(original))
                gt_spans.append((orig_start, orig_end, etype))

    return gt_spans


# ─── Presidio mask ──────────────────────────────────────────────────────


def create_analyzer(language: str = "es") -> AnalyzerEngine:
    """
    Crea un AnalyzerEngine de Presidio para español usando
    spaCy es_core_news_md. Sin modificaciones a recognizers,
    thresholds, o entidades: Presidio out-of-the-box con español.
    """
    import os
    config_path = os.path.join(os.path.dirname(__file__), "presidio_es_config.yaml")
    provider = NlpEngineProvider(conf_file=config_path)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=[language],
    )
    return analyzer


def get_presidio_spans(analyzer: AnalyzerEngine, text: str) -> List[Tuple[int, int, str, float]]:
    """Ejecuta Presidio Analyzer y devuelve lista de (start, end, entity_type, score)."""
    results = analyzer.analyze(text=text, language="es")
    return [(r.start, r.end, r.entity_type, r.score) for r in results]


def spans_to_mask(spans: List[Tuple[int, int, str, float]], text_len: int) -> List[bool]:
    """Convierte spans detectados a máscara binaria."""
    mask = [False] * text_len
    for start, end, _, _ in spans:
        for i in range(max(0, start), min(end, text_len)):
            mask[i] = True
    return mask


# ─── Metrics ─────────────────────────────────────────────────────────────

def span_iou(a_start, a_end, b_start, b_end) -> float:
    """Intersection over Union de dos spans."""
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    union = max(a_end - a_start, b_end - b_start, 1)
    return inter / union


@dataclass
class PerTypeMetrics:
    """Métricas para un tipo de entidad."""
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
    """Resultados de evaluación para un documento."""
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
    # Métricas por tipo de entidad Carmen
    per_type: dict  # {entity_type: PerTypeMetrics}
    # Falsos positivos por tipo Presidio
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
    iou_threshold: float = 0.3,
) -> Tuple[dict, Counter]:
    """
    Computa TP/FP/FN por tipo de entidad Carmen.
    Aparea spans GT con spans de Presidio por IoU.
    """
    per_type = defaultdict(PerTypeMetrics)
    fp_by_presidio = Counter()

    gt_used = [False] * len(gt_spans)
    pred_used = [False] * len(pred_spans)

    # Para cada GT span, buscar el mejor match en pred
    for gi, (gs, ge, gt) in enumerate(gt_spans):
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
            gt_used[gi] = True
            pred_used[best_idx] = True
        else:
            per_type[gt].fn += 1

    # FPs: pred spans no usados
    for pi, (ps, pe, pt, sc) in enumerate(pred_spans):
        if not pred_used[pi]:
            fp_by_presidio[pt] += 1

    return dict(per_type), fp_by_presidio


def evaluate_document(
    doc_id: str, original: str, gt_masked: str, analyzer: AnalyzerEngine
) -> EvalResult:
    """Evalúa Presidio en un solo documento: métricas globales + por tipo."""
    # --- Métricas por máscara de caracteres (globales) ---
    gt_mask = get_gt_mask(original, gt_masked)
    gt_spans_count = len(MARKER_PATTERN.findall(gt_masked))

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

    # --- Métricas por tipo de entidad ---
    gt_spans = get_gt_spans(original, gt_masked)
    per_type, fp_by_presidio = compute_per_type_metrics(gt_spans, pred_spans)

    return EvalResult(
        doc_id=doc_id,
        gt_n_spans=gt_spans_count,
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


# ─── Main evaluation ─────────────────────────────────────────────────────

def run_evaluation(dataset_path: str, sample_size: Optional[int] = None):
    """Run full evaluation on the Carmen dataset."""
    print("=" * 70)
    print("Evaluación de Presidio contra el dataset Carmen")
    print("=" * 70)

    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_docs = len(data)
    doc_keys = list(data.keys())
    if sample_size:
        import random
        random.seed(42)
        doc_keys = random.sample(doc_keys, min(sample_size, total_docs))

    print(f"   Documentos: {len(doc_keys)} (de {total_docs} totales)")

    print("\n🔧 Inicializando Presidio Analyzer (español)...")
    analyzer = create_analyzer()
    print("   ✓ Analyzer listo")

    print(f"\n📊 Evaluando {len(doc_keys)} documentos...")
    start_time = time.time()

    results: List[EvalResult] = []
    skipped = 0

    for i, doc_id in enumerate(doc_keys):
        item = data[doc_id]
        original = item['original']
        gt_masked = item['gt_masked']

        try:
            result = evaluate_document(doc_id, original, gt_masked, analyzer)
            results.append(result)
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"   ⚠ Error en {doc_id}: {e}")

        if (i + 1) % 200 == 0:
            elapsed = time.time() - start_time
            print(f"   Procesados {i+1}/{len(doc_keys)} docs ({elapsed:.1f}s)")

    elapsed = time.time() - start_time
    print(f"\n✅ Evaluación completada en {elapsed:.1f}s")
    if skipped:
        print(f"   ⚠ Documentos omitidos: {skipped}")

    generate_report(data, results, elapsed, sample_size)
    return results


def generate_report(data, results, elapsed, sample_size):
    """Generate a Markdown evaluation report."""
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
    for doc_id, item in data.items():
        types = MARKER_PATTERN.findall(item['gt_masked'])
        type_counter.update(types)

    report = f"""# Informe de Evaluación: Presidio vs Dataset Carmen

**Fecha**: {time.strftime('%Y-%m-%d %H:%M')}
**Modelo**: spaCy `es_core_news_md` | **Umbral confianza**: 0.35
**Documentos evaluados**: {n_docs}

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

    # ── Métricas por tipo de entidad Carmen ──
    # Agregar per-type metrics de todos los documentos
    aggregated_per_type = defaultdict(PerTypeMetrics)
    global_fp_by_presidio = Counter()

    for r in results:
        for etype, m in r.per_type.items():
            aggregated_per_type[etype] += m
        for ptype, count in r.fp_by_presidio_type.items():
            global_fp_by_presidio[ptype] += count

    report += f"""
---

## Métricas por Tipo de Entidad (Carmen)

| Tipo de Entidad | TP | FN | FP (Presidio) | Presición | Recall | F1 |
|-----------------|----|----|---------------|-----------|--------|-----|
"""

    # Ordenar por frecuencia descendente
    for etype in sorted(type_counter.keys(), key=lambda t: -type_counter[t]):
        m = aggregated_per_type.get(etype, PerTypeMetrics())
        report += (
            f"| `{etype}` | {m.tp} | {m.fn} | — "
            f"| {m.precision:.4f} | {m.recall:.4f} | {m.f1:.4f} |\n"
        )

    # Fila de totales (todos los tipos)
    total_m = sum(aggregated_per_type.values(), PerTypeMetrics())
    report += (
        f"| **Total (todos)** | **{total_m.tp}** | **{total_m.fn}** | — "
        f"| **{total_m.precision:.4f}** | **{total_m.recall:.4f}** | **{total_m.f1:.4f}** |\n"
    )

    # ── Totales excluyendo entidades no detectadas ──
    def fmt_filtered_row(label, types_dict):
        if not types_dict:
            return ""
        tm = sum(types_dict.values(), PerTypeMetrics())
        excluded = set(aggregated_per_type.keys()) - set(types_dict.keys())
        excl_names = ", ".join(sorted(excluded)) if excluded else ""
        note = f" *(excluye: {excl_names})*" if excl_names else ""
        return (
            f"| **{label}** | **{tm.tp}** | **{tm.fn}** | — "
            f"| **{tm.precision:.4f}** | **{tm.recall:.4f}** | **{tm.f1:.4f}** |{note}\n"
        )

    filtered_f1_0  = {t: m for t, m in aggregated_per_type.items() if m.f1 > 0}
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

| Tipo de Entidad (Carmen) | Frecuencia |
|--------------------------|-----------|
"""

    for etype, count in sorted(type_counter.items(), key=lambda x: -x[1]):
        report += f"| `{etype}` | {count} |\n"

    report += f"""
---

## Comparativa con otros estudios

| Estudio / Fuente | Dominio | Resultado Presidio |
|---|---|---|
| **Kotevski et al., 2022, Int J Med Inform** | Oncología radioterápica, Australia, 300 docs | P **0.8921**; R strict **0.8064**; **F1 strict 0.8471**; R relaxed **0.9039**; **F1 relaxed 0.8980** |
| **Friebely, 2022, tesis/disertación** | SSN en emails Enron | Presidio OOTB: P **0.8347**, R **1.0000**, **F1 0.9099**. Regex ajustado: P **0.9878**, R **1.0000**, **F1 0.9938** |
| **Text Anonymization Benchmark, Pilán et al., 2022** | Legal / European Court HR | Presidio default: P **0.761**, R **0.707**, **F1 ≈0.733**. Presidio +ORG: P **0.542**, R **0.782**, **F1 ≈0.640** |
| **Benchmarking Advanced Text Anonymisation Methods, 2024** | Benchmark general anonimización | P **0.83**, R **0.88**, **F1 0.85** |
| **Alrazihi et al., 2025** | Notas neuroquirúrgicas, UK, 200 docs | P **0.51**, R **0.74**, **F1 0.60** |
| **Cross-Domain Transfer and Few-Shot Learning for PII Recognition, 2025** | TAB / Wikipedia / i2b2 | TAB **F1 0.649**; Wikipedia **0.642**; i2b2 **0.573**; media **0.621** |
| **MathEd-PII, 2026** | Tutoring matemático | Presidio Large: P **0.254**, R **0.747**, **F1 0.379**. Presidio Transformer: P **0.230**, R **0.781**, **F1 0.355** |
| **PIIBench, 2026** | Benchmark multi-fuente PII | Presidio fue el mejor baseline, pero solo **F1 0.1385** |
| **Identification and Anonymization… Social Engineering Detection, 2026** | OSINT / social engineering | Presidio NER: **F1 0.74** en máquina no dedicada; **F1 0.79** en HPC |
| **SurrogateShield, 2026** | PII en queries LLM | Presidio comparable types: P **85.50%**, R **92.91%**, **F1 89.05%**. BERTScore F1 **0.8159** |
| **Este estudio (Carmen, 2026)** | **Textos clínicos español, 2000 docs** | **P {precision_global:.4f}**, **R {recall_global:.4f}**, **Jaccard {jaccard_global:.4f}**, **F1 {f1_global:.4f}** (global) |

Los F1 de Presidio varían según dominio:
| Contexto | Rango F1 |
|---|---|
| Tareas estrechas (SSN, emails Enron) | **0.85 – 0.99** |
| Textos generales / legales en inglés | **0.60 – 0.85** |
| Textos clínicos en inglés (Australia, UK) | **0.60 – 0.90** |
| Benchmark multi-fuente (PIIBench) | **0.14** |
| **Texto clínico español (Carmen)** | **{f1_global:.4f}** (global) |

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

1. **Dataset**: Carmen-I ({n_docs} documentos clínicos en español extraídos de {list(data.keys())[0].split('_')[0]} con anonimización manual)
2. **Análisis**: Presidio Analyzer con modelo spaCy `es_core_news_md` para español
3. **Métrica**: Para cada documento se construye una máscara binaria de caracteres (1 = anonimizado, 0 = no anonimizado) tanto para el ground truth (extrayendo marcadores `[**TYPE**]` del texto anonimizado y alineándolos con el original) como para la predicción de Presidio. Luego se calcula **Jaccard**, Precision, Recall y F1 sobre estas máscaras.
4. **Limitaciones**:
   - La alineación de caracteres entre original y texto anonimizado puede tener imprecisiones debido a diferencias en saltos de línea y espacios
   - Presidio no tiene recognizers específicos para todos los tipos de entidad de Carmen (ej. `PROFESION`, `FAMILIARES_SUJETO_ASISTENCIA`)
   - El análisis opera sobre español general, no sobre vocabulario clínico especializado

---
"""

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📝 Reporte generado: {REPORT_PATH}")

    print(f"\n{'='*70}")
    print("RESUMEN GLOBAL (máscara de caracteres):")
    print(f"  Jaccard:   {jaccard_global:.4f}")
    print(f"  Precision: {precision_global:.4f}")
    print(f"  Recall:    {recall_global:.4f}")
    print(f"  F1:        {f1_global:.4f}")
    print(f"  Spans GT:  {total_gt_spans}  Pred: {total_pred_spans}")
    print(f"  TP chars: {total_intersection:,}  FP chars: {total_fp:,}  FN chars: {total_fn:,}")

    print("\n📊 MÉTRICAS POR TIPO DE ENTIDAD (span-level, IoU≥0.3):")
    print(f"  {'Tipo':30s} {'TP':>4s} {'FN':>4s} {'Prec':>7s} {'Rec':>7s} {'F1':>7s}")
    print(f"  {'-'*30} {'-'*4} {'-'*4} {'-'*7} {'-'*7} {'-'*7}")
    for etype in sorted(type_counter.keys(), key=lambda t: -type_counter[t]):
        m = aggregated_per_type.get(etype, PerTypeMetrics())
        if m.tp + m.fn > 0:
            print(f"  {etype:30s} {m.tp:4d} {m.fn:4d} {m.precision:7.4f} {m.recall:7.4f} {m.f1:7.4f}")
    total_m = sum(aggregated_per_type.values(), PerTypeMetrics())
    print(f"  {'─'*30} {'─'*4} {'─'*4} {'─'*7} {'─'*7} {'─'*7}")
    print(f"  {'TOTAL (todos)':30s} {total_m.tp:4d} {total_m.fn:4d} {total_m.precision:7.4f} {total_m.recall:7.4f} {total_m.f1:7.4f}")

    # Totales excluyendo tipos no detectados
    def print_filtered(label, types_dict):
        if not types_dict:
            return
        tm = sum(types_dict.values(), PerTypeMetrics())
        excluded = set(aggregated_per_type.keys()) - set(types_dict.keys())
        excl_n = len(excluded)
        print(f"  {label:30s} {tm.tp:4d} {tm.fn:4d} {tm.precision:7.4f} {tm.recall:7.4f} {tm.f1:7.4f}  (excluye {excl_n} tipos)")

    print_filtered('TOTAL (solo F1>0)',   {t: m for t, m in aggregated_per_type.items() if m.f1 > 0})
    print_filtered('TOTAL (solo F1≥0.20)', {t: m for t, m in aggregated_per_type.items() if m.f1 >= 0.20})
    print_filtered('TOTAL (solo F1≥0.60)', {t: m for t, m in aggregated_per_type.items() if m.f1 >= 0.60})

    print(f"{'='*70}")


# ─── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = SAMPLE_SIZE
    if '--sample' in sys.argv:
        idx = sys.argv.index('--sample')
        sample = int(sys.argv[idx + 1])
    if '--full' in sys.argv:
        sample = None

    run_evaluation(DATASET_PATH, sample_size=sample)
