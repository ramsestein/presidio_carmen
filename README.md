# Presidio Carmen

Evaluation of **Presidio Analyzer** (Microsoft) against the **Carmen** dataset — 2000 Spanish clinical documents with manual anonymization.

---

## ⚙️ Configuration

| Parameter | Value |
|---|---|
| Presidio | v2.2.363 (out-of-the-box, unmodified) |
| NLP model | spaCy `es_core_news_md` |
| Language | Spanish (`es`) |
| Dataset | Carmen-I, 2000 clinical documents |
| Entity types | 18 (FECHAS, HOSPITAL, PERSONA, etc.) |
| Hardware | CPU |
| **Total time** | **120.8s** (~0.06s/doc) |

---

## 📊 Global Summary (character mask)

| Metric | Value |
|---|---|
| **Jaccard** | **0.1357** |
| **Precision** | **0.1588** |
| **Recall** | **0.4832** |
| **F1-Score** | **0.2390** |

### Per-document Jaccard distribution

| Range | Docs | % |
|---|---|---|
| 1.0 | 21 | 1.1% |
| 0.8–1.0 | 7 | 0.4% |
| 0.6–0.8 | 44 | 2.2% |
| 0.4–0.6 | 80 | 4.0% |
| 0.2–0.4 | 256 | 12.8% |
| 0.0–0.2 | 735 | 36.8% |
| 0.0 | 857 | 42.9% |

---

## 📈 Metrics by Entity Type (span-level, IoU ≥ 0.3)

| Carmen Type | TP | FN | Recall | F1 |
|---|---|---|---|---|
| `ID_CONTACTO_ASISTENCIAL` | 2 | 0 | 1.0000 | **1.0000** |
| `CALLE` | 17 | 1 | 0.9444 | **0.9714** |
| `PAIS` | 107 | 10 | 0.9145 | **0.9554** |
| `INSTITUCION` | 107 | 16 | 0.8699 | **0.9304** |
| `TERRITORIO` | 74 | 15 | 0.8315 | **0.9080** |
| `CENTRO_SALUD` | 42 | 9 | 0.8235 | **0.9032** |
| `HOSPITAL` | 255 | 55 | 0.8226 | **0.9027** |
| `NOMBRE_PERSONAL_SANITARIO` | 123 | 27 | 0.8200 | **0.9011** |
| `ID_SUJETO_ASISTENCIA` | 8 | 6 | 0.5714 | **0.7273** |
| `FECHAS` | 1898 | 1941 | 0.4944 | **0.6617** |
| `OTROS_SUJETO_ASISTENCIA` | 11 | 26 | 0.2973 | **0.4583** |
| `SEXO_SUJETO_ASISTENCIA` | 116 | 332 | 0.2589 | **0.4113** |
| `NUMERO_IDENTIF` | 22 | 171 | 0.1140 | **0.2047** |
| `PROFESION` | 9 | 82 | 0.0989 | **0.1800** |
| `FAMILIARES_SUJETO_ASISTENCIA` | 20 | 275 | 0.0678 | **0.1270** |
| `EDAD_SUJETO_ASISTENCIA` | 17 | 724 | 0.0229 | **0.0449** |
| `NUMERO_TELEFONO` | 0 | 15 | 0.0000 | **0.0000** |
| `URL_WEB` | 0 | 0 | — | — |

### Filtered totals

| Filter | TP | FN | Recall | F1 | Excludes |
|---|---|---|---|---|---|
| **All** | 2,828 | 3,705 | 0.433 | **0.604** | — |
| F1 > 0 only | 2,828 | 3,690 | 0.434 | **0.605** | NUMERO_TELEFONO |
| F1 ≥ 0.20 only | 2,782 | 2,609 | **0.516** | **0.681** | 4 undetectable types |
| F1 ≥ 0.60 only | 2,633 | 2,080 | **0.559** | **0.717** | 7 types with the lowest F1 |

### False Positives by Presidio type

| Presidio Type | FP Spans |
|---|---|
| `ORGANIZATION` | 8,560 |
| `LOCATION` | 6,910 |
| `PERSON` | 5,571 |
| `DATE_TIME` | 900 |
| `URL` | 233 |
| `PHONE_NUMBER` | 46 |
| `IP_ADDRESS` | 1 |

---

## 🧠 Interpretation

### ✅ What Presidio detects well (F1 > 0.80)
| Type | How? |
|---|---|
| **HOSPITAL, CENTRO_SALUD, INSTITUCION** | NER ORGANIZATION |
| **PAIS, CALLE, TERRITORIO** | NER LOCATION/GPE |
| **NOMBRE_PERSONAL_SANITARIO** | NER PERSON |

### ⚠️ Partial detection
| Type | Problem |
|---|---|
| **FECHAS** (F1 0.66) | Detects `dd/mm/yy` formats but not free-text dates |
| **ID_SUJETO_ASISTENCIA** (F1 0.73) | Detects some as PERSON |

### ❌ Not detected
| Type | Reason |
|---|---|
| **PROFESION, FAMILIARES** | Semantic entities without a recognizer |
| **EDAD** | Presidio has no age recognizer |
| **NUMERO_TELEFONO** (F1 0.0) | Regex does not cover the Spanish format |
| **NUMERO_IDENTIF** (F1 0.20) | ES_NIF/ES_NIE cover it only partially |

---

## ⏱ Performance

| Measurement | Value |
|---|---|
| Documents processed | 2,000 |
| Total time | **120.8 seconds** |
| Mean per document | **0.060 seconds** |
| Total GT spans | 8,227 |
| Total Presidio detections | 25,049 |
| Mean GT spans per doc | 4.1 |
| Mean detections per doc | 12.5 |
| Docs without GT entities | 461 (23%) |

---

## 🔬 Comparison with other studies

| Study | Domain | Presidio F1 |
|---|---|---|
| **Kotevski et al., 2022** — Oncology, Australia | Clinical EN | **0.847 / 0.898** (strict/relaxed) |
| **Friebely, 2022** — SSN in Enron | Narrow (SSN) | **0.910** |
| **Pilán et al., 2022** — Legal, EUR Court | Legal EN | **0.733** |
| **Benchmark 2024** — General anonymization | General EN | **0.85** |
| **Alrazihi et al., 2025** — Neurosurgery UK | Clinical EN | **0.60** |
| **MathEd-PII, 2026** — Math tutoring | Educational EN | **0.379** |
| **PIIBench, 2026** — Multi-source | General | **0.139** |
| **SurrogateShield, 2026** — LLM queries | Technical EN | **0.891** |
| **→ This study (Carmen)** | **Clinical ES** | **0.239** (global) / **0.717** (detectable types) |

Presidio's F1 scores vary **dramatically** by domain and PII type:
- **Narrow tasks** (SSN, emails): **0.85–0.99**
- **General/legal EN texts**: **0.60–0.85**
- **Clinical EN** (Australia, UK): **0.60–0.90**
- **Multi-source benchmark**: **0.14**
- **Clinical ES** (Carmen): **0.24** (global), **0.72** (types Presidio can detect)

---

## 🚀 How to run

```bash
# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Presidio
pip install -e presidio-analyzer/
pip install -e presidio-anonymizer/
python3 -m spacy download es_core_news_md

# Evaluate (sample of 5 docs)
python3 scripts/evaluate_presidio_on_carmen.py --sample 5

# Evaluate (full dataset, 2000 docs)
python3 scripts/evaluate_presidio_on_carmen.py --full
```

The detailed report is generated in `evaluation_report.md`.

---

> **Note**: The Carmen dataset (`carmen/raw_data.json`) contains real clinical data with PII and is excluded from the repository via `.gitignore`.
| **Cross-Domain Transfer and Few-Shot Learning for PII Recognition, 2025** | TAB / Wikipedia / i2b2 | TAB **F1 0.649**; Wikipedia **0.642**; i2b2 **0.573**; mean **0.621** |
| **MathEd-PII, 2026** | Math tutoring | Presidio Large: P **0.254**, R **0.747**, **F1 0.379**. Presidio Transformer: P **0.230**, R **0.781**, **F1 0.355** |
| **PIIBench, 2026** | Multi-source PII benchmark | Presidio was the best baseline, but only **F1 0.1385** |
| **Identification and Anonymization… Social Engineering Detection, 2026** | OSINT / social engineering | Presidio NER: **F1 0.74** on a non-dedicated machine; **F1 0.79** on HPC |
| **SurrogateShield, 2026** | PII in LLM queries | Presidio comparable types: P **85.50%**, R **92.91%**, **F1 89.05%**. BERTScore F1 **0.8159** |
| **This study (Carmen, 2026)** | **Spanish clinical texts, 2000 docs** | **P 0.1588**, **R 0.4832**, **Jaccard 0.1357**, **F1 0.2390** |

### Interpretation of the comparison

Presidio's F1 scores vary **dramatically** by domain and PII type:

| Context | Observed F1 range |
|---|---|
| Narrow tasks (SSN, Enron emails) | **0.85 – 0.99** |
| General / legal texts in English | **0.60 – 0.85** |
| Clinical texts in English (Australia, UK) | **0.60 – 0.90** |
| Multi-source benchmark (PIIBench) | **0.14** |
| **Spanish clinical text (Carmen)** | **0.24** |

**Our result (F1 0.239)** sits in the low range, comparable to PIIBench (0.138), and far below the English-language clinical studies. This is explained by:

1. **Language**: spaCy's Spanish NER model produces more false positives than the English one in clinical context
2. **Entity complexity**: Carmen includes complex semantic entities (`PROFESION`, `FAMILIARES_SUJETO_ASISTENCIA`) that Presidio does not recognize
3. **Strict metric**: We use character-level overlap, not token-relaxed matching
4. **Presidio OOTB**: No threshold tuning, custom recognizers or fine-tuning

---

## Methodology

1. **Dataset**: Carmen-I (2000 Spanish clinical documents extracted from CARMEN-I with manual anonymization)
2. **Analysis**: Presidio Analyzer with the spaCy `es_core_news_md` model for Spanish
3. **Metric**: For each document, a binary character mask (1 = anonymized, 0 = not anonymized) is built both for the ground truth (extracting `[**TYPE**]` markers from the anonymized text and aligning them with the original) and for Presidio's prediction. **Jaccard**, Precision, Recall and F1 are then computed over these masks.
4. **Limitations**:
   - Character alignment between the original and the anonymized text may be imprecise due to differences in line breaks and whitespace
   - Presidio has no specific recognizers for all Carmen entity types (e.g. `PROFESION`, `FAMILIARES_SUJETO_ASISTENCIA`)
   - The analysis operates on general Spanish, not on specialized clinical vocabulary

---
