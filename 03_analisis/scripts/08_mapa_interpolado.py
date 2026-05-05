# =============================================================================
# 08_mapa_interpolado.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Genera un mapa de superficie continua de vulnerabilidad mediante
#   interpolación espacial IDW (Inverse Distance Weighting) a partir
#   de los valores calculados por localidad del ITER Censo 2020.
#
#   El proceso es:
#     1. Cargar ITER completo (todas las localidades, no solo municipios)
#     2. Calcular un IVS aproximado por localidad con las variables
#        disponibles a ese nivel
#     3. Aplicar IDW para generar una grilla continua sobre Campeche
#     4. Recortar la superficie al límite estatal
#     5. Exportar el mapa como PNG de alta resolución
#
#   Entrada:  01_datos_crudos/iter_04_cpv2020_csv/.../conjunto_de_datos_iter_04CSV20.csv
#             01_datos_crudos/2025_1_04_MUN/2025_1_04_MUN.shp
#   Salida:   04_outputs/mapas/fig05_mapa_interpolado.png
# =============================================================================

import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.family"] = "DejaVu Sans"

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from config import (
    ITER_CSV,
    SHP_MUN,
    DIR_MAPAS,
    DPI_FIGURAS,
    FORMATO_FIG,
)

# ── Parámetros de interpolación ───────────────────────────────────────────────
IDW_POTENCIA   = 2       # Potencia del IDW (2 es estándar)
IDW_VECINOS    = 8       # Número de vecinos para el IDW
GRID_RESOLUCION = 200    # Puntos por lado de la grilla (200×200)

# ── Variables para IVS a nivel localidad ─────────────────────────────────────
# Subconjunto de variables disponibles en el ITER a nivel localidad
# (no todas las variables municipales existen a nivel localidad)
VARS_LOCALIDAD_VS = ["P15YM_AN", "VPH_AGUAFV", "VPH_NODREN",
                     "VPH_PISODT", "PSINDER"]
VARS_LOCALIDAD_EF = ["POBTOT", "VPH_C_ELEC", "VPH_SNBIEN"]

PESO_VS = 0.6
PESO_EF = 0.4

# ── Tamaños de fuente ─────────────────────────────────────────────────────────
FS_TITULO = 15
FS_EJE    = 12
FS_TICK   = 11


# =============================================================================
# CARGA Y PREPARACIÓN DE DATOS
# =============================================================================

def cargar_iter_localidades() -> pd.DataFrame:
    """
    Carga el ITER completo y filtra únicamente las localidades
    con población > 0, coordenadas válidas y que NO sean
    totales municipales (LOC != 0000).
    """
    print(f"  Cargando ITER completo: {ITER_CSV.name}")
    df = pd.read_csv(
        ITER_CSV,
        encoding="utf-8-sig",
        dtype=str,
        low_memory=False,
    )
    df.columns = [c.replace("ï»¿", "").strip() for c in df.columns]

    # Filtrar: solo localidades (no totales municipales ni estatales)
    df = df[
        (df["MUN"] != "000") &
        (df["LOC"] != "0000") &
        (df["LOC"] != "000")
    ].copy()

    # Convertir coordenadas y población a numérico
    for col in ["LONGITUD", "LATITUD", "POBTOT", "TVIVHAB"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Filtrar localidades con coordenadas válidas y población > 0
    df = df.dropna(subset=["LONGITUD", "LATITUD"])
    df = df[df["POBTOT"] > 0]

    # Corregir longitudes negativas si es necesario
    # (INEGI a veces reporta longitudes positivas para México)
    if df["LONGITUD"].mean() > 0:
        df["LONGITUD"] = -df["LONGITUD"]

    print(f"  Localidades con coordenadas válidas: {len(df):,}")
    return df


def calcular_ivs_localidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula un IVS aproximado para cada localidad usando las variables
    disponibles en el ITER a nivel de localidad.

    Las variables absolutas se convierten a proporciones antes de
    normalizar, igual que en el análisis municipal.

    NOTA: Este IVS por localidad es una aproximación para la
    interpolación espacial — no es el IVS municipal oficial del estudio.
    """
    df = df.copy()

    # Convertir variables a numérico
    todas_vars = VARS_LOCALIDAD_VS + VARS_LOCALIDAD_EF
    for col in todas_vars:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Calcular proporciones
    vars_pob = ["P15YM_AN", "PSINDER"]
    vars_viv = ["VPH_AGUAFV", "VPH_NODREN", "VPH_PISODT",
                "VPH_C_ELEC", "VPH_SNBIEN"]

    for col in vars_pob:
        if col in df.columns:
            df[f"PROP_{col}"] = (df[col] / df["POBTOT"]).clip(0, 1)

    for col in vars_viv:
        if col in df.columns:
            df[f"PROP_{col}"] = (df[col] / df["TVIVHAB"]).clip(0, 1)

    # Normalización min-max por variable
    def minmax(serie):
        mn, mx = serie.min(), serie.max()
        return pd.Series(0.5, index=serie.index) if mx == mn \
               else (serie - mn) / (mx - mn)

    cols_vs, cols_ef = [], []

    for col in VARS_LOCALIDAD_VS:
        prop = f"PROP_{col}" if col != "POBTOT" else col
        if prop in df.columns:
            norm_col = f"NORM_{col}"
            df[norm_col] = minmax(df[prop].fillna(df[prop].median()))
            cols_vs.append(norm_col)

    for col in VARS_LOCALIDAD_EF:
        prop = f"PROP_{col}" if col != "POBTOT" else col
        if prop in df.columns:
            norm_col = f"NORM_{col}"
            df[norm_col] = minmax(df[prop].fillna(df[prop].median()))
            cols_ef.append(norm_col)

    # Dimensiones e IVS
    df["DIM_VS"] = df[cols_vs].mean(axis=1) if cols_vs else 0.5
    df["DIM_EF"] = df[cols_ef].mean(axis=1) if cols_ef else 0.5
    df["IVS_LOC"] = (df["DIM_VS"] * PESO_VS + df["DIM_EF"] * PESO_EF)

    print(f"  IVS por localidad calculado: {len(df)} localidades")
    print(f"  IVS rango: [{df['IVS_LOC'].min():.3f} — "
          f"{df['IVS_LOC'].max():.3f}]")
    print(f"  Variables VS usadas: {len(cols_vs)} | "
          f"Variables EF usadas: {len(cols_ef)}")

    return df


# =============================================================================
# INTERPOLACIÓN IDW
# =============================================================================

def interpolar_idw(puntos_x: np.ndarray,
                   puntos_y: np.ndarray,
                   valores:  np.ndarray,
                   grid_x:   np.ndarray,
                   grid_y:   np.ndarray,
                   potencia: int = 2,
                   vecinos:  int = 8) -> np.ndarray:
    """
    Interpolación IDW (Inverse Distance Weighting).

    Para cada punto de la grilla busca los K vecinos más cercanos
    y calcula el valor como promedio ponderado por la inversa de
    la distancia elevada a la potencia p.

    Fórmula:
        z* = Σ(z_i / d_i^p) / Σ(1 / d_i^p)

    donde d_i es la distancia al vecino i y p es la potencia.
    """
    # Construir árbol KD para búsqueda eficiente de vecinos
    puntos = np.column_stack([puntos_x, puntos_y])
    arbol  = cKDTree(puntos)

    # Puntos de la grilla
    grilla = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # Buscar K vecinos más cercanos para cada punto de la grilla
    distancias, indices = arbol.query(grilla, k=min(vecinos, len(puntos)))

    # Manejar caso de un solo vecino (distancias 1D)
    if distancias.ndim == 1:
        distancias = distancias[:, np.newaxis]
        indices    = indices[:, np.newaxis]

    # Evitar división por cero en puntos exactamente sobre datos
    distancias = np.where(distancias == 0, 1e-10, distancias)

    # Calcular pesos IDW
    pesos  = 1.0 / np.power(distancias, potencia)
    pesos_norm = pesos / pesos.sum(axis=1, keepdims=True)

    # Interpolación
    vals_vecinos = valores[indices]
    resultado    = (pesos_norm * vals_vecinos).sum(axis=1)

    return resultado.reshape(grid_x.shape)


# =============================================================================
# GENERACIÓN DEL MAPA
# =============================================================================

def generar_mapa_interpolado(df: pd.DataFrame) -> None:
    """
    Genera el mapa de superficie continua interpolada.
    Recorta la superficie al límite estatal de Campeche usando
    el shapefile si geopandas está disponible.
    """
    try:
        import geopandas as gpd
        from matplotlib.patches import PathPatch
        from matplotlib.path import Path as MplPath
        from shapely.ops import unary_union
        TIENE_GEO = True
    except ImportError:
        print("  ⚠ geopandas no disponible — mapa sin recorte al límite estatal")
        TIENE_GEO = False

    # ── Preparar puntos de datos ──────────────────────────────────────────────
    df_valido = df.dropna(subset=["LONGITUD", "LATITUD", "IVS_LOC"])
    lons = df_valido["LONGITUD"].values
    lats = df_valido["LATITUD"].values
    ivs  = df_valido["IVS_LOC"].values

    print(f"  Puntos para interpolación: {len(lons):,}")

    # ── Crear grilla ──────────────────────────────────────────────────────────
    lon_min, lon_max = lons.min() - 0.1, lons.max() + 0.1
    lat_min, lat_max = lats.min() - 0.1, lats.max() + 0.1

    grid_lon, grid_lat = np.meshgrid(
        np.linspace(lon_min, lon_max, GRID_RESOLUCION),
        np.linspace(lat_min, lat_max, GRID_RESOLUCION),
    )

    print(f"  Grilla: {GRID_RESOLUCION}×{GRID_RESOLUCION} puntos")
    print("  Interpolando con IDW (esto puede tardar ~30s)...")

    # ── IDW ──────────────────────────────────────────────────────────────────
    grid_ivs = interpolar_idw(
        lons, lats, ivs,
        grid_lon, grid_lat,
        potencia=IDW_POTENCIA,
        vecinos=IDW_VECINOS,
    )

    print(f"  Interpolación completada. "
          f"Rango grilla: [{grid_ivs.min():.3f} — {grid_ivs.max():.3f}]")

    # ── Figura ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 10))

    # Superficie interpolada
    img = ax.pcolormesh(
        grid_lon, grid_lat, grid_ivs,
        cmap="YlOrRd",
        vmin=0, vmax=1,
        shading="gouraud",   # Interpolación suave entre celdas
        zorder=1,
    )

    # Barra de color
    cbar = plt.colorbar(img, ax=ax, shrink=0.65, pad=0.02, aspect=20)
    cbar.set_label("Índice de Vulnerabilidad Socioterritorial (IVS)",
                   fontsize=FS_EJE)
    cbar.ax.tick_params(labelsize=FS_TICK)

    # ── Límite estatal y municipal encima ─────────────────────────────────────
    if TIENE_GEO and SHP_MUN.exists():
        gdf = gpd.read_file(SHP_MUN)

        # Contorno de municipios en blanco semitransparente
        gdf.boundary.plot(ax=ax, linewidth=0.7,
                          edgecolor="white", alpha=0.6, zorder=2)

        # Contorno estatal en blanco sólido
        estado = gdf.dissolve()
        estado.boundary.plot(ax=ax, linewidth=1.8,
                             edgecolor="white", zorder=3)

        # Máscara fuera del estado (recorte visual)
        try:
            from shapely.ops import unary_union
            poligono_estado = unary_union(gdf.geometry)
            # Crear máscara blanca fuera del estado
            from shapely.geometry import box
            bbox = box(lon_min - 1, lat_min - 1,
                       lon_max + 1, lat_max + 1)
            mascara = bbox.difference(poligono_estado)
            from descartes import PolygonPatch
            patch = PolygonPatch(mascara, fc="white", ec="none",
                                 alpha=1.0, zorder=4)
            ax.add_patch(patch)
        except Exception:
            # Si descartes no está disponible, continuar sin máscara
            print("  ℹ Instala 'descartes' para recorte preciso al límite estatal")
            print("    pip install descartes")

        # Etiquetas de municipios con acrónimos
        ACRONIMOS_MAP = {
            "Calkiní":     "CK", "Campeche":  "CA", "Carmen":   "CR",
            "Champotón":   "CH", "Hecelchakán": "HE", "Hopelchén": "HO",
            "Palizada":    "PA", "Tenabo":    "TE", "Escárcega": "ES",
            "Calakmul":    "CL", "Candelaria": "CN", "Seybaplaya": "SY",
        }
        for _, row in gdf.iterrows():
            if row.geometry:
                c    = row.geometry.centroid
                nom  = str(row.get("NOMGEO", row.get("NOM_MUN", "")))
                acr  = ACRONIMOS_MAP.get(nom, nom[:2].upper())
                ax.annotate(
                    acr, xy=(c.x, c.y),
                    ha="center", va="center",
                    fontsize=10, color="white",
                    fontweight="bold", zorder=5,
                )

    # Puntos de localidades como referencia (opcional, pequeños)
    ax.scatter(lons, lats, c="black", s=1.5,
               alpha=0.25, zorder=6, label="Localidades")

    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_xlabel("Longitud", fontsize=FS_EJE)
    ax.set_ylabel("Latitud",  fontsize=FS_EJE)
    ax.tick_params(labelsize=FS_TICK)
    ax.set_title(
        "Superficie continua de vulnerabilidad ante inundaciones\n"
        "Campeche, México — Interpolación IDW (Censo 2020)",
        fontsize=FS_TITULO, pad=14,
    )

    plt.tight_layout()
    ruta = DIR_MAPAS / f"fig05_mapa_interpolado.{FORMATO_FIG}"
    DIR_MAPAS.mkdir(parents=True, exist_ok=True)
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta.name}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SCRIPT 08 — Mapa de superficie interpolada (IDW)")
    print("=" * 60)

    # 1. Cargar localidades
    df = cargar_iter_localidades()

    # 2. Calcular IVS por localidad
    df = calcular_ivs_localidad(df)

    # 3. Generar mapa interpolado
    generar_mapa_interpolado(df)

    print("\n✓ Script 08 completado exitosamente\n")


if __name__ == "__main__":
    main()