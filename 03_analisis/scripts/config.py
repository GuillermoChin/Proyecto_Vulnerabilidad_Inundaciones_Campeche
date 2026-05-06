# =============================================================================
# config.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Archivo central de configuración del proyecto.
#   Define todas las rutas, parámetros y constantes globales.
#   TODOS los demás scripts importan desde aquí — no hardcodear rutas nunca.
# =============================================================================

from pathlib import Path

# ── Raíz del proyecto ─────────────────────────────────────────────────────────
# Sube 3 niveles desde 03_analisis/scripts/ hasta la raíz del proyecto
ROOT = Path(__file__).resolve().parents[2]

# ── Directorios principales ───────────────────────────────────────────────────
DIR_CRUDOS      = ROOT / "01_datos_crudos"
DIR_PROCESADOS  = ROOT / "02_datos_procesados"
DIR_FIGURAS     = ROOT / "04_outputs" / "figuras"
DIR_TABLAS      = ROOT / "04_outputs" / "tablas"
DIR_MAPAS       = ROOT / "04_outputs" / "mapas"

# ── Archivos de entrada ───────────────────────────────────────────────────────
ITER_CSV = (
    DIR_CRUDOS
    / "iter_04_cpv2020_csv"
    / "conjunto_de_datos"
    / "conjunto_de_datos_iter_04CSV20.csv"
)

IML_XLS = DIR_CRUDOS / "IML_2020" / "IML_2020.xls"

SHP_MUN = DIR_CRUDOS / "2025_1_04_MUN" / "2025_1_04_MUN.shp"

# ── Archivos de salida ────────────────────────────────────────────────────────
ITER_LIMPIO   = DIR_PROCESADOS / "iter_municipal_limpio.csv"
IML_LIMPIO    = DIR_PROCESADOS / "iml_campeche_municipal.csv"
DATOS_MERGED  = DIR_PROCESADOS / "campeche_municipios_merged.csv"
DATOS_INDICE  = DIR_PROCESADOS / "campeche_indice_final.csv"

# ── Parámetros del análisis ───────────────────────────────────────────────────
CLAVE_ENTIDAD  = "04"       # Clave INEGI del estado de Campeche
NUM_MUNICIPIOS = 13         # Total de municipios en Campeche

# Etiquetas de los 5 niveles del índice (de mayor a menor vulnerabilidad)
NIVELES_INDICE = ["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"]

# Variables del ITER que entran al índice
# Dirección: "positiva" = más valor → más vulnerable
#            "inversa"  = más valor → menos vulnerable (se invierte al normalizar)
VARIABLES_INDICE = {
    # --- Dimensión 1: Sensibilidad Social (SS) ---
    "SS1": {"col": "P15YM_AN",   "dir": "positiva"},
    "SS2": {"col": "VPH_AGUAFV", "dir": "positiva"},
    "SS3": {"col": "VPH_NODREN", "dir": "positiva"},
    "SS4": {"col": "VPH_PISODT", "dir": "positiva"},
    "SS5": {"col": "PSINDER",    "dir": "positiva"},
    # --- Dimensión 2: Exposición Física (EF) ---
    "EF1": {"col": "POBTOT",     "dir": "positiva"},
    "EF2": {"col": "VPH_C_ELEC", "dir": "positiva"},
    "EF3": {"col": "VPH_SNBIEN", "dir": "positiva"},
    # --- Dimensión 3: Capacidad Adaptativa (CA) ---
    "CA1": {"col": "GRAPROES",   "dir": "inversa"},
    "CA2": {"col": "P18YM_PB",   "dir": "inversa"},
    "CA3": {"col": "PDER_IMSS",  "dir": "inversa"},
    "CA4": {"col": "POCUPADA",   "dir": "inversa"},
    # --- Dimensión 4: Grupos Vulnerables (GV) ---
    "GV1": {"col": "P60YMAS",    "dir": "positiva"},
    "GV2": {"col": "POB0_14",    "dir": "positiva"},
    "GV3": {"col": "P3YM_HLI",   "dir": "positiva"},
    "GV4": {"col": "PCON_DISC",  "dir": "positiva"},
}

# ── Pesos de dimensiones (justificados en IPCC AR5 + Cutter 2003) ─────────────
# Suma = 1.0
# SS=0.30 — Cutter et al. (2003) Social Vulnerability Index
# EF=0.25 — IPCC AR5 (2014) exposure component
# CA=0.25 — IPCC AR5 (2014) adaptive capacity component
# GV=0.20 — Wisner et al. (2004) "At Risk" framework
PESOS_DIMENSIONES = {
    "SS": 0.30,
    "EF": 0.25,
    "CA": 0.25,
    "GV": 0.20,
}
# ── Columnas de variables (extraídas del diccionario para uso en scripts) ─────
COLS_VARIABLES = [v["col"] for v in VARIABLES_INDICE.values()]

# ── Variables con normalización inversa ───────────────────────────────────────
VARS_INVERSAS = [k for k, v in VARIABLES_INDICE.items()
                 if v["dir"] == "inversa"]

# ── Parámetros de visualización ───────────────────────────────────────────────
DPI_FIGURAS    = 300        # Resolución de figuras para publicación
FORMATO_FIG    = "png"      # Formato de salida de figuras
PALETA_COLORES = "YlOrRd"   # Paleta para mapas coropléticos (amarillo-rojo)

# ── Verificación de rutas al importar ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Verificación de rutas del proyecto ===\n")
    rutas = {
        "Raíz del proyecto": ROOT,
        "Datos crudos":      DIR_CRUDOS,
        "Datos procesados":  DIR_PROCESADOS,
        "Figuras":           DIR_FIGURAS,
        "Tablas":            DIR_TABLAS,
        "Mapas":             DIR_MAPAS,
    }
    for nombre, ruta in rutas.items():
        estado = "✓" if ruta.exists() else "✗ NO EXISTE"
        print(f"  {estado}  {nombre}: {ruta}")

    print("\n=== Archivos de entrada ===\n")
    archivos = {
        "ITER CSV":  ITER_CSV,
        "IML XLS":   IML_XLS,
        "Shapefile": SHP_MUN,
    }
    for nombre, archivo in archivos.items():
        estado = "✓" if archivo.exists() else "✗ NO EXISTE"
        print(f"  {estado}  {nombre}: {archivo.name}")
