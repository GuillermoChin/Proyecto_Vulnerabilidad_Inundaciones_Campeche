# =============================================================================
# 06_visualizaciones.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Genera todas las figuras para publicación, figuras exploratorias
#   secundarias y un reporte TXT completo con todos los resultados
#   calculados paso a paso. Este script es autocontenido: lee el índice
#   final y produce todos los outputs visuales y textuales del proyecto.
#
#   Entrada:  02_datos_procesados/campeche_indice_final.csv
#             01_datos_crudos/2025_1_04_MUN/2025_1_04_MUN.shp
#
#   Salida (figuras publicación):
#             04_outputs/figuras/fig01_ranking_ivs.png
#             04_outputs/figuras/fig02_dimensiones_barras.png
#             04_outputs/figuras/fig03_heatmap_variables.png
#             04_outputs/mapas/fig04_mapa_cloropletico.png
#
#   Salida (figuras exploratorias):
#             04_outputs/figuras/exp01_dispersion_vs_ef.png
#             04_outputs/figuras/exp02_boxplot_variables.png
#             04_outputs/figuras/exp03_correlacion_iml_ivs.png
#             04_outputs/figuras/exp04_radar_municipios.png
#
#   Salida (reporte):
#             04_outputs/reporte_completo_ivs.txt
# =============================================================================

import sys
import warnings
import datetime
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import seaborn as sns
from pathlib import Path

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.family"] = "DejaVu Sans"

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from config import (
    DATOS_INDICE,
    SHP_MUN,
    DIR_FIGURAS,
    DIR_MAPAS,
    DIR_TABLAS,
    DPI_FIGURAS,
    FORMATO_FIG,
    PALETA_COLORES,
    NIVELES_INDICE,
    PESOS_DIMENSIONES,
    VARS_NORMALIZACION if hasattr(__import__('config'), 'VARS_NORMALIZACION')
    else None,
)

# ── Paleta de colores por nivel de vulnerabilidad ─────────────────────────────
COLORES_NIVELES = {
    "Muy Alto": "#d73027",
    "Alto":     "#f46d43",
    "Medio":    "#fdae61",
    "Bajo":     "#a6d96a",
    "Muy Bajo": "#1a9641",
}

# ── Variables normalizadas para heatmap y radar ───────────────────────────────
VARS_NORM = ["NORM_VS1", "NORM_VS2", "NORM_VS3", "NORM_VS4",
             "NORM_VS5", "NORM_EF1", "NORM_EF2", "NORM_EF3"]

ETIQUETAS_VARS = {
    "NORM_VS1": "Analfabetismo",
    "NORM_VS2": "Sin agua",
    "NORM_VS3": "Sin drenaje",
    "NORM_VS4": "Piso tierra",
    "NORM_VS5": "Sin salud",
    "NORM_EF1": "Densidad pob.",
    "NORM_EF2": "Sin electricidad",
    "NORM_EF3": "Pob. rural",
}


# =============================================================================
# CARGA DE DATOS
# =============================================================================

def cargar_indice(ruta) -> pd.DataFrame:
    """Carga la tabla del índice final generada por el script 05."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"Archivo no encontrado: {ruta}\n"
            f"Ejecuta los scripts 01 al 05 primero."
        )
    df = pd.read_csv(ruta, dtype={"CVE_MUN": str, "MUN": str})
    print(f"  Tabla del índice cargada: {len(df)} municipios")
    return df


# =============================================================================
# FIGURAS DE PUBLICACIÓN
# =============================================================================

def fig01_ranking_ivs(df: pd.DataFrame) -> None:
    """
    FIG 01 — Ranking de municipios por IVS (barras horizontales).
    Figura principal del artículo. Ordenada de mayor a menor vulnerabilidad.
    Cada barra coloreada según su nivel de vulnerabilidad.
    """
    df_plot = df.sort_values("IVS", ascending=True)
    colores  = [COLORES_NIVELES.get(str(n), "#888888")
                for n in df_plot["NIVEL_IVS"]]

    fig, ax = plt.subplots(figsize=(10, 7))

    bars = ax.barh(df_plot["NOM_MUN"], df_plot["IVS"],
                   color=colores, edgecolor="white", linewidth=0.5)

    # Etiquetas de valor al final de cada barra
    for bar, val in zip(bars, df_plot["IVS"]):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left", fontsize=8.5)

    # Leyenda de niveles
    parches = [mpatches.Patch(color=c, label=n)
               for n, c in COLORES_NIVELES.items()]
    ax.legend(handles=parches, title="Nivel de vulnerabilidad",
              loc="lower right", fontsize=8, title_fontsize=8.5)

    ax.set_xlabel("Índice de Vulnerabilidad Socioterritorial (IVS)", fontsize=10)
    ax.set_title("Índice de Vulnerabilidad Socioterritorial ante Inundaciones\n"
                 "Municipios de Campeche, México (2020)", fontsize=11, pad=12)
    ax.set_xlim(0, df["IVS"].max() + 0.08)
    ax.axvline(df["IVS"].mean(), color="gray", linestyle="--",
               linewidth=0.8, label=f"Media = {df['IVS'].mean():.3f}")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"fig01_ranking_ivs.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def fig02_dimensiones_barras(df: pd.DataFrame) -> None:
    """
    FIG 02 — Barras agrupadas: DIM_VS y DIM_EF por municipio.
    Permite ver qué dimensión domina la vulnerabilidad en cada municipio.
    """
    df_plot = df.sort_values("IVS", ascending=False)
    x       = np.arange(len(df_plot))
    ancho   = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(x - ancho/2, df_plot["DIM_VS"], ancho,
           label=f"Vulnerabilidad Social (peso {PESOS_DIMENSIONES['VS']})",
           color="#e07b54", edgecolor="white")
    ax.bar(x + ancho/2, df_plot["DIM_EF"], ancho,
           label=f"Exposición Física (peso {PESOS_DIMENSIONES['EF']})",
           color="#5b9bd5", edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(df_plot["NOM_MUN"], rotation=45,
                       ha="right", fontsize=8.5)
    ax.set_ylabel("Valor normalizado de la dimensión", fontsize=10)
    ax.set_title("Comparación de dimensiones del IVS por municipio\n"
                 "Campeche, México (2020)", fontsize=11, pad=12)
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"fig02_dimensiones_barras.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def fig03_heatmap_variables(df: pd.DataFrame) -> None:
    """
    FIG 03 — Heatmap de variables normalizadas por municipio.
    Permite identificar patrones de vulnerabilidad a nivel de variable.
    Filas = municipios ordenados por IVS, columnas = variables del índice.
    """
    cols_disp = [c for c in VARS_NORM if c in df.columns]
    df_plot   = df.sort_values("IVS", ascending=False).set_index("NOM_MUN")
    matriz    = df_plot[cols_disp].rename(columns=ETIQUETAS_VARS)

    fig, ax = plt.subplots(figsize=(11, 7))

    sns.heatmap(
        matriz,
        annot=True,
        fmt=".2f",
        cmap=PALETA_COLORES,
        linewidths=0.4,
        linecolor="white",
        vmin=0, vmax=1,
        ax=ax,
        cbar_kws={"label": "Valor normalizado [0–1]", "shrink": 0.8},
        annot_kws={"size": 8},
    )

    ax.set_title("Variables normalizadas del IVS por municipio\n"
                 "Campeche, México (2020)", fontsize=11, pad=12)
    ax.set_xlabel("Variable del índice", fontsize=10)
    ax.set_ylabel("Municipio (ordenado por IVS)", fontsize=10)
    ax.tick_params(axis="x", rotation=30, labelsize=8.5)
    ax.tick_params(axis="y", rotation=0,  labelsize=8.5)

    # Línea divisoria entre dimensiones VS y EF
    n_vs = sum(1 for c in cols_disp if "VS" in c)
    ax.axvline(x=n_vs, color="black", linewidth=1.5, linestyle="--")
    ax.text(n_vs / 2, -0.6, "Dim. VS", ha="center",
            fontsize=8.5, color="#c0392b", fontweight="bold",
            transform=ax.get_xaxis_transform())
    ax.text(n_vs + (len(cols_disp) - n_vs) / 2, -0.6, "Dim. EF",
            ha="center", fontsize=8.5, color="#2980b9", fontweight="bold",
            transform=ax.get_xaxis_transform())

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"fig03_heatmap_variables.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def fig04_mapa_cloropletico(df: pd.DataFrame) -> None:
    """
    FIG 04 — Mapa coroplético del IVS por municipio.
    Requiere geopandas y el shapefile de municipios de Campeche.
    Si geopandas no está instalado o el shapefile no existe, se omite.
    """
    try:
        import geopandas as gpd
    except ImportError:
        print("  ⚠ geopandas no instalado — mapa omitido")
        print("    Instala con: pip install geopandas")
        return

    if not SHP_MUN.exists():
        print(f"  ⚠ Shapefile no encontrado: {SHP_MUN} — mapa omitido")
        return

    gdf = gpd.read_file(SHP_MUN)

    # Estandarizar clave municipal para el join
    if "CVEGEO" in gdf.columns:
        gdf["CVE_MUN"] = gdf["CVEGEO"].str[-3:]
    elif "CVE_MUN" not in gdf.columns:
        print("  ⚠ No se encontró columna de clave municipal en el shapefile")
        return

    df["CVE_MUN"] = df["CVE_MUN"].astype(str).str.zfill(3)
    gdf = gdf.merge(df[["CVE_MUN", "IVS", "NIVEL_IVS", "NOM_MUN"]],
                    on="CVE_MUN", how="left")

    fig, ax = plt.subplots(figsize=(10, 9))

    gdf.plot(
        column="IVS",
        cmap=PALETA_COLORES,
        linewidth=0.5,
        edgecolor="white",
        legend=True,
        legend_kwds={
            "label": "Índice de Vulnerabilidad Socioterritorial (IVS)",
            "orientation": "horizontal",
            "shrink": 0.7,
            "pad": 0.02,
        },
        ax=ax,
        missing_kwds={"color": "#cccccc", "label": "Sin datos"},
    )

    # Etiquetas de municipio en el centroide
    for _, row in gdf.iterrows():
        if row.geometry and not pd.isna(row.get("IVS", None)):
            centroide = row.geometry.centroid
            ax.annotate(
                row["NOM_MUN"],
                xy=(centroide.x, centroide.y),
                ha="center", va="center",
                fontsize=6.5, color="black",
                fontweight="bold",
            )

    ax.set_title("Índice de Vulnerabilidad Socioterritorial ante Inundaciones\n"
                 "Municipios de Campeche, México (2020)", fontsize=11, pad=12)
    ax.set_axis_off()

    plt.tight_layout()
    ruta = DIR_MAPAS / f"fig04_mapa_cloropletico.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


# =============================================================================
# FIGURAS EXPLORATORIAS SECUNDARIAS
# =============================================================================

def exp01_dispersion_vs_ef(df: pd.DataFrame) -> None:
    """
    EXP 01 — Dispersión DIM_VS vs DIM_EF.
    Identifica municipios donde ambas dimensiones coinciden o divergen.
    """
    colores = [COLORES_NIVELES.get(str(n), "#888") for n in df["NIVEL_IVS"]]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df["DIM_EF"], df["DIM_VS"], c=colores, s=100,
               edgecolors="white", linewidth=0.8, zorder=3)

    for _, row in df.iterrows():
        ax.annotate(row["NOM_MUN"], (row["DIM_EF"], row["DIM_VS"]),
                    textcoords="offset points", xytext=(5, 3),
                    fontsize=7, color="#333333")

    # Línea diagonal de referencia (VS = EF)
    lim = max(df["DIM_VS"].max(), df["DIM_EF"].max()) + 0.05
    ax.plot([0, lim], [0, lim], "--", color="gray",
            linewidth=0.8, label="VS = EF")

    parches = [mpatches.Patch(color=c, label=n)
               for n, c in COLORES_NIVELES.items()]
    ax.legend(handles=parches, fontsize=8, title="Nivel IVS",
              title_fontsize=8.5, loc="upper left")

    ax.set_xlabel("Dimensión Exposición Física (DIM_EF)", fontsize=10)
    ax.set_ylabel("Dimensión Vulnerabilidad Social (DIM_VS)", fontsize=10)
    ax.set_title("Relación entre dimensiones del IVS\nMunicipios de Campeche",
                 fontsize=11, pad=10)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp01_dispersion_vs_ef.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def exp02_boxplot_variables(df: pd.DataFrame) -> None:
    """
    EXP 02 — Boxplot de todas las variables normalizadas.
    Muestra la dispersión de cada variable entre los 13 municipios.
    Útil para identificar variables con mayor variabilidad explicativa.
    """
    cols_disp = [c for c in VARS_NORM if c in df.columns]
    df_melt   = df[cols_disp].rename(columns=ETIQUETAS_VARS).melt(
        var_name="Variable", value_name="Valor normalizado"
    )

    fig, ax = plt.subplots(figsize=(11, 5))

    sns.boxplot(
        data=df_melt, x="Variable", y="Valor normalizado",
        palette="Set2", width=0.5, linewidth=0.8,
        flierprops=dict(marker="o", markersize=5,
                        markerfacecolor="gray", alpha=0.6),
        ax=ax,
    )

    ax.axhline(0.5, color="gray", linestyle="--",
               linewidth=0.7, label="Punto medio (0.5)")
    ax.set_title("Distribución de variables normalizadas (N=13 municipios)\n"
                 "Campeche, México (2020)", fontsize=11, pad=10)
    ax.set_xlabel("")
    ax.set_ylabel("Valor normalizado [0–1]", fontsize=10)
    ax.tick_params(axis="x", rotation=30, labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp02_boxplot_variables.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def exp03_correlacion_iml_ivs(df: pd.DataFrame) -> None:
    """
    EXP 03 — Correlación entre IML_MUNICIPAL (CONAPO) e IVS calculado.
    Sirve como validación externa del índice: si correlacionan bien,
    el IVS es consistente con una medida independiente de marginación.
    """
    if "IML_MUNICIPAL" not in df.columns:
        print("  ⚠ IML_MUNICIPAL no disponible — exp03 omitida")
        return

    corr = df["IML_MUNICIPAL"].corr(df["IVS"])
    colores = [COLORES_NIVELES.get(str(n), "#888") for n in df["NIVEL_IVS"]]

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(df["IML_MUNICIPAL"], df["IVS"], c=colores,
               s=90, edgecolors="white", linewidth=0.7, zorder=3)

    for _, row in df.iterrows():
        ax.annotate(row["NOM_MUN"],
                    (row["IML_MUNICIPAL"], row["IVS"]),
                    textcoords="offset points", xytext=(5, 3),
                    fontsize=7, color="#333333")

    # Línea de tendencia
    m, b = np.polyfit(df["IML_MUNICIPAL"], df["IVS"], 1)
    x_line = np.linspace(df["IML_MUNICIPAL"].min(),
                         df["IML_MUNICIPAL"].max(), 100)
    ax.plot(x_line, m * x_line + b, color="gray",
            linestyle="--", linewidth=1, label=f"r = {corr:.3f}")

    ax.set_xlabel("Índice de Marginación Municipal (CONAPO 2020)", fontsize=10)
    ax.set_ylabel("Índice de Vulnerabilidad Socioterritorial (IVS)", fontsize=10)
    ax.set_title("Validación externa: IML CONAPO vs IVS calculado\n"
                 "Municipios de Campeche, México", fontsize=11, pad=10)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp03_correlacion_iml_ivs.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def exp04_radar_municipios(df: pd.DataFrame) -> None:
    """
    EXP 04 — Gráfica de radar (spider) para los 3 municipios con mayor
    y menor IVS. Muestra el perfil de vulnerabilidad por variable.
    """
    cols_disp = [c for c in VARS_NORM if c in df.columns]
    etiquetas = [ETIQUETAS_VARS.get(c, c) for c in cols_disp]
    N         = len(cols_disp)
    angulos   = [n / float(N) * 2 * np.pi for n in range(N)]
    angulos  += angulos[:1]  # Cerrar el polígono

    # Seleccionar top 3 más vulnerables y top 3 menos vulnerables
    top3    = df.nlargest(3,  "IVS")
    bottom3 = df.nsmallest(3, "IVS")
    seleccion = pd.concat([top3, bottom3])

    colores_radar = ["#d73027", "#f46d43", "#fdae61",
                     "#a6d96a", "#66bd63", "#1a9641"]

    fig, ax = plt.subplots(figsize=(8, 8),
                            subplot_kw=dict(polar=True))

    for i, (_, row) in enumerate(seleccion.iterrows()):
        valores  = [row[c] if c in row.index else 0 for c in cols_disp]
        valores += valores[:1]
        ax.plot(angulos, valores, "o-", linewidth=1.5,
                color=colores_radar[i], label=row["NOM_MUN"], markersize=4)
        ax.fill(angulos, valores, alpha=0.08, color=colores_radar[i])

    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(etiquetas, size=8.5)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], size=7)
    ax.set_title("Perfil de vulnerabilidad — Top 3 vs Bottom 3\n"
                 "Municipios de Campeche, México", pad=20, fontsize=11)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1),
              fontsize=8.5, title="Municipio", title_fontsize=9)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp04_radar_municipios.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


# =============================================================================
# REPORTE TXT COMPLETO
# =============================================================================

def generar_reporte(df: pd.DataFrame) -> None:
    """
    Genera un reporte TXT exhaustivo con absolutamente todo lo calculado:
    metadatos, estadísticas descriptivas, valores por variable, dimensiones,
    índice compuesto, ranking, clasificación, correlaciones y notas
    metodológicas. Sirve como bitácora permanente del análisis.
    """
    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_TABLAS / "reporte_completo_ivs.txt"
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cols_norm = [c for c in VARS_NORM if c in df.columns]
    cols_prop = [c for c in df.columns if c.startswith("PROP_")]

    with open(ruta, "w", encoding="utf-8") as f:

        def linea(char="=", n=70):
            f.write(char * n + "\n")

        def titulo(texto):
            linea()
            f.write(f"  {texto}\n")
            linea()

        def subtitulo(texto):
            f.write(f"\n{'-'*70}\n")
            f.write(f"  {texto}\n")
            f.write(f"{'-'*70}\n")

        # ── Encabezado ────────────────────────────────────────────────────────
        titulo("REPORTE COMPLETO — ÍNDICE DE VULNERABILIDAD SOCIOTERRITORIAL")
        f.write(f"  Proyecto: Inundaciones Campeche, México\n")
        f.write(f"  Generado: {ahora}\n")
        f.write(f"  Autores:  Guillermo Adrián Chin Canché (ITESCAM)\n")
        f.write(f"            Javier Pan Barcel (UAC-EPOMEX)\n")
        f.write(f"            [Nombre Katia] [Apellido Katia] ([Institución])\n")
        f.write(f"  Fuentes:  ITER Censo 2020 (INEGI) + IML 2020 (CONAPO)\n")
        linea()

        # ── 1. Parámetros del análisis ────────────────────────────────────────
        subtitulo("1. PARÁMETROS DEL ANÁLISIS")
        f.write(f"  Entidad federativa:  Campeche (clave 04)\n")
        f.write(f"  N municipios:        {len(df)}\n")
        f.write(f"  Método:              Promedio ponderado + normalización min-max\n")
        f.write(f"  Peso DIM_VS:         {PESOS_DIMENSIONES['VS']} "
                f"(Vulnerabilidad Social)\n")
        f.write(f"  Peso DIM_EF:         {PESOS_DIMENSIONES['EF']} "
                f"(Exposición Física)\n")
        f.write(f"  Variables VS:        VS1-VS5 (5 variables)\n")
        f.write(f"  Variables EF:        EF1-EF3 (3 variables)\n")
        f.write(f"  Total variables:     8\n")
        f.write(f"  Niveles IVS:         {' | '.join(NIVELES_INDICE)}\n")

        # ── 2. Estadísticas descriptivas por variable normalizada ─────────────
        subtitulo("2. ESTADÍSTICAS DESCRIPTIVAS — VARIABLES NORMALIZADAS [0–1]")
        f.write(f"\n  {'Variable':<12} {'Etiqueta':<22} {'Min':>7} {'Max':>7} "
                f"{'Media':>8} {'Mediana':>9} {'Desv.':>8} {'CV':>7}\n")
        f.write(f"  {'-'*80}\n")
        for col in cols_norm:
            etiq = ETIQUETAS_VARS.get(col, col)
            s    = df[col]
            cv   = (s.std() / s.mean() * 100) if s.mean() != 0 else 0
            f.write(
                f"  {col:<12} {etiq:<22} {s.min():>7.4f} {s.max():>7.4f} "
                f"{s.mean():>8.4f} {s.median():>9.4f} {s.std():>8.4f} "
                f"{cv:>6.1f}%\n"
            )

        # ── 3. Estadísticas descriptivas — proporciones originales ────────────
        if cols_prop:
            subtitulo("3. ESTADÍSTICAS DESCRIPTIVAS — PROPORCIONES ORIGINALES")
            f.write(f"\n  {'Variable':<22} {'Min':>8} {'Max':>8} "
                    f"{'Media':>9} {'Mediana':>10} {'Desv.':>9}\n")
            f.write(f"  {'-'*72}\n")
            for col in cols_prop:
                s = df[col]
                f.write(
                    f"  {col:<22} {s.min():>8.4f} {s.max():>8.4f} "
                    f"{s.mean():>9.4f} {s.median():>10.4f} "
                    f"{s.std():>9.4f}\n"
                )

        # ── 4. Valores normalizados por municipio ─────────────────────────────
        subtitulo("4. VALORES NORMALIZADOS POR MUNICIPIO")
        encabezado = f"  {'Municipio':<30} " + \
                     " ".join(f"{c:<10}" for c in cols_norm)
        f.write(encabezado + "\n")
        f.write(f"  {'-'*90}\n")
        for _, row in df.sort_values("IVS", ascending=False).iterrows():
            vals = " ".join(f"{row[c]:>10.4f}" if c in row.index
                            else f"{'N/D':>10}" for c in cols_norm)
            f.write(f"  {row['NOM_MUN']:<30} {vals}\n")

        # ── 5. Dimensiones por municipio ──────────────────────────────────────
        subtitulo("5. VALORES DE DIMENSIONES POR MUNICIPIO")
        f.write(f"\n  {'Municipio':<30} {'DIM_VS':>10} {'DIM_EF':>10} "
                f"{'IVS':>10} {'Nivel':<12} {'Ranking':>8}\n")
        f.write(f"  {'-'*84}\n")
        for _, row in df.sort_values("IVS", ascending=False).iterrows():
            f.write(
                f"  {row['NOM_MUN']:<30} {row['DIM_VS']:>10.4f} "
                f"{row['DIM_EF']:>10.4f} {row['IVS']:>10.4f} "
                f"{str(row['NIVEL_IVS']):<12} {int(row['RANKING']):>8}\n"
            )

        # ── 6. Ranking final completo ─────────────────────────────────────────
        subtitulo("6. RANKING FINAL DE VULNERABILIDAD (mayor a menor IVS)")
        f.write(f"\n  {'#':<5} {'Municipio':<30} {'IVS':>8} "
                f"{'Nivel':<12} {'DIM_VS':>9} {'DIM_EF':>9}")
        if "IML_MUNICIPAL" in df.columns:
            f.write(f" {'IML':>9}")
        if "GM_MUNICIPAL" in df.columns:
            f.write(f"  {'Grado marg.'}")
        f.write("\n")
        f.write(f"  {'-'*90}\n")

        for _, row in df.sort_values("IVS", ascending=False).iterrows():
            f.write(
                f"  {int(row['RANKING']):<5} {row['NOM_MUN']:<30} "
                f"{row['IVS']:>8.4f} {str(row['NIVEL_IVS']):<12} "
                f"{row['DIM_VS']:>9.4f} {row['DIM_EF']:>9.4f}"
            )
            if "IML_MUNICIPAL" in df.columns:
                f.write(f" {row['IML_MUNICIPAL']:>9.4f}")
            if "GM_MUNICIPAL" in df.columns:
                f.write(f"  {row['GM_MUNICIPAL']}")
            f.write("\n")

        # ── 7. Distribución por niveles ───────────────────────────────────────
        subtitulo("7. DISTRIBUCIÓN POR NIVEL DE VULNERABILIDAD")
        conteo = df["NIVEL_IVS"].value_counts()
        for nivel in NIVELES_INDICE:
            n     = conteo.get(nivel, 0)
            pct   = n / len(df) * 100
            barra = "█" * n
            f.write(f"  {nivel:<12} {barra:<15} {n} municipios ({pct:.1f}%)\n")

        # ── 8. Correlaciones entre variables ──────────────────────────────────
        subtitulo("8. MATRIZ DE CORRELACIONES — VARIABLES NORMALIZADAS")
        if len(cols_norm) > 1:
            corr_mat = df[cols_norm].rename(
                columns={c: ETIQUETAS_VARS.get(c, c) for c in cols_norm}
            ).corr().round(3)
            f.write("\n")
            f.write(corr_mat.to_string())
            f.write("\n")

        # ── 9. Correlación IML vs IVS ─────────────────────────────────────────
        if "IML_MUNICIPAL" in df.columns:
            subtitulo("9. VALIDACIÓN EXTERNA — CORRELACIÓN IML (CONAPO) vs IVS")
            corr_val = df["IML_MUNICIPAL"].corr(df["IVS"])
            corr_vs  = df["IML_MUNICIPAL"].corr(df["DIM_VS"])
            corr_ef  = df["IML_MUNICIPAL"].corr(df["DIM_EF"])
            f.write(f"  Pearson IML vs IVS:    r = {corr_val:.4f}\n")
            f.write(f"  Pearson IML vs DIM_VS: r = {corr_vs:.4f}\n")
            f.write(f"  Pearson IML vs DIM_EF: r = {corr_ef:.4f}\n")
            interpretacion = (
                "Muy alta" if abs(corr_val) >= 0.8 else
                "Alta"     if abs(corr_val) >= 0.6 else
                "Moderada" if abs(corr_val) >= 0.4 else
                "Baja"
            )
            f.write(f"  Interpretación:        Correlación {interpretacion} "
                    f"entre IML y IVS\n")
            f.write(f"  Nota: Con N=13 interpretar con cautela (p-value "
                    f"no calculado aquí)\n")

        # ── 10. Notas metodológicas ───────────────────────────────────────────
        subtitulo("10. NOTAS METODOLÓGICAS")
        f.write(
            "  - Normalización: min-max por variable, rango [0,1].\n"
            "    0 = municipio con menor valor (menor vulnerabilidad).\n"
            "    1 = municipio con mayor valor (mayor vulnerabilidad).\n\n"
            "  - Si todos los valores de una variable son iguales,\n"
            "    se asigna 0.5 a todos los municipios (neutralidad).\n\n"
            "  - DIM_VS = promedio simple de NORM_VS1 a NORM_VS5.\n"
            "  - DIM_EF = promedio simple de NORM_EF1 a NORM_EF3.\n"
            "  - IVS    = DIM_VS × 0.6 + DIM_EF × 0.4.\n\n"
            "  - Clasificación en niveles: quintiles del IVS.\n"
            "    Con N=13 los quintiles no son perfectamente iguales.\n\n"
            "  - Valores atípicos detectados pero NO eliminados (N=13).\n"
            "    Se recomienda discutir en el artículo.\n\n"
            "  - PLOCRUG no es variable estándar del ITER; si no existe\n"
            "    en el archivo, EF3 se omite del cálculo.\n\n"
            "  - Marco de referencia: Marco de Sendai para la Reducción\n"
            "    del Riesgo de Desastres 2015-2030.\n"
        )

        # ── Pie del reporte ───────────────────────────────────────────────────
        linea()
        f.write(f"  Fin del reporte — generado el {ahora}\n")
        linea()

    print(f"  Reporte TXT guardado: {ruta.name}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SCRIPT 06 — Visualizaciones y reporte completo")
    print("=" * 60)

    # Crear directorios de salida si no existen
    for d in [DIR_FIGURAS, DIR_MAPAS, DIR_TABLAS]:
        d.mkdir(parents=True, exist_ok=True)

    # Cargar datos
    df = cargar_indice(DATOS_INDICE)

    # ── Figuras de publicación ────────────────────────────────────────────────
    print("\n  [Figuras de publicación]")
    fig01_ranking_ivs(df)
    fig02_dimensiones_barras(df)
    fig03_heatmap_variables(df)
    fig04_mapa_cloropletico(df)

    # ── Figuras exploratorias ─────────────────────────────────────────────────
    print("\n  [Figuras exploratorias]")
    exp01_dispersion_vs_ef(df)
    exp02_boxplot_variables(df)
    exp03_correlacion_iml_ivs(df)
    exp04_radar_municipios(df)

    # ── Reporte TXT completo ──────────────────────────────────────────────────
    print("\n  [Reporte completo]")
    generar_reporte(df)

    print("\n✓ Script 06 completado exitosamente")
    print(f"  Figuras en:  {DIR_FIGURAS}")
    print(f"  Mapa en:     {DIR_MAPAS}")
    print(f"  Reporte en:  {DIR_TABLAS}\n")


if __name__ == "__main__":
    main()