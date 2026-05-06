# Índice de Vulnerabilidad Socioterritorial ante Inundaciones — Campeche, México

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0003--2104--6625-brightgreen.svg)](https://orcid.org/0000-0003-2104-6625)

## Descripción

Repositorio de código asociado al artículo:

> Chin Canché, G. A., Pan Barcel, J. y Ruiz Canul, K. (2026). Índice de
> Vulnerabilidad Socioterritorial ante Inundaciones en los municipios de
> Campeche, México. *Impluvium*, No. 35. Universidad Nacional Autónoma de
> México (UNAM). https://www.agua.unam.mx/impluvium.html (Pendiente de publicación)

El estudio construye un índice compuesto de vulnerabilidad ante inundaciones
para los 12 municipios del estado de Campeche, México, integrando cuatro
dimensiones analíticas: Sensibilidad Social (SS), Exposición Física (EF),
Capacidad Adaptativa (CA) y Grupos Vulnerables (GV), con base en el Censo
de Población y Vivienda 2020 (INEGI) y el Índice de Marginación por
Localidad 2020 (CONAPO). El marco conceptual se sustenta en el enfoque del
IPCC AR5 (2014) y el Marco de Sendai para la Reducción del Riesgo de
Desastres 2015–2030.

---

## Autores

### Autor de correspondencia

**Guillermo Adrián Chin Canché**
Instituto Tecnológico Superior de Calkiní (ITESCAM),
Tecnológico Nacional de México — Campeche, México
ORCID: [0000-0003-2104-6625](https://orcid.org/0000-0003-2104-6625)
Contacto y más información: [linktr.ee/guille_chin](https://linktr.ee/guille_chin)
✉️ contacto@guillermochin.com

### Coautores

- **Javier Pan Barcel** — Universidad Autónoma de Campeche, EPOMEX
- **Katia Ruiz Canul** — Instituto Tecnológico Superior de Calkiní (ITESCAM)

---

## Marco conceptual del índice

El Índice de Vulnerabilidad Socioterritorial (IVS) se calcula como:

IVS = SS×0.30 + EF×0.25 + CA×0.25 + GV×0.20

| Dimensión | Código | Peso | Justificación |
|---|---|---|---|
| Sensibilidad Social | SS | 0.30 | Cutter et al. (2003) |
| Exposición Física | EF | 0.25 | IPCC AR5 (2014) |
| Capacidad Adaptativa | CA | 0.25 | IPCC AR5 (2014) |
| Grupos Vulnerables | GV | 0.20 | Wisner et al. (2004) |

Las variables de Capacidad Adaptativa se normalizan de forma inversa
(mayor valor = menor vulnerabilidad).

## Estructura del repositorio

```
Proyecto_Vulnerabilidad_Inundaciones_Campeche/
│
├── 01_datos_crudos/               # Datos originales sin modificar (solo lectura)
│   ├── iter_04_cpv2020_csv/       # ITER Censo 2020 Campeche (INEGI)
│   ├── IML_2020/                  # Índice de Marginación por Localidad 2020 (CONAPO)
│   ├── 2025_1_04_MUN/             # Shapefile municipios Campeche (Marco Geoestadístico INEGI)
│   └── 04_campeche/               # Shapefiles adicionales Campeche (INEGI)
│
├── 02_datos_procesados/           # Datos limpios y transformados (output de scripts)
│
├── 03_analisis/
│   ├── notebooks/                 # Jupyter Notebooks por etapa de análisis
│  #└── scripts/                   # Scripts Python de soporte
│
├── 04_outputs/
│   ├── figuras/                   # Gráficas y visualizaciones (.png, 150+ dpi)
│   ├── tablas/                    # Tablas de resultados (.csv, .xlsx)
│  #└── mapas/                     # Mapas coropléticos (.png, .html)
│
├── 05_manuscrito/                 # Borrador del artículo (Word, no versionado en Git)
│
├── requirements.txt               # Dependencias Python
├── CITATION.cff                   # Metadatos de citación (Zenodo/GitHub)
├── LICENSE                        # Licencia CC BY 4.0
└── README.md                      # Este archivo
```

## Fuentes de datos

| Dataset | Fuente | Año | Licencia | URL |
|---|---|---|---|---|
| ITER Censo de Población y Vivienda — Campeche | INEGI | 2020 | Datos abiertos | https://www.inegi.org.mx/programas/ccpv/2020/ |
| Índice de Marginación por Localidad | CONAPO | 2020 | Datos abiertos | https://www.gob.mx/conapo/documentos/indices-de-marginacion-2020-284372 |
| Marco Geoestadístico Nacional — Municipios | INEGI | 2025 | Datos abiertos | https://www.inegi.org.mx/temas/mg/ |
| Natural Earth — Polígonos de tierra 1:10m | Natural Earth | 2024 | Dominio público | https://www.naturalearthdata.com |

> **Nota metodológica sobre Dzitbalché:** El municipio de Dzitbalché fue
> creado recientemente por segregación del municipio de Calkiní. El Censo
> 2020 (INEGI) y el IML 2020 (CONAPO) no lo registran como municipio
> independiente, por lo que sus datos se encuentran integrados en los
> valores de Calkiní. Esta limitación se discute en el apartado de
> consideraciones metodológicas del artículo.

> **Nota sobre datos crudos:** Los datos originales no se versionan en
> GitHub. Se archivan en Zenodo junto con los datos procesados.
> Solo el código de análisis está versionado en este repositorio.

## Instalación y reproducibilidad

```bash
# 1. Clonar el repositorio
git clone https://github.com/guillermochin/Proyecto_Vulnerabilidad_Inundaciones_Campeche.git
cd Proyecto_Vulnerabilidad_Inundaciones_Campeche

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Colocar los datos crudos en 01_datos_crudos/
#    (descargar desde las fuentes indicadas o desde Zenodo)

# 5. Ejecutar el pipeline completo
python 03_analisis/scripts/pipeline.py

# 6. O ejecutar desde un paso específico
python 03_analisis/scripts/pipeline.py --desde 3

# 7. Generar mapas interpolados (independiente del pipeline)
python 03_analisis/scripts/08_mapa_interpolado.py
```

## Outputs generados

| Archivo | Descripción |
|---|---|
| `fig01_ranking_ivs.png` | Ranking de municipios por IVS |
| `fig02_dimensiones_barras.png` | Comparación de dimensiones SS y EF |
| `fig03_heatmap_variables.png` | Heatmap de variables normalizadas |
| `fig04_mapa_cloropletico.png` | Mapa coroplético municipal del IVS |
| `fig05_mapa_interpolado.png` | Superficie continua IDW — IVS |
| `fig06_mapa_dim_ss.png` | Superficie continua IDW — Sensibilidad Social |
| `fig07_mapa_dim_ef.png` | Superficie continua IDW — Exposición Física |
| `fig08_mapa_dim_ca.png` | Superficie continua IDW — Capacidad Adaptativa |
| `fig09_mapa_dim_gv.png` | Superficie continua IDW — Grupos Vulnerables |
| `fig10_mapa_dimension_dominante.png` | Dimensión de mayor vulnerabilidad por zona |
| `fig11_panel_comparativo.png` | Panel comparativo 2×3: municipal + IDW |
| `tabla_ranking_ivs.csv` | Tabla de resultados para el artículo |
| `reporte_completo_ivs.txt` | Reporte exhaustivo de todos los cálculos |
| `metadatos_figuras.txt` | Títulos, pies y notas editoriales de figuras |
| `log_pipeline.txt` | Registro de ejecución del pipeline |

---

## Licencia

Este repositorio se distribuye bajo la licencia
[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

Puedes compartir y adaptar el material para cualquier propósito,
siempre que se otorgue el crédito apropiado.

## Uso de inteligencia artificial

Se empleó Claude (Anthropic) como apoyo para la corrección y comentado del código a modo de que sea más facil de seguir la lógica de la programación. 

## Citación (Revisa si ya se publicó el artículo)

Si utilizas este código o datos en tu investigación, por favor cita:

```bibtex
@article{chincanche2026ivs,
  author  = {Chin Canché, Guillermo Adrián and Pan Barcel, Javier
             and Ruiz Canul, Katia},
  title   = {Índice de Vulnerabilidad Socioterritorial ante Inundaciones
             en los municipios de Campeche, México},
  journal = {Impluvium},
  number  = {35},
  year    = {2026},
  url     = {https://www.agua.unam.mx/impluvium.html}
}
```

---

*Guillermo Adrián Chin Canché — ITESCAM, Campeche, México*
*[linktr.ee/guille_chin](https://linktr.ee/guille_chin)*
