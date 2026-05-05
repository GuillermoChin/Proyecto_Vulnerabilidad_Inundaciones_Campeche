# =============================================================================
# config.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
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
# VS = Vulnerabilidad Social | EF = Exposición Física
VARIABLES_INDICE = {
    # --- Dimensión 1: Vulnerabilidad Social (VS) ---
    "VS1": "P15YM_AN",    # % población analfabeta > 15 años
    "VS2": "VPH_AGUAFV",  # % viviendas sin agua entubada
    "VS3": "VPH_NODREN",  # % viviendas sin drenaje
    "VS4": "VPH_PISODT",  # % viviendas con piso de tierra
    "VS5": "PSINDER",     # % población sin derechohabiencia a salud
    # --- Dimensión 2: Exposición Física (EF) ---
    "EF1": "POBTOT",      # Densidad de población (se calculará con área)
    "EF2": "VPH_C_ELEC",  # % viviendas sin electricidad (proxy precariedad)
    "EF3": "VPH_SNBIEN",   # % viviendas sin ningún bien (proxy precariedad física)
}

# Pesos de cada dimensión en el índice compuesto (deben sumar 1.0)
PESOS_DIMENSIONES = {
    "VS": 0.6,   # Vulnerabilidad Social tiene mayor peso
    "EF": 0.4,   # Exposición Física
}

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
