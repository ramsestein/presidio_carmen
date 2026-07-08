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


def get_gt_mask(original: str, gt_masked: str) -> List[bool]:
    """
    Construye la máscara binaria de caracteres del ground truth.

    Enfoque: diff entre original y gt_masked (sin marcadores), ambos
    normalizados. Las partes eliminadas (en original, no en clean) son PII.

    Returns: lista de bool del mismo largo que `original`, True donde hay PII.
    """
    if not MARKER_PATTERN.search(gt_masked):
        return [False] * len(original)

    import difflib

    # Normalizar ambos textos
    norm_orig = re.sub(r'\s+', ' ', original).strip()

    # gt_masked sin marcadores
    clean = re.sub(r'\[\*\*\w+\*\*\]', '', gt_masked)
    norm_clean = re.sub(r'\s+', ' ', clean).strip()

    # Diff
    matcher = difflib.SequenceMatcher(None, norm_orig, norm_clean, autojunk=False)

    # Extraer spans PII: opcode 'delete' significa texto en original no en clean
    pii_spans = []  # (start, end) en norm_orig
    for op, a1, a2, b1, b2 in matcher.get_opcodes():
        if op == 'delete':
            pii_spans.append((a1, a2))

    # Construir mapping: norm_orig index -> posiciones en original
    no2orig = []
    in_ws = False
    for oi, ch in enumerate(original):
        if ch in ' \t\n\r\f\v':
            if not in_ws:
                no2orig.append(oi)
                in_ws = True
        else:
            no2orig.append(oi)
            in_ws = False

    # Construir máscara
    mask = [False] * len(original)
    for a1, a2 in pii_spans:
        for no_idx in range(a1, min(a2, len(no2orig))):
            oi = no2orig[no_idx]
            if 0 <= oi < len(mask):
                mask[oi] = True
        # También marcar whitespace antes/después si existe
        if a1 > 0 and a1 - 1 < len(no2orig):
            ws_pos = no2orig[a1 - 1]
            if ws_pos < len(mask) and original[ws_pos] in ' \t\n\r\f\v':
                # El espacio antes del PII podría ser parte del texto original
                pass

    return mask


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


def evaluate_document(
    doc_id: str, original: str, gt_masked: str, analyzer: AnalyzerEngine
) -> EvalResult:
    """Evalúa Presidio en un solo documento usando máscaras de caracteres."""
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

    report += f"""
---

## Distribución de tipos de entidad en el dataset

| Tipo de Entidad (Carmen) | Frecuencia |
|--------------------------|-----------|
"""

    for etype, count in sorted(type_counter.items(), key=lambda x: -x[1]):
        report += f"| `{etype}` | {count} |\n"

    report += f"""
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
