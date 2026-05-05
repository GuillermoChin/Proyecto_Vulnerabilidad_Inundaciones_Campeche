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
IDW_VECINOS    = 5       # Número de vecinos para el IDW
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
    Carga localidades combinando:
    - Coordenadas decimales del shapefile 04l.shp
    - Variables socioeconómicas del ITER CSV
    Merge por clave CVEGEO de 9 dígitos.
    """
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError("Instala geopandas: pip install geopandas")

    # ── 1. Shapefile de localidades ───────────────────────────────────────────
    shp_loc = ITER_CSV.parents[2] / "04_campeche" / \
              "conjunto_de_datos" / "04l.shp"
    if not shp_loc.exists():
        shp_loc = ITER_CSV.parents[2] / "04_campeche" / \
                  "conjunto_de_datos" / "04sip.shp"

    print(f"  Cargando shapefile de localidades: {shp_loc.name}")
    try:
        gdf = gpd.read_file(shp_loc, engine="fiona", encoding="latin-1")
    except Exception:
        gdf = gpd.read_file(shp_loc)

    print(f"  Columnas shapefile: {list(gdf.columns)}")
    print(f"  CRS original: {gdf.crs}")

    # Reproyectar a WGS84 ANTES de extraer centroides
    # El shapefile viene en Lambert Conformal Conic (metros)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
        print(f"  Reproyectado a WGS84 ✓")

    # Extraer coordenadas decimales del centroide (ya en grados)
    gdf["_LON"] = gdf.geometry.centroid.x
    gdf["_LAT"] = gdf.geometry.centroid.y

    print(f"  Rango LON: [{gdf['_LON'].min():.4f} — {gdf['_LON'].max():.4f}]")
    print(f"  Rango LAT: [{gdf['_LAT'].min():.4f} — {gdf['_LAT'].max():.4f}]")

    # Corregir longitudes positivas
    if gdf["_LON"].mean() > 0:
        gdf["_LON"] = -gdf["_LON"]

    # Clave de 9 dígitos
    gdf["_CLAVE"] = gdf["CVEGEO"].astype(str).str.zfill(9)

    # Solo quedarnos con lo que necesitamos del shapefile
    gdf_coords = gdf[["_CLAVE", "_LON", "_LAT"]].copy()
    print(f"  Localidades en shapefile: {len(gdf_coords):,}")
    print(f"  Ejemplo clave shapefile: {gdf_coords['_CLAVE'].iloc[0]}")

    # ── 2. ITER CSV ───────────────────────────────────────────────────────────
    print(f"  Cargando ITER: {ITER_CSV.name}")
    df = pd.read_csv(
        ITER_CSV,
        encoding="utf-8-sig",
        dtype=str,
        low_memory=False,
    )
    df.columns = [c.replace("ï»¿", "").strip() for c in df.columns]

    # Filtrar solo localidades
    df = df[
        (df["MUN"] != "000") &
        (~df["LOC"].isin(["0000", "000"]))
    ].copy()

    # Eliminar columnas de coordenadas DMS del ITER (no son útiles)
    df = df.drop(columns=[c for c in ["LONGITUD", "LATITUD", "ALTITUD"]
                           if c in df.columns])

    # Construir clave de 9 dígitos
    ent = "04"  # Campeche
    df["_CLAVE"] = (
        ent +
        df["MUN"].astype(str).str.zfill(3) +
        df["LOC"].astype(str).str.zfill(4)
    )

    print(f"  Localidades en ITER: {len(df):,}")
    print(f"  Ejemplo clave ITER: {df['_CLAVE'].iloc[0]}")

    # ── 3. Merge ──────────────────────────────────────────────────────────────
    df_merge = df.merge(gdf_coords, on="_CLAVE", how="inner")

    print(f"  Localidades tras merge: {len(df_merge):,}")

    # Convertir variables numéricas
    for col in ["POBTOT", "TVIVHAB"]:
        if col in df_merge.columns:
            df_merge[col] = pd.to_numeric(df_merge[col], errors="coerce")

    # Filtrar población > 0 y coords válidas
    df_merge = df_merge[
        df_merge["POBTOT"].notna() &
        (df_merge["POBTOT"] > 0) &
        df_merge["_LON"].notna() &
        df_merge["_LAT"].notna()
    ].copy()

    # Renombrar coordenadas para el resto del script
    df_merge = df_merge.rename(columns={"_LON": "LONGITUD", "_LAT": "LATITUD"})

    print(f"  Localidades válidas finales: {len(df_merge):,}")
    return df_merge

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
    Genera mapa interpolado IDW recortado al límite estatal de Campeche.
    Los puntos fuera del polígono estatal se enmascaran con NaN.
    """
    import geopandas as gpd
    from shapely.ops import unary_union
    from shapely.geometry import Point
    import numpy as np

    # ── Puntos de datos ───────────────────────────────────────────────────────
    df_valido = df.dropna(subset=["LONGITUD", "LATITUD", "IVS_LOC"])
    lons = df_valido["LONGITUD"].values.astype(float)
    lats = df_valido["LATITUD"].values.astype(float)
    ivs  = df_valido["IVS_LOC"].values.astype(float)

    print(f"  Puntos: {len(lons):,} | IVS [{ivs.min():.3f}–{ivs.max():.3f}]")

    # ── Cargar shapefile y reproyectar a WGS84 ────────────────────────────────
    gdf_mun = gpd.read_file(SHP_MUN)
    if gdf_mun.crs and gdf_mun.crs.to_epsg() != 4326:
        gdf_mun = gdf_mun.to_crs(epsg=4326)

    # Polígono del estado completo (unión de municipios)
    poligono_estado = unary_union(gdf_mun.geometry)
    # ── Intersectar con tierra firme (excluye automáticamente cuerpos de agua) ─
    # En lugar de restar agua, usamos el polígono de tierra de Natural Earth.
    # Esto excluye automáticamente Laguna de Términos, mar y cualquier
    # cuerpo de agua costero o interior.
    dir_agua  = ITER_CSV.parents[3] / "01_datos_crudos" / "natural_earth_agua"
    shp_land  = dir_agua / "ne_10m_land.shp"

    if shp_land.exists():
        try:
            print("  Cargando polígono de tierra Natural Earth...")
            gdf_land = gpd.read_file(shp_land)
            if gdf_land.crs.to_epsg() != 4326:
                gdf_land = gdf_land.to_crs(epsg=4326)

            # Recortar tierra al bbox de Campeche + margen
            from shapely.geometry import box
            bbox_camp = box(
                gdf_mun.total_bounds[0] - 0.5,
                gdf_mun.total_bounds[1] - 0.5,
                gdf_mun.total_bounds[2] + 0.5,
                gdf_mun.total_bounds[3] + 0.5,
            )
            land_camp = gdf_land[gdf_land.intersects(bbox_camp)]
            tierra_union = unary_union(land_camp.geometry)

            # Intersección: tierra ∩ estado = solo tierra dentro de Campeche
            poligono_estado = poligono_estado.intersection(tierra_union)
            print("  Laguna de Términos y cuerpos de agua excluidos ✓")
        except Exception as e:
            print(f"  ⚠ Error con ne_10m_land: {e}")
            print("  Continuando con polígono estatal sin corrección de agua")
    else:
        print(f"  ⚠ ne_10m_land.shp no encontrado en {dir_agua}")
        print("  Ejecuta descargar_datos_agua.py primero")
    
    bbox = gdf_mun.total_bounds  # [minx, miny, maxx, maxy]

    lon_min, lat_min = bbox[0] - 0.05, bbox[1] - 0.05
    lon_max, lat_max = bbox[2] + 0.05, bbox[3] + 0.05

    print(f"  BBox estado: lon[{lon_min:.2f}–{lon_max:.2f}] "
          f"lat[{lat_min:.2f}–{lat_max:.2f}]")

    # ── Crear grilla ──────────────────────────────────────────────────────────
    grid_lon, grid_lat = np.meshgrid(
        np.linspace(lon_min, lon_max, GRID_RESOLUCION),
        np.linspace(lat_min, lat_max, GRID_RESOLUCION),
    )

    # ── IDW ───────────────────────────────────────────────────────────────────
    print("  Interpolando IDW...")
    grid_ivs = interpolar_idw(
        lons, lats, ivs,
        grid_lon, grid_lat,
        potencia=IDW_POTENCIA,
        vecinos=IDW_VECINOS,
    )

    # ── MÁSCARA — solo mostrar dentro del polígono estatal ────────────────────
    print("  Aplicando máscara al límite estatal (esto tarda ~20s)...")
    filas, cols = grid_lon.shape
    mascara = np.zeros((filas, cols), dtype=bool)

    for i in range(filas):
        for j in range(cols):
            punto = Point(grid_lon[i, j], grid_lat[i, j])
            mascara[i, j] = not poligono_estado.contains(punto)

    grid_ivs_masked = np.ma.masked_where(mascara, grid_ivs)
    print(f"  Celdas dentro del estado: "
          f"{(~mascara).sum():,} / {filas*cols:,}")

    # ── Escala de color por percentiles del área enmascarada ──────────────────
    valores_validos = grid_ivs_masked.compressed()
    vmin = np.percentile(valores_validos, 5)
    vmax = np.percentile(valores_validos, 95)
    print(f"  Escala p5–p95: [{vmin:.3f}–{vmax:.3f}]")

    # ── Figura ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 11))

    # Fondo del mapa (color neutro para mar/exterior)
    ax.set_facecolor("#d6eaf8")

    # Superficie interpolada enmascarada
    from matplotlib.colors import PowerNorm
    norma = PowerNorm(gamma=0.7, vmin=vmin, vmax=vmax)

    img = ax.pcolormesh(
        grid_lon, grid_lat, grid_ivs_masked,
        cmap="RdYlGn_r",
        norm=norma,
        shading="gouraud",
        zorder=2,
    )

    # Contornos municipales
    gdf_mun.boundary.plot(
        ax=ax, linewidth=0.8,
        edgecolor="white", alpha=0.8, zorder=3
    )

    # Contorno estatal grueso
    gdf_estado = gpd.GeoDataFrame(
        geometry=[poligono_estado], crs=gdf_mun.crs
    )
    gdf_estado.boundary.plot(
        ax=ax, linewidth=2.2,
        edgecolor="black", zorder=4
    )

    # Etiquetas de municipios
    ACRONIMOS_MAP = {
        "Calkiní":     "CK", "Campeche":    "CA", "Carmen":    "CR",
        "Champotón":   "CH", "Hecelchakán": "HE", "Hopelchén": "HO",
        "Palizada":    "PA", "Tenabo":       "TE", "Escárcega": "ES",
        "Calakmul":    "CL", "Candelaria":   "CN", "Seybaplaya":"SY",
    }
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
    ax.scatter(lons, lats, c="black", s=3,
               alpha=0.3, zorder=5)

    # Barra de color
    cbar = plt.colorbar(img, ax=ax, shrink=0.6, pad=0.02, aspect=20)
    cbar.set_label("Índice de Vulnerabilidad Socioterritorial (IVS)",
                   fontsize=FS_EJE)
    cbar.ax.tick_params(labelsize=FS_TICK)
    ticks = np.linspace(vmin, vmax, 5)
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([f"{v:.3f}" for v in ticks])

    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_xlabel("Longitud (°)", fontsize=FS_EJE)
    ax.set_ylabel("Latitud (°)",  fontsize=FS_EJE)
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