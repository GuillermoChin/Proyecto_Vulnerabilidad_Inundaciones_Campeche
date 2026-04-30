# Índice de Vulnerabilidad Socioterritorial ante Inundaciones — Campeche, México

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

## Descripción

Repositorio de código y datos procesados asociado al artículo:

> Chin Canché, G. A., Pan Barcel, J. y [Apellido Katia], [Nombre Katia] (2026). Índice de Vulnerabilidad Socioterritorial ante Inundaciones en los municipios de Campeche, México. *Impluvium*, No. 35. Universidad Nacional Autónoma de México (UNAM). https://www.agua.unam.mx/impluvium.html

El estudio construye un índice compuesto de vulnerabilidad ante inundaciones para los 13 municipios del estado de Campeche, México, a partir de variables sociales, demográficas y de condición de vivienda del Censo de Población y Vivienda 2020 (INEGI) y el Índice de Marginación Municipal 2020 (CONAPO).

## Autores

| Autor | Institución | ORCID |
|---|---|---|
| Guillermo Adrián Chin Canché | Instituto Tecnológico Superior de Calkiní (ITESCAM), Tecnológico Nacional de México | [0000-XXXX-XXXX-XXXX](https://orcid.org/0000-XXXX-XXXX-XXXX) |
| Javier Pan Barcel | Universidad Autónoma de Campeche — EPOMEX | [0000-XXXX-XXXX-XXXX](https://orcid.org/0000-XXXX-XXXX-XXXX) |
| [Nombre Katia] [Apellido Katia] | [Institución Katia] | [0000-XXXX-XXXX-XXXX](https://orcid.org/0000-XXXX-XXXX-XXXX) |

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

> **Nota:** Los datos crudos no se modifican en ninguna etapa del análisis. Todo procesamiento parte de los archivos en `01_datos_crudos/` y escribe resultados en `02_datos_procesados/`.

## Instalación y reproducibilidad

```bash
# 1. Clonar el repositorio
git clone https://github.com/[usuario]/Proyecto_Vulnerabilidad_Inundaciones_Campeche.git
cd Proyecto_Vulnerabilidad_Inundaciones_Campeche

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar notebooks en orden
#    03_analisis/notebooks/01_limpieza_datos.ipynb
#    03_analisis/notebooks/02_construccion_indice.ipynb
#    03_analisis/notebooks/03_visualizacion.ipynb
```

## Licencia

Este repositorio se distribuye bajo la licencia [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

Puedes compartir y adaptar el material para cualquier propósito, siempre que se otorgue el crédito apropiado.

## Uso de inteligencia artificial

En la elaboración del código de análisis y la redacción del manuscrito se empleó Claude (Anthropic) como apoyo en organización del código, revisión de estilo y redacción. La responsabilidad total del contenido, los argumentos, los datos y las conclusiones recae exclusivamente en los autores.

## Contacto

Guillermo Adrián Chin Canché — contacto@guillermochin.com — ITESCAM, Campeche, México
