# =============================================================================
# 08_mapa_interpolado.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  2.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Genera mapas de superficie continua interpolada (IDW) para:
#     fig05 — IVS compuesto
#     fig06 — DIM_SS Sensibilidad Social
#     fig07 — DIM_EF Exposición Física
#     fig08 — DIM_CA Capacidad Adaptativa
#     fig09 — DIM_GV Grupos Vulnerables
#     fig10 — Dimensión dominante por zona
#     fig11 — Panel comparativo 4 dimensiones + IVS
#
#   Entrada:  01_datos_crudos/iter_04_cpv2020_csv/.../conjunto_de_datos_iter_04CSV20.csv
#             01_datos_crudos/2025_1_04_MUN/2025_1_04_MUN.shp
#             01_datos_crudos/04_campeche/conjunto_de_datos/04l.shp
#             01_datos_crudos/natural_earth_agua/ne_10m_land.shp
#   Salida:   04_outputs/mapas/fig05–fig11
# =============================================================================

import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.colors import PowerNorm, ListedColormap
from pathlib import Path
from scipy.spatial import cKDTree

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.family"] = "DejaVu Sans"

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from config import (
    ITER_CSV,
    SHP_MUN,
    DIR_MAPAS,
    DATOS_INDICE,
    DPI_FIGURAS,
    FORMATO_FIG,
    PESOS_DIMENSIONES,
)

# ── Parámetros de interpolación ───────────────────────────────────────────────
IDW_POTENCIA    = 3
IDW_VECINOS     = 4
GRID_RESOLUCION = 300

# ── Tamaños de fuente ─────────────────────────────────────────────────────────
FS_TITULO = 15
FS_EJE    = 12
FS_TICK   = 11

# ── Variables para IVS a nivel localidad ─────────────────────────────────────
VARS_LOC_SS = ["P15YM_AN", "VPH_AGUAFV", "VPH_NODREN", "VPH_PISODT", "PSINDER"]
VARS_LOC_EF = ["POBTOT", "VPH_C_ELEC", "VPH_SNBIEN"]
VARS_LOC_CA = ["GRAPROES", "P18YM_PB", "PDER_IMSS", "POCUPADA"]
VARS_LOC_GV = ["P60YMAS", "POB0_14", "P3YM_HLI", "PCON_DISC"]

# ── Acrónimos ─────────────────────────────────────────────────────────────────
ACRONIMOS_MAP = {
    "Calkiní":     "CK", "Campeche":    "CA", "Carmen":    "CR",
    "Champotón":   "CH", "Hecelchakán": "HE", "Hopelchén": "HO",
    "Palizada":    "PA", "Tenabo":       "TE", "Escárcega": "ES",
    "Calakmul":    "CL", "Candelaria":   "CN", "Seybaplaya":"SY",
}

# ── Configuración de cada mapa ────────────────────────────────────────────────
MAPAS_CONFIG = [
    {
        "id":      "fig05",
        "col":     "IVS_LOC",
        "titulo":  "Índice de Vulnerabilidad Socioterritorial (IVS)\nCampeche, México — Interpolación IDW (Censo 2020)",
        "cmap":    "RdYlGn_r",
        "archivo": "fig05_mapa_interpolado",
    },
    {
        "id":      "fig06",
        "col":     "DIM_SS_LOC",
        "titulo":  "Dimensión Sensibilidad Social (DIM_SS)\nCampeche, México — Interpolación IDW (Censo 2020)",
        "cmap":    "RdYlGn_r",
        "archivo": "fig06_mapa_dim_ss",
    },
    {
        "id":      "fig07",
        "col":     "DIM_EF_LOC",
        "titulo":  "Dimensión Exposición Física (DIM_EF)\nCampeche, México — Interpolación IDW (Censo 2020)",
        "cmap":    "RdYlBu_r",
        "archivo": "fig07_mapa_dim_ef",
    },
    {
        "id":      "fig08",
        "col":     "DIM_CA_LOC",
        "titulo":  "Dimensión Capacidad Adaptativa (DIM_CA)\nCampeche, México — Interpolación IDW (Censo 2020)",
        "cmap":    "RdYlGn",   # Invertido: verde=alta CA=menos vulnerable
        "archivo": "fig08_mapa_dim_ca",
    },
    {
        "id":      "fig09",
        "col":     "DIM_GV_LOC",
        "titulo":  "Dimensión Grupos Vulnerables (DIM_GV)\nCampeche, México — Interpolación IDW (Censo 2020)",
        "cmap":    "YlOrRd",
        "archivo": "fig09_mapa_dim_gv",
    },
]


# =============================================================================
# UTILIDADES GEOESPACIALES
# =============================================================================

def cargar_geodatos():
    """
    Carga y prepara todos los geodatos necesarios:
    - Shapefile municipal reproyectado a WGS84
    - Polígono estatal (unión de municipios)
    - Polígono de tierra Natural Earth (excluye agua)
    """
    import geopandas as gpd
    from shapely.ops import unary_union
    from shapely.geometry import box

    print("  Cargando geodatos...")

    # Municipios
    gdf_mun = gpd.read_file(SHP_MUN)
    if gdf_mun.crs.to_epsg() != 4326:
        gdf_mun = gdf_mun.to_crs(epsg=4326)

    # Polígono estatal
    poligono_estado = unary_union(gdf_mun.geometry)

    # Tierra Natural Earth
    dir_agua = ITER_CSV.parents[3] / "01_datos_crudos" / "natural_earth_agua"
    shp_land = dir_agua / "ne_10m_land.shp"
    if shp_land.exists():
        gdf_land = gpd.read_file(shp_land)
        if gdf_land.crs.to_epsg() != 4326:
            gdf_land = gdf_land.to_crs(epsg=4326)
        bbox_camp = box(
            gdf_mun.total_bounds[0] - 0.5,
            gdf_mun.total_bounds[1] - 0.5,
            gdf_mun.total_bounds[2] + 0.5,
            gdf_mun.total_bounds[3] + 0.5,
        )
        land_camp    = gdf_land[gdf_land.intersects(bbox_camp)]
        tierra_union = unary_union(land_camp.geometry)
        poligono_estado = poligono_estado.intersection(tierra_union)
        print("  Cuerpos de agua excluidos ✓")
    else:
        print("  ⚠ ne_10m_land.shp no encontrado — sin exclusión de agua")

    print(f"  BBox: {gdf_mun.total_bounds}")
    return gdf_mun, poligono_estado


def crear_mascara(grid_lon, grid_lat, poligono):
    """
    Crea una máscara booleana: True = fuera del polígono (enmascarar).
    Usa vectorización con STRtree para mayor velocidad.
    """
    from shapely.geometry import MultiPoint
    import geopandas as gpd

    print("  Creando máscara vectorizada...")
    filas, cols = grid_lon.shape
    puntos_flat = np.column_stack([grid_lon.ravel(), grid_lat.ravel()])

    gdf_puntos = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(puntos_flat[:, 0], puntos_flat[:, 1]),
        crs="EPSG:4326"
    )
    dentro = gdf_puntos.within(poligono)
    mascara = ~dentro.values.reshape(filas, cols)
    print(f"  Celdas dentro: {dentro.sum():,} / {filas*cols:,}")
    return mascara


# =============================================================================
# CARGA Y CÁLCULO DE DATOS POR LOCALIDAD
# =============================================================================

def cargar_iter_localidades():
    """
    Carga localidades con coordenadas WGS84 desde shapefile 04l.shp
    y variables socioeconómicas del ITER CSV.
    """
    import geopandas as gpd

    shp_loc = ITER_CSV.parents[2] / "04_campeche" / \
              "conjunto_de_datos" / "04l.shp"

    print(f"  Cargando shapefile: {shp_loc.name}")
    try:
        gdf = gpd.read_file(shp_loc, engine="fiona", encoding="latin-1")
    except Exception:
        gdf = gpd.read_file(shp_loc)

    # Reproyectar a WGS84 ANTES de extraer centroides
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf["_LON"] = gdf.geometry.centroid.x
    gdf["_LAT"] = gdf.geometry.centroid.y
    gdf["_CLAVE"] = gdf["CVEGEO"].astype(str).str.zfill(9)
    gdf_coords = gdf[["_CLAVE", "_LON", "_LAT"]].copy()

    print(f"  Localidades shapefile: {len(gdf_coords):,}")

    # ITER CSV
    df = pd.read_csv(ITER_CSV, encoding="utf-8-sig",
                     dtype=str, low_memory=False)
    df.columns = [c.replace("ï»¿", "").strip() for c in df.columns]
    df = df[(df["MUN"] != "000") &
            (~df["LOC"].isin(["0000", "000"]))].copy()

    # Eliminar columnas DMS del ITER
    df = df.drop(columns=[c for c in ["LONGITUD", "LATITUD", "ALTITUD"]
                           if c in df.columns])

    df["_CLAVE"] = "04" + \
        df["MUN"].astype(str).str.zfill(3) + \
        df["LOC"].astype(str).str.zfill(4)

    # Merge
    df_merge = df.merge(gdf_coords, on="_CLAVE", how="inner")

    for col in ["POBTOT", "TVIVHAB"]:
        if col in df_merge.columns:
            df_merge[col] = pd.to_numeric(df_merge[col], errors="coerce")

    df_merge = df_merge[
        df_merge["POBTOT"].notna() &
        (df_merge["POBTOT"] > 0) &
        df_merge["_LON"].notna()
    ].copy()

    df_merge = df_merge.rename(
        columns={"_LON": "LONGITUD", "_LAT": "LATITUD"}
    )

    print(f"  Localidades válidas: {len(df_merge):,}")
    return df_merge


def calcular_dimensiones_localidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula las 4 dimensiones e IVS a nivel localidad.
    Variables de CA se invierten (mayor = menos vulnerable).
    """
    df = df.copy()

    def minmax(serie):
        mn, mx = serie.min(), serie.max()
        return pd.Series(0.5, index=serie.index) if mx == mn \
               else (serie - mn) / (mx - mn)

    def calc_dim(vars_list, inversas=None):
        inversas = inversas or []
        cols = []
        for col in vars_list:
            if col not in df.columns:
                continue
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Proporción
            if col in ["GRAPROES", "POBTOT"]:
                prop = df[col].fillna(df[col].median())
            elif col in ["P15YM_AN", "PSINDER", "P18YM_PB", "PDER_IMSS",
                         "POCUPADA", "P60YMAS", "POB0_14",
                         "P3YM_HLI", "PCON_DISC"]:
                prop = (df[col] / df["POBTOT"]).clip(0, 1).fillna(0)
            else:
                prop = (df[col] / df["TVIVHAB"]).clip(0, 1).fillna(0)

            norm_col = f"_N_{col}"
            df[norm_col] = minmax(prop)
            if col in inversas:
                df[norm_col] = 1 - df[norm_col]
            cols.append(norm_col)
        return df[cols].mean(axis=1) if cols else pd.Series(0.5, index=df.index)

    df["DIM_SS_LOC"] = calc_dim(VARS_LOC_SS)
    df["DIM_EF_LOC"] = calc_dim(VARS_LOC_EF)
    df["DIM_CA_LOC"] = calc_dim(
        VARS_LOC_CA,
        inversas=["GRAPROES", "P18YM_PB", "PDER_IMSS", "POCUPADA"]
    )
    df["DIM_GV_LOC"] = calc_dim(VARS_LOC_GV)

    p = PESOS_DIMENSIONES
    df["IVS_LOC"] = (
        df["DIM_SS_LOC"] * p["SS"] +
        df["DIM_EF_LOC"] * p["EF"] +
        df["DIM_CA_LOC"] * p["CA"] +
        df["DIM_GV_LOC"] * p["GV"]
    )

    print(f"  IVS rango: [{df['IVS_LOC'].min():.3f}–{df['IVS_LOC'].max():.3f}]")
    for dim in ["DIM_SS_LOC", "DIM_EF_LOC", "DIM_CA_LOC", "DIM_GV_LOC"]:
        print(f"  {dim}: [{df[dim].min():.3f}–{df[dim].max():.3f}]")

    return df


# =============================================================================
# INTERPOLACIÓN IDW
# =============================================================================

def interpolar_idw(lons, lats, vals, grid_lon, grid_lat,
                   potencia=3, vecinos=4):
    """IDW con cKDTree para eficiencia."""
    puntos  = np.column_stack([lons, lats])
    arbol   = cKDTree(puntos)
    grilla  = np.column_stack([grid_lon.ravel(), grid_lat.ravel()])
    dists, idx = arbol.query(grilla, k=min(vecinos, len(puntos)))

    if dists.ndim == 1:
        dists = dists[:, np.newaxis]
        idx   = idx[:, np.newaxis]

    dists  = np.where(dists == 0, 1e-10, dists)
    pesos  = 1.0 / np.power(dists, potencia)
    pesos /= pesos.sum(axis=1, keepdims=True)

    return (pesos * vals[idx]).sum(axis=1).reshape(grid_lon.shape)


# =============================================================================
# GENERACIÓN DE MAPA INDIVIDUAL
# =============================================================================

def generar_mapa(df, col, titulo, cmap, archivo,
                 gdf_mun, poligono_estado, mascara,
                 grid_lon, grid_lat):
    """Genera un mapa interpolado para una variable dada."""
    import geopandas as gpd
    from shapely.ops import unary_union

    lons = df["LONGITUD"].values.astype(float)
    lats = df["LATITUD"].values.astype(float)
    vals = df[col].values.astype(float)

    print(f"  Interpolando {col}...")
    grid_vals = interpolar_idw(
        lons, lats, vals, grid_lon, grid_lat,
        potencia=IDW_POTENCIA, vecinos=IDW_VECINOS,
    )

    grid_masked = np.ma.masked_where(mascara, grid_vals)
    valores_validos = grid_masked.compressed()
    vmin = np.percentile(valores_validos, 5)
    vmax = np.percentile(valores_validos, 95)
    norma = PowerNorm(gamma=0.7, vmin=vmin, vmax=vmax)

    fig, ax = plt.subplots(figsize=(12, 11))
    ax.set_facecolor("#d6eaf8")

    ax.pcolormesh(grid_lon, grid_lat, grid_masked,
                  cmap=cmap, norm=norma,
                  shading="gouraud", zorder=2)

    # Contornos
    gdf_mun.boundary.plot(ax=ax, linewidth=0.8,
                          edgecolor="white", alpha=0.8, zorder=3)
    gdf_estado = gpd.GeoDataFrame(
        geometry=[poligono_estado], crs="EPSG:4326"
    )
    gdf_estado.boundary.plot(ax=ax, linewidth=2.2,
                             edgecolor="black", zorder=4)

    # Etiquetas
    col_nom = next((c for c in ["NOMGEO", "NOM_MUN"]
                    if c in gdf_mun.columns), None)
    if col_nom:
        for _, row in gdf_mun.iterrows():
            if row.geometry:
                c   = row.geometry.centroid
                nom = str(row[col_nom])
                acr = ACRONIMOS_MAP.get(nom, nom[:2].upper())
                ax.annotate(
                    acr, xy=(c.x, c.y),
                    ha="center", va="center",
                    fontsize=11, color="white", fontweight="bold",
                    zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2",
                              fc="black", alpha=0.4, ec="none")
                )

    # Puntos de localidades
    ax.scatter(lons, lats, c="black", s=3, alpha=0.3, zorder=5)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norma)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02, aspect=20)
    cbar.set_label("Valor normalizado [0–1]", fontsize=FS_EJE)
    cbar.ax.tick_params(labelsize=FS_TICK)
    ticks = np.linspace(vmin, vmax, 5)
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([f"{v:.3f}" for v in ticks])

    bbox = gdf_mun.total_bounds
    ax.set_xlim(bbox[0] - 0.05, bbox[2] + 0.05)
    ax.set_ylim(bbox[1] - 0.05, bbox[3] + 0.05)
    ax.set_xlabel("Longitud (°)", fontsize=FS_EJE)
    ax.set_ylabel("Latitud (°)", fontsize=FS_EJE)
    ax.tick_params(labelsize=FS_TICK)
    ax.set_title(titulo, fontsize=FS_TITULO, pad=14)

    plt.tight_layout()
    ruta = DIR_MAPAS / f"{archivo}.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta.name}")


# =============================================================================
# MAPA DE DIMENSIÓN DOMINANTE
# =============================================================================

def generar_mapa_dimension_dominante(df, gdf_mun, poligono_estado,
                                     mascara, grid_lon, grid_lat):
    """
    fig10 — Mapa de la dimensión con mayor valor por zona.
    Muestra qué dimensión domina la vulnerabilidad en cada punto.
    """
    import geopandas as gpd

    print("  Generando fig10 — Dimensión dominante...")
    dims = {
        "SS": ("DIM_SS_LOC", "#d73027"),
        "EF": ("DIM_EF_LOC", "#4575b4"),
        "CA": ("DIM_CA_LOC", "#fdae61"),
        "GV": ("DIM_GV_LOC", "#1a9641"),
    }

    lons = df["LONGITUD"].values.astype(float)
    lats = df["LATITUD"].values.astype(float)

    # Interpolar cada dimensión
    grids = {}
    for nombre, (col, _) in dims.items():
        vals = df[col].values.astype(float)
        grids[nombre] = interpolar_idw(
            lons, lats, vals, grid_lon, grid_lat,
            potencia=IDW_POTENCIA, vecinos=IDW_VECINOS,
        )

    # Encontrar dimensión dominante en cada celda
    stack       = np.stack(list(grids.values()), axis=-1)
    idx_dom     = np.argmax(stack, axis=-1)
    nombres_dim = list(grids.keys())

    # Crear mapa de colores categórico
    colores_dims = [dims[n][1] for n in nombres_dim]
    cmap_cat     = ListedColormap(colores_dims)

    idx_masked = np.ma.masked_where(mascara, idx_dom.astype(float))

    fig, ax = plt.subplots(figsize=(12, 11))
    ax.set_facecolor("#d6eaf8")

    ax.pcolormesh(grid_lon, grid_lat, idx_masked,
                  cmap=cmap_cat, vmin=-0.5, vmax=3.5,
                  shading="nearest", zorder=2)

    # Contornos
    gdf_mun.boundary.plot(ax=ax, linewidth=0.8,
                          edgecolor="white", alpha=0.8, zorder=3)
    gdf_estado = gpd.GeoDataFrame(
        geometry=[poligono_estado], crs="EPSG:4326"
    )
    gdf_estado.boundary.plot(ax=ax, linewidth=2.2,
                             edgecolor="black", zorder=4)

    # Etiquetas municipios
    col_nom = next((c for c in ["NOMGEO", "NOM_MUN"]
                    if c in gdf_mun.columns), None)
    if col_nom:
        for _, row in gdf_mun.iterrows():
            if row.geometry:
                c   = row.geometry.centroid
                nom = str(row[col_nom])
                acr = ACRONIMOS_MAP.get(nom, nom[:2].upper())
                ax.annotate(
                    acr, xy=(c.x, c.y),
                    ha="center", va="center",
                    fontsize=11, color="white", fontweight="bold",
                    zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2",
                              fc="black", alpha=0.4, ec="none")
                )

    # Leyenda
    etiquetas = {
        "SS": "Sensibilidad Social",
        "EF": "Exposición Física",
        "CA": "Capacidad Adaptativa",
        "GV": "Grupos Vulnerables",
    }
    parches = [mpatches.Patch(color=dims[n][1],
               label=etiquetas[n]) for n in nombres_dim]
    ax.legend(handles=parches, title="Dimensión dominante",
              loc="lower left", fontsize=11, title_fontsize=11,
              framealpha=0.8)

    bbox = gdf_mun.total_bounds
    ax.set_xlim(bbox[0] - 0.05, bbox[2] + 0.05)
    ax.set_ylim(bbox[1] - 0.05, bbox[3] + 0.05)
    ax.set_xlabel("Longitud (°)", fontsize=FS_EJE)
    ax.set_ylabel("Latitud (°)", fontsize=FS_EJE)
    ax.tick_params(labelsize=FS_TICK)
    ax.set_title(
        "Dimensión de mayor vulnerabilidad por zona\n"
        "Campeche, México — Interpolación IDW (Censo 2020)",
        fontsize=FS_TITULO, pad=14
    )

    plt.tight_layout()
    ruta = DIR_MAPAS / f"fig10_mapa_dimension_dominante.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta.name}")


# =============================================================================
# PANEL COMPARATIVO
# =============================================================================

def generar_panel_comparativo(df, gdf_mun, poligono_estado,
                               mascara, grid_lon, grid_lat):
    """
    fig11 — Panel 2×3 con IVS y las 4 dimensiones.
    """
    import geopandas as gpd

    print("  Generando fig11 — Panel comparativo...")

    paneles = [
        ("IVS_LOC",    "IVS Compuesto",         "RdYlGn_r"),
        ("DIM_SS_LOC", "Sensibilidad Social",    "RdYlGn_r"),
        ("DIM_EF_LOC", "Exposición Física",      "RdYlBu_r"),
        ("DIM_CA_LOC", "Capacidad Adaptativa",   "RdYlGn"),
        ("DIM_GV_LOC", "Grupos Vulnerables",     "YlOrRd"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(20, 14))
    axes_flat = axes.flatten()

    lons = df["LONGITUD"].values.astype(float)
    lats = df["LATITUD"].values.astype(float)
    bbox = gdf_mun.total_bounds

    col_nom = next((c for c in ["NOMGEO", "NOM_MUN"]
                    if c in gdf_mun.columns), None)

    for i, (col, etiqueta, cmap) in enumerate(paneles):
        ax = axes_flat[i]
        vals = df[col].values.astype(float)

        grid_vals  = interpolar_idw(
            lons, lats, vals, grid_lon, grid_lat,
            potencia=IDW_POTENCIA, vecinos=IDW_VECINOS,
        )
        grid_masked = np.ma.masked_where(mascara, grid_vals)
        v_validos   = grid_masked.compressed()
        vmin = np.percentile(v_validos, 5)
        vmax = np.percentile(v_validos, 95)
        norma = PowerNorm(gamma=0.7, vmin=vmin, vmax=vmax)

        ax.set_facecolor("#d6eaf8")
        im = ax.pcolormesh(grid_lon, grid_lat, grid_masked,
                           cmap=cmap, norm=norma,
                           shading="gouraud", zorder=2)

        gdf_mun.boundary.plot(ax=ax, linewidth=0.5,
                              edgecolor="white", alpha=0.7, zorder=3)
        gdf_estado = gpd.GeoDataFrame(
            geometry=[poligono_estado], crs="EPSG:4326"
        )
        gdf_estado.boundary.plot(ax=ax, linewidth=1.5,
                                 edgecolor="black", zorder=4)

        # Etiquetas pequeñas
        if col_nom:
            for _, row in gdf_mun.iterrows():
                if row.geometry:
                    c   = row.geometry.centroid
                    nom = str(row[col_nom])
                    acr = ACRONIMOS_MAP.get(nom, nom[:2].upper())
                    ax.annotate(
                        acr, xy=(c.x, c.y),
                        ha="center", va="center",
                        fontsize=7, color="white", fontweight="bold",
                        zorder=6,
                        bbox=dict(boxstyle="round,pad=0.1",
                                  fc="black", alpha=0.35, ec="none")
                    )

        cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
        cbar.ax.tick_params(labelsize=8)
        ticks = np.linspace(vmin, vmax, 3)
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f"{v:.2f}" for v in ticks])

        ax.set_xlim(bbox[0] - 0.05, bbox[2] + 0.05)
        ax.set_ylim(bbox[1] - 0.05, bbox[3] + 0.05)
        ax.set_title(etiqueta, fontsize=12, fontweight="bold", pad=8)
        ax.tick_params(labelsize=8)
        ax.set_xlabel("Longitud (°)", fontsize=9)
        ax.set_ylabel("Latitud (°)", fontsize=9)

    # Ocultar el sexto panel vacío
    axes_flat[5].set_visible(False)

    fig.suptitle(
        "Componentes del Índice de Vulnerabilidad Socioterritorial\n"
        "Campeche, México — Interpolación IDW (Censo 2020)",
        fontsize=16, fontweight="bold", y=1.01
    )

    plt.tight_layout()
    ruta = DIR_MAPAS / f"fig11_panel_comparativo.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta.name}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SCRIPT 08 — Mapas de superficie interpolada (IDW)")
    print("=" * 60)

    DIR_MAPAS.mkdir(parents=True, exist_ok=True)

    # ── 1. Geodatos ───────────────────────────────────────────────────────────
    gdf_mun, poligono_estado = cargar_geodatos()
    bbox = gdf_mun.total_bounds

    # ── 2. Grilla común para todos los mapas ──────────────────────────────────
    lon_min, lat_min = bbox[0] - 0.05, bbox[1] - 0.05
    lon_max, lat_max = bbox[2] + 0.05, bbox[3] + 0.05

    grid_lon, grid_lat = np.meshgrid(
        np.linspace(lon_min, lon_max, GRID_RESOLUCION),
        np.linspace(lat_min, lat_max, GRID_RESOLUCION),
    )
    print(f"  Grilla: {GRID_RESOLUCION}×{GRID_RESOLUCION}")

    # ── 3. Máscara (calculada una sola vez) ───────────────────────────────────
    mascara = crear_mascara(grid_lon, grid_lat, poligono_estado)

    # ── 4. Datos por localidad ────────────────────────────────────────────────
    df = cargar_iter_localidades()
    df = calcular_dimensiones_localidad(df)

    # ── 5. Mapas individuales fig05–fig09 ─────────────────────────────────────
    print("\n  [Mapas individuales]")
    for cfg in MAPAS_CONFIG:
        generar_mapa(
            df, cfg["col"], cfg["titulo"], cfg["cmap"], cfg["archivo"],
            gdf_mun, poligono_estado, mascara, grid_lon, grid_lat,
        )

    # ── 6. Mapa dimensión dominante fig10 ─────────────────────────────────────
    print("\n  [Mapa dimensión dominante]")
    generar_mapa_dimension_dominante(
        df, gdf_mun, poligono_estado, mascara, grid_lon, grid_lat
    )

    # ── 7. Panel comparativo fig11 ────────────────────────────────────────────
    print("\n  [Panel comparativo]")
    generar_panel_comparativo(
        df, gdf_mun, poligono_estado, mascara, grid_lon, grid_lat
    )

    print("\n✓ Script 08 completado exitosamente")
    print(f"  Mapas en: {DIR_MAPAS}\n")


if __name__ == "__main__":
    main()