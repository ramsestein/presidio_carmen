# Informe de Evaluación: Presidio vs Dataset MEDDOCAN

**Fecha**: 2026-09-19 19:07
**Modelo**: spaCy `es_core_news_md` | **Umbral confianza**: 0.35 | **IoU**: ≥ 0.3
**Documentos evaluados**: 1000 (train + dev + test)

---

## Resumen Global (a nivel de carácter)

| Métrica | Valor |
|---------|-------|
| Caracteres GT anonimizados | 267,106 |
| Caracteres detectados por Presidio | 254,097 |
| Intersección (TP chars) | 165,977 |
| Unión (GT ∪ Pred) | 355,226 |
| Falsos Positivos (chars) | 88,120 |
| Falsos Negativos (chars) | 101,129 |
| Verdaderos Negativos (chars) | 2,532,743 |

### Métricas agregadas (acumuladas sobre todos los documentos)

| Métrica | Valor |
|---------|-------|
| **Jaccard** (global) | **0.4672** |
| **Precision** (global) | **0.6532** |
| **Recall** (global) | **0.6214** |
| **F1-Score** (global) | **0.6369** |
| **Specificity** (global) | **0.9664** |

### Métricas promedio por documento

| Métrica | Valor |
|---------|-------|
| Jaccard promedio | 0.4746 |
| Precision promedio | 0.6695 |
| Recall promedio | 0.6227 |
| F1 promedio | 0.6391 |

---

## Distribución de Jaccard por documento

| Rango Jaccard | Documentos | % |
|---------------|-----------|---|
| `1.0` | 0 | 0.0% |
| `0.8-1.0` | 0 | 0.0% |
| `0.6-0.8` | 59 | 5.9% |
| `0.4-0.6` | 757 | 75.7% |
| `0.2-0.4` | 182 | 18.2% |
| `0.0-0.2` | 2 | 0.2% |
| `0.0` | 0 | 0.0% |

---

## Métricas por Tipo de Entidad (MEDDOCAN, span-level, IoU ≥ 0.3)

| Tipo de Entidad | TP | FN | Precision | Recall | F1 |
|-----------------|----|----|-----------|--------|-----|
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
| **Total (todos)** | **11741** | **11054** | **1.0000** | **0.5151** | **0.6799** |
| **Total (solo F1>0)** | **11741** | **11053** | **1.0000** | **0.5151** | **0.6799** | *(excluye: ID_EMPLEO_PERSONAL_SANITARIO)*
| **Total (solo F1≥0.20)** | **11570** | **6493** | **1.0000** | **0.6405** | **0.7809** | *(excluye: EDAD_SUJETO_ASISTENCIA, FAMILIARES_SUJETO_ASISTENCIA, ID_ASEGURAMIENTO, ID_CONTACTO_ASISTENCIAL, ID_EMPLEO_PERSONAL_SANITARIO, ID_SUJETO_ASISTENCIA, NUMERO_TELEFONO, OTROS_SUJETO_ASISTENCIA, PROFESION)*
| **Total (solo F1≥0.60)** | **10554** | **3000** | **1.0000** | **0.7787** | **0.8756** | *(excluye: CALLE, EDAD_SUJETO_ASISTENCIA, FAMILIARES_SUJETO_ASISTENCIA, ID_ASEGURAMIENTO, ID_CONTACTO_ASISTENCIAL, ID_EMPLEO_PERSONAL_SANITARIO, ID_SUJETO_ASISTENCIA, ID_TITULACION_PERSONAL_SANITARIO, NUMERO_FAX, NUMERO_TELEFONO, OTROS_SUJETO_ASISTENCIA, PROFESION, SEXO_SUJETO_ASISTENCIA)*

### Falsos Positivos por tipo de entidad detectado por Presidio

| Tipo Presidio | Spans FP |
|---------------|----------|
| `LOCATION` | 5475 |
| `ORGANIZATION` | 2250 |
| `PERSON` | 1685 |
| `URL` | 1100 |
| `DATE_TIME` | 81 |
| `PHONE_NUMBER` | 14 |
| `EMAIL_ADDRESS` | 3 |

---

## Distribución de tipos de entidad en el dataset

| Tipo de Entidad (MEDDOCAN) | Frecuencia |
|--------------------------|-----------|
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

## Comparativa con otros estudios

| Estudio / Fuente | Dominio | Resultado Presidio |
|---|---|---|
| **Kotevski et al., 2022** | Oncología radioterápica, Australia, 300 docs | F1 strict **0.8471**; F1 relaxed **0.8980** |
| **Pilán et al., 2022** | Legal / European Court HR | F1 ≈ **0.733** |
| **Alrazihi et al., 2025** | Notas neuroquirúrgicas, UK, 200 docs | F1 **0.60** |
| **PIIBench, 2026** | Benchmark multi-fuente PII | F1 **0.1385** |
| **Este estudio (Carmen, 2026)** | Textos clínicos español, 2000 docs | F1 global **0.239** / tipos detectables **0.717** |
| **Este estudio (MEDDOCAN)** | Textos clínicos español, 1000 docs | F1 global **0.6369** |

---

## Estadísticas por Documento

| Estadística | Valor |
|-------------|-------|
| Promedio spans GT por doc | 22.8 |
| Promedio detecciones por doc | 22.3 |
| Tiempo total | 186.3s |
| Promedio por documento | 0.186s |
| Documentos con Jaccard > 0 | 1000 |
| Documentos sin entidades GT | 0 |

---

## Metodología

1. **Dataset**: MEDDOCAN (1000 informes clínicos en español; 1.000 casos de SPACCC con PHI anotado manualmente).
2. **Ground truth**: spans BRAT exactos (`meddocan/gt_spans.json`) convertidos desde `meddocan/corpus/{train,dev,test}/brat/*.ann`.
3. **Análisis**: Presidio Analyzer con spaCy `es_core_news_md`, out-of-the-box (misma configuración que Carmen).
4. **Métrica**: máscara binaria de caracteres (1 = anonimizado) → Jaccard, Precision, Recall, F1; y métricas a nivel de span por tipo con IoU ≥ 0.3.
5. **Limitaciones**: Presidio no tiene recognizers para muchos tipos MEDDOCAN (PROFESION, FAMILIARES_SUJETO_ASISTENCIA, EDAD, etc.); opera sobre español general, no clínico.

---
