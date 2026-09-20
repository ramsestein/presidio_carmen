# Evaluation Report: Presidio vs MEDDOCAN Dataset

**Date**: 2026-09-19 19:07
**Model**: spaCy `es_core_news_md` | **Confidence threshold**: 0.35 | **IoU**: ≥ 0.3
**Documents evaluated**: 1000 (train + dev + test)

---

## Global Summary (character level)

| Metric | Value |
|--------|-------|
| GT anonymized characters | 267,106 |
| Characters detected by Presidio | 254,097 |
| Intersection (TP chars) | 165,977 |
| Union (GT ∪ Pred) | 355,226 |
| False Positives (chars) | 88,120 |
| False Negatives (chars) | 101,129 |
| True Negatives (chars) | 2,532,743 |

### Aggregate metrics (accumulated over all documents)

| Metric | Value |
|--------|-------|
| **Jaccard** (global) | **0.4672** |
| **Precision** (global) | **0.6532** |
| **Recall** (global) | **0.6214** |
| **F1-Score** (global) | **0.6369** |
| **Specificity** (global) | **0.9664** |

### Per-document average metrics

| Metric | Value |
|--------|-------|
| Mean Jaccard | 0.4746 |
| Mean Precision | 0.6695 |
| Mean Recall | 0.6227 |
| Mean F1 | 0.6391 |

---

## Per-document Jaccard distribution

| Jaccard range | Documents | % |
|---------------|-----------|---|
| `1.0` | 0 | 0.0% |
| `0.8-1.0` | 0 | 0.0% |
| `0.6-0.8` | 59 | 5.9% |
| `0.4-0.6` | 757 | 75.7% |
| `0.2-0.4` | 182 | 18.2% |
| `0.0-0.2` | 2 | 0.2% |
| `0.0` | 0 | 0.0% |

---

## Metrics by Entity Type (MEDDOCAN, span level, IoU ≥ 0.3)

| Entity Type | TP | FN | Precision | Recall | F1 |
|-------------|----|----|-----------|--------|-----|
| `TERRITORIO` | 2013 | 1805 | 1.0000 | 0.5272 | 0.6904 |
| `FECHAS` | 2013 | 553 | 1.0000 | 0.7845 | 0.8792 |
| `EDAD_SUJETO_ASISTENCIA` | 2 | 2072 | 1.0000 | 0.0010 | 0.0019 |
| `NOMBRE_SUJETO_ASISTENCIA` | 1756 | 258 | 1.0000 | 0.8719 | 0.9316 |
| `NOMBRE_PERSONAL_SANITARIO` | 1899 | 99 | 1.0000 | 0.9505 | 0.9746 |
| `SEXO_SUJETO_ASISTENCIA` | 274 | 1567 | 1.0000 | 0.1488 | 0.2591 |
| `CALLE` | 614 | 1095 | 1.0000 | 0.3593 | 0.5286 |
| `PAIS` | 1335 | 88 | 1.0000 | 0.9382 | 0.9681 |
| `ID_SUJETO_ASISTENCIA` | 52 | 1090 | 1.0000 | 0.0455 | 0.0871 |
| `CORREO_ELECTRONICO` | 956 | 3 | 1.0000 | 0.9969 | 0.9984 |
| `ID_TITULACION_PERSONAL_SANITARIO` | 124 | 807 | 1.0000 | 0.1332 | 0.2351 |
| `ID_ASEGURAMIENTO` | 72 | 711 | 1.0000 | 0.0920 | 0.1684 |
| `HOSPITAL` | 381 | 144 | 1.0000 | 0.7257 | 0.8411 |
| `FAMILIARES_SUJETO_ASISTENCIA` | 21 | 395 | 1.0000 | 0.0505 | 0.0961 |
| `INSTITUCION` | 190 | 47 | 1.0000 | 0.8017 | 0.8899 |
| `ID_CONTACTO_ASISTENCIAL` | 13 | 135 | 1.0000 | 0.0878 | 0.1615 |
| `NUMERO_TELEFONO` | 7 | 102 | 1.0000 | 0.0642 | 0.1207 |
| `PROFESION` | 2 | 35 | 1.0000 | 0.0541 | 0.1026 |
| `NUMERO_FAX` | 4 | 24 | 1.0000 | 0.1429 | 0.2500 |
| `OTROS_SUJETO_ASISTENCIA` | 2 | 20 | 1.0000 | 0.0909 | 0.1667 |
| `CENTRO_SALUD` | 11 | 3 | 1.0000 | 0.7857 | 0.8800 |
| `ID_EMPLEO_PERSONAL_SANITARIO` | 0 | 1 | 0.0000 | 0.0000 | 0.0000 |
| **Total (all)** | **11741** | **11054** | **1.0000** | **0.5151** | **0.6799** |
| **Total (F1>0 only)** | **11741** | **11053** | **1.0000** | **0.5151** | **0.6799** | *(excludes: ID_EMPLEO_PERSONAL_SANITARIO)*
| **Total (F1≥0.20 only)** | **11570** | **6493** | **1.0000** | **0.6405** | **0.7809** | *(excludes: EDAD_SUJETO_ASISTENCIA, FAMILIARES_SUJETO_ASISTENCIA, ID_ASEGURAMIENTO, ID_CONTACTO_ASISTENCIAL, ID_EMPLEO_PERSONAL_SANITARIO, ID_SUJETO_ASISTENCIA, NUMERO_TELEFONO, OTROS_SUJETO_ASISTENCIA, PROFESION)*
| **Total (F1≥0.60 only)** | **10554** | **3000** | **1.0000** | **0.7787** | **0.8756** | *(excludes: CALLE, EDAD_SUJETO_ASISTENCIA, FAMILIARES_SUJETO_ASISTENCIA, ID_ASEGURAMIENTO, ID_CONTACTO_ASISTENCIAL, ID_EMPLEO_PERSONAL_SANITARIO, ID_SUJETO_ASISTENCIA, ID_TITULACION_PERSONAL_SANITARIO, NUMERO_FAX, NUMERO_TELEFONO, OTROS_SUJETO_ASISTENCIA, PROFESION, SEXO_SUJETO_ASISTENCIA)*

### False Positives by Presidio-detected entity type

| Presidio Type | FP Spans |
|---------------|----------|
| `LOCATION` | 5475 |
| `ORGANIZATION` | 2250 |
| `PERSON` | 1685 |
| `URL` | 1100 |
| `DATE_TIME` | 81 |
| `PHONE_NUMBER` | 14 |
| `EMAIL_ADDRESS` | 3 |

---

## Entity type distribution in the dataset

| Entity Type (MEDDOCAN) | Frequency |
|------------------------|-----------|
| `TERRITORIO` | 3818 |
| `FECHAS` | 2566 |
| `EDAD_SUJETO_ASISTENCIA` | 2074 |
| `NOMBRE_SUJETO_ASISTENCIA` | 2014 |
| `NOMBRE_PERSONAL_SANITARIO` | 1998 |
| `SEXO_SUJETO_ASISTENCIA` | 1841 |
| `CALLE` | 1709 |
| `PAIS` | 1423 |
| `ID_SUJETO_ASISTENCIA` | 1142 |
| `CORREO_ELECTRONICO` | 959 |
| `ID_TITULACION_PERSONAL_SANITARIO` | 931 |
| `ID_ASEGURAMIENTO` | 783 |
| `HOSPITAL` | 525 |
| `FAMILIARES_SUJETO_ASISTENCIA` | 416 |
| `INSTITUCION` | 237 |
| `ID_CONTACTO_ASISTENCIAL` | 148 |
| `NUMERO_TELEFONO` | 109 |
| `PROFESION` | 37 |
| `NUMERO_FAX` | 28 |
| `OTROS_SUJETO_ASISTENCIA` | 22 |
| `CENTRO_SALUD` | 14 |
| `ID_EMPLEO_PERSONAL_SANITARIO` | 1 |

---

## Comparison with other studies

| Study / Source | Domain | Presidio Result |
|---|---|---|
| **Kotevski et al., 2022** | Radiation oncology, Australia, 300 docs | F1 strict **0.8471**; F1 relaxed **0.8980** |
| **Pilán et al., 2022** | Legal / European Court of Human Rights | F1 ≈ **0.733** |
| **Alrazihi et al., 2025** | Neurosurgical notes, UK, 200 docs | F1 **0.60** |
| **PIIBench, 2026** | Multi-source PII benchmark | F1 **0.1385** |
| **This study (Carmen, 2026)** | Spanish clinical texts, 2000 docs | Global F1 **0.239** / detectable types **0.717** |
| **This study (MEDDOCAN)** | Spanish clinical texts, 1000 docs | Global F1 **0.6369** |

---

## Per-Document Statistics

| Statistic | Value |
|-----------|-------|
| Mean GT spans per doc | 22.8 |
| Mean detections per doc | 22.3 |
| Total time | 186.3s |
| Mean per document | 0.186s |
| Documents with Jaccard > 0 | 1000 |
| Documents without GT entities | 0 |

---

## Methodology

1. **Dataset**: MEDDOCAN (1000 clinical reports in Spanish; 1,000 SPACCC cases with manually annotated PHI).
2. **Ground truth**: exact BRAT spans (`meddocan/gt_spans.json`) converted from `meddocan/corpus/{train,dev,test}/brat/*.ann`.
3. **Analysis**: Presidio Analyzer with spaCy `es_core_news_md`, out-of-the-box (same configuration as Carmen).
4. **Metric**: binary character mask (1 = anonymized) → Jaccard, Precision, Recall, F1; plus span-level metrics by type with IoU ≥ 0.3.
5. **Limitations**: Presidio has no recognizers for many MEDDOCAN types (PROFESION, FAMILIARES_SUJETO_ASISTENCIA, EDAD, etc.); it operates on general Spanish, not clinical Spanish.

---
