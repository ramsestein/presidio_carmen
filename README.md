# Presidio Carmen

Evaluación de **Presidio Analyzer** (Microsoft) contra el dataset **Carmen** — 2000 documentos clínicos en español con anonimización manual.

---

## ⚙️ Configuración

| Parámetro | Valor |
|---|---|
| Presidio | v2.2.363 (out-of-the-box, sin modificar) |
| Modelo NLP | spaCy `es_core_news_md` |
| Idioma | Español (`es`) |
| Dataset | Carmen-I, 2000 documentos clínicos |
| Tipos de entidad | 18 (FECHAS, HOSPITAL, PERSONA, etc.) |
| Hardware | CPU |
| **Tiempo total** | **120.8s** (~0.06s/doc) |

---

## 📊 Resumen Global (máscara de caracteres)

| Métrica | Valor |
|---|---|
| **Jaccard** | **0.1113** |
| **Precision** | **0.1258** |
| **Recall** | **0.4920** |
| **F1-Score** | **0.2003** |
| Specificity | 0.9372 |
| TP chars | 26,757 |
| FP chars | 186,021 |
| FN chars | 27,628 |

### Distribución de Jaccard por documento

| Rango | Docs | % |
|---|---|---|
| 1.0 | 21 | 1.1% |
| 0.8–1.0 | 7 | 0.4% |
| 0.6–0.8 | 44 | 2.2% |
| 0.4–0.6 | 80 | 4.0% |
| 0.2–0.4 | 256 | 12.8% |
| 0.0–0.2 | 735 | 36.8% |
| 0.0 | 857 | 42.9% |

---

## 📈 Métricas por Tipo de Entidad (span-level, IoU ≥ 0.3)

| Tipo Carmen | TP | FN | Recall | F1 |
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

### Totales con filtros

| Filtro | TP | FN | Recall | F1 | Excluye |
|---|---|---|---|---|---|
| **Todos** | 2,828 | 3,705 | 0.433 | **0.604** | — |
| Solo F1 > 0 | 2,828 | 3,690 | 0.434 | **0.605** | NUMERO_TELEFONO |
| Solo F1 ≥ 0.20 | 2,782 | 2,609 | **0.516** | **0.681** | 4 tipos no detectables |
| Solo F1 ≥ 0.60 | 2,633 | 2,080 | **0.559** | **0.717** | 7 tipos con peor F1 |

### Falsos Positivos por tipo Presidio

| Tipo Presidio | Spans FP |
|---|---|
| `ORGANIZATION` | 8,560 |
| `LOCATION` | 6,910 |
| `PERSON` | 5,571 |
| `DATE_TIME` | 900 |
| `URL` | 233 |
| `PHONE_NUMBER` | 46 |
| `IP_ADDRESS` | 1 |

---

## 🧠 Interpretación

### ✅ Lo que Presidio detecta bien (F1 > 0.80)
| Tipo | ¿Cómo? |
|---|---|
| **HOSPITAL, CENTRO_SALUD, INSTITUCION** | NER ORGANIZATION |
| **PAIS, CALLE, TERRITORIO** | NER LOCATION/GPE |
| **NOMBRE_PERSONAL_SANITARIO** | NER PERSON |

### ⚠️ Detección parcial
| Tipo | Problema |
|---|---|
| **FECHAS** (F1 0.66) | Detecta formatos `dd/mm/aa` pero no fechas en texto libre |
| **ID_SUJETO_ASISTENCIA** (F1 0.73) | Detecta algunos como PERSON |

### ❌ No detectado
| Tipo | Motivo |
|---|---|
| **PROFESION, FAMILIARES** | Entidades semánticas sin recognizer |
| **EDAD** | No hay recognizer de edad en Presidio |
| **NUMERO_TELEFONO** (F1 0.0) | Regex no cubre formato español |
| **NUMERO_IDENTIF** (F1 0.20) | ES_NIF/ES_NIE cubren parcialmente |

---

## ⏱ Rendimiento

| Medición | Valor |
|---|---|
| Documentos procesados | 2,000 |
| Tiempo total | **120.8 segundos** |
| Promedio por documento | **0.060 segundos** |
| Spans GT totales | 8,227 |
| Detecciones Presidio totales | 25,049 |
| Promedio spans GT por doc | 4.1 |
| Promedio detecciones por doc | 12.5 |
| Docs sin entidades GT | 461 (23%) |

---

## 🔬 Comparativa con otros estudios

| Estudio | Dominio | F1 Presidio |
|---|---|---|
| **Kotevski et al., 2022** — Oncología, Australia | Clínico EN | **0.847 / 0.898** (strict/relaxed) |
| **Friebely, 2022** — SSN en Enron | Estrecho (SSN) | **0.910** |
| **Pilán et al., 2022** — Legal, EUR Court | Legal EN | **0.733** |
| **Benchmark 2024** — General anonimización | General EN | **0.85** |
| **Alrazihi et al., 2025** — Neurocirugía UK | Clínico EN | **0.60** |
| **MathEd-PII, 2026** — Tutoring matemático | Educativo EN | **0.379** |
| **PIIBench, 2026** — Multi-fuente | General | **0.139** |
| **SurrogateShield, 2026** — LLM queries | Técnico EN | **0.891** |
| **→ Este estudio (Carmen)** | **Clínico ES** | **0.239** (global) / **0.717** (tipos detectables) |

Los F1 de Presidio varían **brutalmente** según dominio y tipo de PII:
- **Tareas estrechas** (SSN, emails): **0.85–0.99**
- **Textos generales/legales EN**: **0.60–0.85**
- **Clínico EN** (Australia, UK): **0.60–0.90**
- **Benchmark multi-fuente**: **0.14**
- **Clínico ES** (Carmen): **0.24** (global), **0.72** (tipos que Presidio puede detectar)

---

## 🚀 Cómo ejecutar

```bash
# Entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar Presidio
pip install -e presidio-analyzer/
pip install -e presidio-anonymizer/
python3 -m spacy download es_core_news_md

# Evaluar (sample de 5 docs)
python3 scripts/evaluate_presidio_on_carmen.py --sample 5

# Evaluar (dataset completo, 2000 docs)
python3 scripts/evaluate_presidio_on_carmen.py --full
```

El reporte detallado se genera en `evaluation_report.md`.

---

> **Nota**: El dataset Carmen (`carmen/raw_data.json`) contiene datos clínicos reales con PII y está excluido del repositorio vía `.gitignore`.
| **Cross-Domain Transfer and Few-Shot Learning for PII Recognition, 2025** | TAB / Wikipedia / i2b2 | TAB **F1 0.649**; Wikipedia **0.642**; i2b2 **0.573**; media **0.621** |
| **MathEd-PII, 2026** | Tutoring matemático | Presidio Large: P **0.254**, R **0.747**, **F1 0.379**. Presidio Transformer: P **0.230**, R **0.781**, **F1 0.355** |
| **PIIBench, 2026** | Benchmark multi-fuente PII | Presidio fue el mejor baseline, pero solo **F1 0.1385** |
| **Identification and Anonymization… Social Engineering Detection, 2026** | OSINT / social engineering | Presidio NER: **F1 0.74** en máquina no dedicada; **F1 0.79** en HPC |
| **SurrogateShield, 2026** | PII en queries LLM | Presidio comparable types: P **85.50%**, R **92.91%**, **F1 89.05%**. BERTScore F1 **0.8159** |
| **Este estudio (Carmen, 2026)** | **Textos clínicos español, 2000 docs** | **P 0.1588**, **R 0.4832**, **Jaccard 0.1357**, **F1 0.2390** |

### Interpretación de la comparativa

Los F1 de Presidio varían **brutalmente** según el dominio y el tipo de PII:

| Contexto | Rango F1 observado |
|---|---|
| Tareas estrechas (SSN, emails Enron) | **0.85 – 0.99** |
| Textos generales / legales en inglés | **0.60 – 0.85** |
| Textos clínicos en inglés (Australia, UK) | **0.60 – 0.90** |
| Benchmark multi-fuente (PIIBench) | **0.14** |
| **Texto clínico español (Carmen)** | **0.24** |

**Nuestro resultado (F1 0.239)** está en el rango bajo, comparable a PIIBench (0.138), y muy por debajo de los estudios clínicos en inglés. Esto se explica por:

1. **Idioma**: El modelo NER de spaCy para español tiene más falsos positivos que el de inglés en contexto clínico
2. **Complejidad de entidades**: Carmen incluye entidades semánticas complejas (`PROFESION`, `FAMILIARES_SUJETO_ASISTENCIA`) que Presidio no reconoce
3. **Métrica estricta**: Usamos solapamiento de caracteres, no relajado por token
4. **Presidio OOTB**: Sin ajuste de thresholds, recognizers personalizados ni fine-tuning

---

## Metodología

1. **Dataset**: Carmen-I (2000 documentos clínicos en español extraídos de CARMEN-I con anonimización manual)
2. **Análisis**: Presidio Analyzer con modelo spaCy `es_core_news_md` para español
3. **Métrica**: Para cada documento se construye una máscara binaria de caracteres (1 = anonimizado, 0 = no anonimizado) tanto para el ground truth (extrayendo marcadores `[**TYPE**]` del texto anonimizado y alineándolos con el original) como para la predicción de Presidio. Luego se calcula **Jaccard**, Precision, Recall y F1 sobre estas máscaras.
4. **Limitaciones**:
   - La alineación de caracteres entre original y texto anonimizado puede tener imprecisiones debido a diferencias en saltos de línea y espacios
   - Presidio no tiene recognizers específicos para todos los tipos de entidad de Carmen (ej. `PROFESION`, `FAMILIARES_SUJETO_ASISTENCIA`)
   - El análisis opera sobre español general, no sobre vocabulario clínico especializado

---
