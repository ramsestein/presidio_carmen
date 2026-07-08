# Informe de Evaluación: Presidio vs Dataset Carmen

**Fecha**: 2026-07-08 22:01
**Modelo**: spaCy `es_core_news_md` | **Umbral confianza**: 0.35
**Documentos evaluados**: 2000

---

## Resumen Global (a nivel de carácter)

| Métrica | Valor |
|---------|-------|
| Caracteres GT anonimizados | 69,912 |
| Caracteres detectados por Presidio | 212,778 |
| Intersección (TP chars) | 33,782 |
| Unión (GT ∪ Pred) | 248,908 |
| Falsos Positivos (chars) | 178,996 |
| Falsos Negativos (chars) | 36,130 |
| Verdaderos Negativos (chars) | 2,767,216 |

### Métricas agregadas (acumuladas sobre todos los documentos)

| Métrica | Valor |
|---------|-------|
| **Jaccard** (global) | **0.1357** |
| **Precision** (global) | **0.1588** |
| **Recall** (global) | **0.4832** |
| **F1-Score** (global) | **0.2390** |
| **Specificity** (global) | **0.9392** |

### Métricas promedio por documento

| Métrica | Valor |
|---------|-------|
| Jaccard promedio | 0.1377 |
| Precision promedio | 0.1518 |
| Recall promedio | 0.3696 |
| F1 promedio | 0.1909 |

---

## Distribución de Jaccard por documento

| Rango Jaccard | Documentos | % |
|---------------|-----------|---|
| `1.0` | 21 | 1.1% |
| `0.8-1.0` | 19 | 0.9% |
| `0.6-0.8` | 45 | 2.2% |
| `0.4-0.6` | 114 | 5.7% |
| `0.2-0.4` | 317 | 15.8% |
| `0.0-0.2` | 652 | 32.6% |
| `0.0` | 832 | 41.6% |

---

## Distribución de tipos de entidad en el dataset

| Tipo de Entidad (Carmen) | Frecuencia |
|--------------------------|-----------|
| `FECHAS` | 5382 |
| `EDAD_SUJETO_ASISTENCIA` | 815 |
| `SEXO_SUJETO_ASISTENCIA` | 458 |
| `HOSPITAL` | 316 |
| `FAMILIARES_SUJETO_ASISTENCIA` | 299 |
| `NUMERO_IDENTIF` | 227 |
| `NOMBRE_PERSONAL_SANITARIO` | 151 |
| `INSTITUCION` | 129 |
| `PAIS` | 118 |
| `PROFESION` | 91 |
| `TERRITORIO` | 90 |
| `CENTRO_SALUD` | 52 |
| `OTROS_SUJETO_ASISTENCIA` | 38 |
| `NUMERO_TELEFONO` | 22 |
| `CALLE` | 22 |
| `ID_SUJETO_ASISTENCIA` | 14 |
| `ID_CONTACTO_ASISTENCIAL` | 2 |
| `URL_WEB` | 1 |

## Estadísticas por Documento

| Estadística | Valor |
|-------------|-------|
| Promedio spans GT por doc | 4.1 |
| Promedio detecciones por doc | 12.5 |
| Tiempo total | 73.4s |
| Promedio por documento | 0.037s |
| Documentos con Jaccard > 0 | 1168 |
| Documentos sin entidades GT | 461 |

---

## Comparativa con otros estudios publicados

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
