# =============================================================================
# 06_visualizaciones.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  1.1.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Genera todas las figuras para publicación, figuras exploratorias
#   secundarias y un reporte TXT completo con todos los resultados.
#
#   NOTA METODOLÓGICA — DZITBALCHÉ:
#   El municipio de Dzitbalché fue creado recientemente por segregación
#   del municipio de Calkiní. El Censo de Población y Vivienda 2020
#   (INEGI) y el IML 2020 (CONAPO) no registran a Dzitbalché como
#   municipio independiente, por lo que sus datos están incluidos dentro
#   de los valores correspondientes a Calkiní. Esta situación debe
#   señalarse explícitamente en el apartado de limitaciones del artículo.
#
#   Entrada:  02_datos_procesados/campeche_indice_final.csv
#             01_datos_crudos/2025_1_04_MUN/2025_1_04_MUN.shp
# =============================================================================

import sys
import warnings
import datetime
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
)

# ── Tamaños de fuente globales ────────────────────────────────────────────────
FS_TITULO     = 15    # Títulos de figura
FS_SUBTITULO  = 13    # Subtítulos
FS_EJE        = 12    # Etiquetas de ejes
FS_TICK       = 11    # Valores en ejes
FS_LEYENDA    = 11    # Leyendas
FS_ANOTACION  = 10    # Valores sobre barras y puntos
FS_ETIQUETA   = 11    # Etiquetas de municipios en gráficas

# ── Corrección de nombres de municipios (encoding) ───────────────────────────
NOMBRES_CORRECTOS = {
    "CalkinÃ\xad":    "Calkiní",
    "CalkinÃ­":       "Calkiní",
    "ChampotÃ³n":     "Champotón",
    "HecelchakÃ¡n":   "Hecelchakán",
    "HopelchÃ©n":     "Hopelchén",
    "EscÃ¡rcega":     "Escárcega",
    "Calkin\xed":     "Calkiní",
    "Champot\xf3n":   "Champotón",
    "Hecelchak\xe1n": "Hecelchakán",
    "Hopelch\xe9n":   "Hopelchén",
    "Esc\xe1rcega":   "Escárcega",
}

# ── Acrónimos de 2 letras por municipio ──────────────────────────────────────
# Usados en etiquetas de gráficas para evitar solapamiento
# Se aclara la tabla completa en el artículo
ACRONIMOS = {
    "Calkiní":     "CK",
    "Campeche":    "CA",
    "Carmen":      "CR",
    "Champotón":   "CH",
    "Hecelchakán": "HE",
    "Hopelchén":   "HO",
    "Palizada":    "PA",
    "Tenabo":      "TE",
    "Escárcega":   "ES",
    "Calakmul":    "CL",
    "Candelaria":  "CN",
    "Seybaplaya":  "SY",
}

# ── Nota sobre Dzitbalché ─────────────────────────────────────────────────────
NOTA_DZITBALCHE = (
    "* Los datos de Calkiní (CK) incluyen al municipio de Dzitbalché,\n"
    "  creado recientemente por segregación y no registrado en el Censo 2020."
)

# ── Paleta de colores por nivel ───────────────────────────────────────────────
COLORES_NIVELES = {
    "Muy Alto": "#d73027",
    "Alto":     "#f46d43",
    "Medio":    "#fdae61",
    "Bajo":     "#a6d96a",
    "Muy Bajo": "#1a9641",
}

# ── Variables normalizadas ────────────────────────────────────────────────────
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
    "NORM_EF3": "Sin bienes",
}

# ── Paleta de colores por variable (para radar invertido) ─────────────────────
COLORES_VARS = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#a65628", "#f781bf", "#999999"
]


# =============================================================================
# UTILIDADES
# =============================================================================

def corregir_nombres(df: pd.DataFrame) -> pd.DataFrame:
    """
    Corrige nombres de municipios con problemas de encoding.
    Solo aplica el diccionario de reemplazos — no intenta re-encodear
    porque el CSV ya fue guardado con los bytes tal como están.
    """
    df = df.copy()
    df["NOM_MUN"] = df["NOM_MUN"].replace(NOMBRES_CORRECTOS)
    # Corrección adicional byte a byte para residuos latin-1
    def limpiar(nombre):
        if not isinstance(nombre, str):
            return nombre
        try:
            return nombre.encode("raw_unicode_escape").decode("latin-1")
        except Exception:
            return nombre
    df["NOM_MUN"] = df["NOM_MUN"].apply(limpiar)
    return df


def agregar_acronimo(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columna ACR con el acrónimo de 2 letras de cada municipio."""
    df = df.copy()
    df["ACR"] = df["NOM_MUN"].map(ACRONIMOS).fillna(
        df["NOM_MUN"].str[:2].str.upper()
    )
    return df


def cargar_indice(ruta) -> pd.DataFrame:
    """Carga, corrige nombres y agrega acrónimos al índice final."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"Archivo no encontrado: {ruta}\n"
            f"Ejecuta los scripts 01 al 05 primero."
        )
    df = pd.read_csv(ruta, dtype={"CVE_MUN": str, "MUN": str})
    df = corregir_nombres(df)
    df = agregar_acronimo(df)
    print(f"  Tabla del índice cargada: {len(df)} municipios")
    print(f"  Municipios: {df['NOM_MUN'].tolist()}")
    return df


# =============================================================================
# FIGURAS DE PUBLICACIÓN
# =============================================================================

def fig01_ranking_ivs(df: pd.DataFrame) -> None:
    """
    FIG 01 — Ranking de municipios por IVS (barras horizontales).
    Usa nombres completos en el eje Y. Nota sobre Dzitbalché al pie.
    """
    df_plot = df.sort_values("IVS", ascending=True)
    colores  = [COLORES_NIVELES.get(str(n), "#888888")
                for n in df_plot["NIVEL_IVS"]]

    fig, ax = plt.subplots(figsize=(12, 8))

    bars = ax.barh(df_plot["NOM_MUN"], df_plot["IVS"],
                   color=colores, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, df_plot["IVS"]):
        ax.text(bar.get_width() + 0.005,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left",
                fontsize=FS_ANOTACION)

    parches = [mpatches.Patch(color=c, label=n)
               for n, c in COLORES_NIVELES.items()]
    ax.legend(handles=parches, title="Nivel de vulnerabilidad",
              loc="lower right", fontsize=FS_LEYENDA,
              title_fontsize=FS_LEYENDA)

    ax.set_xlabel("Índice de Vulnerabilidad Socioterritorial (IVS)",
                  fontsize=FS_EJE)
    ax.set_title(
        "Índice de Vulnerabilidad Socioterritorial ante Inundaciones\n"
        "Municipios de Campeche, México (2020)",
        fontsize=FS_TITULO, pad=14)
    ax.set_xlim(0, df["IVS"].max() + 0.10)
    ax.axvline(df["IVS"].mean(), color="gray", linestyle="--",
               linewidth=0.9, label=f"Media = {df['IVS'].mean():.3f}")
    ax.tick_params(axis="both", labelsize=FS_TICK)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    ruta = DIR_FIGURAS / f"fig01_ranking_ivs.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def fig02_dimensiones_barras(df: pd.DataFrame) -> None:
    """
    FIG 02 — Barras agrupadas DIM_VS y DIM_EF.
    Usa acrónimos en eje X para evitar solapamiento.
    """
    df_plot = df.sort_values("IVS", ascending=False)
    x       = np.arange(len(df_plot))
    ancho   = 0.35

    fig, ax = plt.subplots(figsize=(13, 7))

    ax.bar(x - ancho/2, df_plot["DIM_VS"], ancho,
           label=f"Vulnerabilidad Social (peso {PESOS_DIMENSIONES['VS']})",
           color="#e07b54", edgecolor="white")
    ax.bar(x + ancho/2, df_plot["DIM_EF"], ancho,
           label=f"Exposición Física (peso {PESOS_DIMENSIONES['EF']})",
           color="#5b9bd5", edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(df_plot["ACR"], rotation=0,
                       ha="center", fontsize=FS_TICK + 1)
    ax.set_ylabel("Valor normalizado de la dimensión", fontsize=FS_EJE)
    ax.set_title(
        "Comparación de dimensiones del IVS por municipio\n"
        "Campeche, México (2020)",
        fontsize=FS_TITULO, pad=14)
    ax.legend(fontsize=FS_LEYENDA)
    ax.set_ylim(0, 1.10)
    ax.tick_params(axis="y", labelsize=FS_TICK)
    ax.spines[["top", "right"]].set_visible(False)

    # Tabla de acrónimos al pie
    plt.tight_layout()
    ruta = DIR_FIGURAS / f"fig02_dimensiones_barras.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def fig03_heatmap_variables(df: pd.DataFrame) -> None:
    """
    FIG 03 — Heatmap de variables normalizadas por municipio.
    Usa nombres completos en filas.
    """
    cols_disp = [c for c in VARS_NORM if c in df.columns]
    df_plot   = df.sort_values("IVS", ascending=False).set_index("NOM_MUN")
    matriz    = df_plot[cols_disp].rename(columns=ETIQUETAS_VARS)

    fig, ax = plt.subplots(figsize=(13, 8))

    sns.heatmap(
        matriz,
        annot=True, fmt=".2f",
        cmap=PALETA_COLORES,
        linewidths=0.4, linecolor="white",
        vmin=0, vmax=1, ax=ax,
        cbar_kws={"label": "Valor normalizado [0–1]", "shrink": 0.8},
        annot_kws={"size": FS_ANOTACION},
    )

    ax.set_title(
        "Variables normalizadas del IVS por municipio\n"
        "Campeche, México (2020)",
        fontsize=FS_TITULO, pad=14)
    ax.set_xlabel("Variable del índice", fontsize=FS_EJE)
    ax.set_ylabel("Municipio (ordenado por IVS)", fontsize=FS_EJE)
    ax.tick_params(axis="x", rotation=30, labelsize=FS_TICK)
    ax.tick_params(axis="y", rotation=0,  labelsize=FS_TICK)

    n_vs = sum(1 for c in cols_disp if "VS" in c)
    ax.axvline(x=n_vs, color="black", linewidth=1.8, linestyle="--")
    ax.text(n_vs / 2, -0.7, "Dim. VS", ha="center",
            fontsize=FS_EJE, color="#c0392b", fontweight="bold",
            transform=ax.get_xaxis_transform())
    ax.text(n_vs + (len(cols_disp) - n_vs) / 2, -0.7, "Dim. EF",
            ha="center", fontsize=FS_EJE, color="#2980b9", fontweight="bold",
            transform=ax.get_xaxis_transform())
    plt.tight_layout()
    ruta = DIR_FIGURAS / f"fig03_heatmap_variables.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def fig04_mapa_cloropletico(df: pd.DataFrame) -> None:
    """
    FIG 04 — Mapa coroplético del IVS.
    Etiquetas con acrónimos para evitar solapamiento.
    Nota sobre Dzitbalché en el pie del mapa.
    """
    try:
        import geopandas as gpd
    except ImportError:
        print("  ⚠ geopandas no instalado — mapa omitido")
        return

    if not SHP_MUN.exists():
        print(f"  ⚠ Shapefile no encontrado — mapa omitido")
        return

    gdf = gpd.read_file(SHP_MUN)

    if "CVEGEO" in gdf.columns:
        gdf["CVE_MUN"] = gdf["CVEGEO"].str[-3:]
    elif "CVE_MUN" not in gdf.columns:
        print("  ⚠ No se encontró clave municipal en shapefile")
        return

    df["CVE_MUN"] = df["CVE_MUN"].astype(str).str.zfill(3)
    gdf = gdf.merge(
        df[["CVE_MUN", "IVS", "NIVEL_IVS", "NOM_MUN", "ACR"]],
        on="CVE_MUN", how="left"
    )

    fig, ax = plt.subplots(figsize=(11, 10))

    gdf.plot(
        column="IVS", cmap=PALETA_COLORES,
        linewidth=0.6, edgecolor="white",
        legend=True,
        legend_kwds={
            "label": "Índice de Vulnerabilidad Socioterritorial (IVS)",
            "orientation": "horizontal", "shrink": 0.65, "pad": 0.02,
        },
        ax=ax,
        missing_kwds={"color": "#cccccc", "label": "Sin datos"},
    )

    # Etiquetas con acrónimos en centroide
    for _, row in gdf.iterrows():
        if row.geometry and not pd.isna(row.get("IVS", None)):
            c = row.geometry.centroid
            ax.annotate(
                row["ACR"],
                xy=(c.x, c.y), ha="center", va="center",
                fontsize=FS_ETIQUETA + 1, color="black", fontweight="bold",
            )

    ax.set_title(
        "Índice de Vulnerabilidad Socioterritorial ante Inundaciones\n"
        "Municipios de Campeche, México (2020)",
        fontsize=FS_TITULO, pad=14)
    ax.set_axis_off()

    # Tabla de acrónimos
    plt.tight_layout()
    ruta = DIR_MAPAS / f"fig04_mapa_cloropletico.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


# =============================================================================
# FIGURAS EXPLORATORIAS
# =============================================================================

def exp01_dispersion_vs_ef(df: pd.DataFrame) -> None:
    """EXP 01 — Dispersión DIM_VS vs DIM_EF con acrónimos."""
    colores = [COLORES_NIVELES.get(str(n), "#888") for n in df["NIVEL_IVS"]]

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(df["DIM_EF"], df["DIM_VS"], c=colores, s=120,
               edgecolors="white", linewidth=0.8, zorder=3)

    for _, row in df.iterrows():
        ax.annotate(row["ACR"],
                    (row["DIM_EF"], row["DIM_VS"]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=FS_ETIQUETA, color="#222222", fontweight="bold")

    lim = max(df["DIM_VS"].max(), df["DIM_EF"].max()) + 0.07
    ax.plot([0, lim], [0, lim], "--", color="gray",
            linewidth=0.9, label="VS = EF")

    parches = [mpatches.Patch(color=c, label=n)
               for n, c in COLORES_NIVELES.items()]
    ax.legend(handles=parches, fontsize=FS_LEYENDA,
              title="Nivel IVS", title_fontsize=FS_LEYENDA)

    ax.set_xlabel("Dimensión Exposición Física (DIM_EF)", fontsize=FS_EJE)
    ax.set_ylabel("Dimensión Vulnerabilidad Social (DIM_VS)", fontsize=FS_EJE)
    ax.set_title("Relación entre dimensiones del IVS\nMunicipios de Campeche",
                 fontsize=FS_TITULO, pad=12)
    ax.tick_params(labelsize=FS_TICK)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.spines[["top", "right"]].set_visible(False)

    # Tabla de acrónimos y nota
    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp01_dispersion_vs_ef.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def exp02_boxplot_variables(df: pd.DataFrame) -> None:
    """EXP 02 — Boxplot de variables normalizadas."""
    cols_disp = [c for c in VARS_NORM if c in df.columns]
    df_melt   = df[cols_disp].rename(columns=ETIQUETAS_VARS).melt(
        var_name="Variable", value_name="Valor normalizado"
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=df_melt, x="Variable", y="Valor normalizado",
        palette="Set2", width=0.5, linewidth=0.9,
        flierprops=dict(marker="o", markersize=6,
                        markerfacecolor="gray", alpha=0.6),
        ax=ax,
    )
    ax.axhline(0.5, color="gray", linestyle="--",
               linewidth=0.8, label="Punto medio (0.5)")
    ax.set_title(
        "Distribución de variables normalizadas (N=12 municipios)\n"
        "Campeche, México (2020)",
        fontsize=FS_TITULO, pad=12)
    ax.set_xlabel("", fontsize=FS_EJE)
    ax.set_ylabel("Valor normalizado [0–1]", fontsize=FS_EJE)
    ax.tick_params(axis="x", rotation=30, labelsize=FS_TICK)
    ax.tick_params(axis="y", labelsize=FS_TICK)
    ax.legend(fontsize=FS_LEYENDA)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp02_boxplot_variables.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def exp03_correlacion_iml_ivs(df: pd.DataFrame) -> None:
    """EXP 03 — Correlación IML_MUNICIPAL vs IVS con acrónimos."""
    if "IML_MUNICIPAL" not in df.columns:
        print("  ⚠ IML_MUNICIPAL no disponible — exp03 omitida")
        return

    corr   = df["IML_MUNICIPAL"].corr(df["IVS"])
    colores = [COLORES_NIVELES.get(str(n), "#888") for n in df["NIVEL_IVS"]]

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(df["IML_MUNICIPAL"], df["IVS"], c=colores,
               s=110, edgecolors="white", linewidth=0.8, zorder=3)

    for _, row in df.iterrows():
        ax.annotate(row["ACR"],
                    (row["IML_MUNICIPAL"], row["IVS"]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=FS_ETIQUETA, color="#222222", fontweight="bold")

    m, b   = np.polyfit(df["IML_MUNICIPAL"], df["IVS"], 1)
    x_line = np.linspace(df["IML_MUNICIPAL"].min(),
                         df["IML_MUNICIPAL"].max(), 100)
    ax.plot(x_line, m * x_line + b, color="gray",
            linestyle="--", linewidth=1.1, label=f"r = {corr:.3f}")

    ax.set_xlabel("Índice de Marginación Municipal (CONAPO 2020)",
                  fontsize=FS_EJE)
    ax.set_ylabel("Índice de Vulnerabilidad Socioterritorial (IVS)",
                  fontsize=FS_EJE)
    ax.set_title(
        "Validación externa: IML CONAPO vs IVS calculado\n"
        "Municipios de Campeche, México",
        fontsize=FS_TITULO, pad=12)
    ax.tick_params(labelsize=FS_TICK)
    ax.legend(fontsize=FS_LEYENDA)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp03_correlacion_iml_ivs.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


def exp04_radar_municipios(df: pd.DataFrame) -> None:
    """
    EXP 04 — Radar invertido: 6 polígonos = 6 municipios seleccionados,
    colores = variables del índice.

    Se seleccionan los 3 municipios con mayor IVS y los 3 con menor IVS.
    Cada vértice del radar es un municipio y cada línea de color representa
    una variable normalizada, mostrando qué variable impulsa más la
    vulnerabilidad de cada municipio seleccionado.
    """
    # Seleccionar top 3 y bottom 3
    top3    = df.nlargest(3,  "IVS")
    bottom3 = df.nsmallest(3, "IVS")
    df_sel  = pd.concat([top3, bottom3]).reset_index(drop=True)

    cols_disp  = [c for c in VARS_NORM if c in df.columns]
    etiquetas  = [ETIQUETAS_VARS.get(c, c) for c in cols_disp]
    municipios = df_sel["ACR"].tolist()
    N_mun      = len(municipios)

    # Ángulos para cada municipio en el radar
    angulos  = [n / float(N_mun) * 2 * np.pi for n in range(N_mun)]
    angulos += angulos[:1]

    fig, ax = plt.subplots(figsize=(10, 10),
                            subplot_kw=dict(polar=True))

    # Una línea por variable, color por variable
    for i, (col, etiq) in enumerate(zip(cols_disp, etiquetas)):
        valores  = df_sel[col].tolist()
        valores += valores[:1]  # cerrar polígono
        ax.plot(angulos, valores, "o-",
                linewidth=2.0, color=COLORES_VARS[i],
                label=etiq, markersize=6)
        ax.fill(angulos, valores, alpha=0.06, color=COLORES_VARS[i])

    # Etiquetas de municipios en los vértices
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(municipios, size=FS_ETIQUETA + 2, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"],
                       size=FS_TICK)
    ax.set_title(
        "Perfil de vulnerabilidad por variable\n"
        "Top 3 vs Bottom 3 — Municipios de Campeche",
        pad=22, fontsize=FS_TITULO)

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.45, 1.15),
        fontsize=FS_LEYENDA,
        title="Variable del índice",
        title_fontsize=FS_LEYENDA,
    )

    # Tabla de acrónimos y nota
    plt.tight_layout()
    ruta = DIR_FIGURAS / f"exp04_radar_municipios.{FORMATO_FIG}"
    plt.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
    plt.close()
    print(f"  Guardada: {ruta.name}")


# =============================================================================
# REPORTE TXT COMPLETO
# =============================================================================

def generar_reporte(df: pd.DataFrame) -> None:
    """Reporte TXT exhaustivo con todos los resultados calculados."""
    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta  = DIR_TABLAS / "reporte_completo_ivs.txt"
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
            f.write(f"\n{'-'*70}\n  {texto}\n{'-'*70}\n")

        titulo("REPORTE COMPLETO — ÍNDICE DE VULNERABILIDAD SOCIOTERRITORIAL")
        f.write(f"  Proyecto: Inundaciones Campeche, México\n")
        f.write(f"  Generado: {ahora}\n")
        f.write(f"  Autores:  Guillermo Adrián Chin Canché (ITESCAM)\n")
        f.write(f"            Javier Pan Barcel (UAC-EPOMEX)\n")
        f.write(f"            Katia Ruiz Canul (ITESCAM)\n")
        f.write(f"  Fuentes:  ITER Censo 2020 (INEGI) + IML 2020 (CONAPO)\n")
        linea()

        subtitulo("NOTA SOBRE DZITBALCHÉ")
        f.write(
            "  El municipio de Dzitbalché fue creado recientemente por\n"
            "  segregación del municipio de Calkiní. El Censo 2020 (INEGI)\n"
            "  y el IML 2020 (CONAPO) no lo registran como municipio\n"
            "  independiente, por lo que sus datos están incluidos en los\n"
            "  valores de Calkiní. Esta limitación debe señalarse en el\n"
            "  apartado correspondiente del artículo.\n"
        )

        subtitulo("TABLA DE ACRÓNIMOS")
        f.write(f"\n  {'Acrónimo':<10} {'Municipio'}\n")
        f.write(f"  {'-'*35}\n")
        for _, row in df.sort_values("IVS", ascending=False).iterrows():
            f.write(f"  {row['ACR']:<10} {row['NOM_MUN']}\n")

        subtitulo("1. PARÁMETROS DEL ANÁLISIS")
        f.write(f"  Entidad:       Campeche (clave 04)\n")
        f.write(f"  N municipios:  {len(df)}\n")
        f.write(f"  Método:        Promedio ponderado + normalización min-max\n")
        f.write(f"  Peso DIM_VS:   {PESOS_DIMENSIONES['VS']}\n")
        f.write(f"  Peso DIM_EF:   {PESOS_DIMENSIONES['EF']}\n")
        f.write(f"  Variables VS:  VS1-VS5 (5 variables)\n")
        f.write(f"  Variables EF:  EF1-EF3 (3 variables)\n")
        f.write(f"  Niveles IVS:   {' | '.join(NIVELES_INDICE)}\n")

        subtitulo("2. ESTADÍSTICAS DESCRIPTIVAS — VARIABLES NORMALIZADAS")
        f.write(f"\n  {'Variable':<12} {'Etiqueta':<22} {'Min':>7} "
                f"{'Max':>7} {'Media':>8} {'Mediana':>9} {'Desv.':>8}\n")
        f.write(f"  {'-'*78}\n")
        for col in cols_norm:
            etiq = ETIQUETAS_VARS.get(col, col)
            s    = df[col]
            f.write(f"  {col:<12} {etiq:<22} {s.min():>7.4f} {s.max():>7.4f} "
                    f"{s.mean():>8.4f} {s.median():>9.4f} {s.std():>8.4f}\n")

        subtitulo("3. VALORES NORMALIZADOS POR MUNICIPIO")
        encabezado = f"  {'ACR':<5} {'Municipio':<18} " + \
                     " ".join(f"{c:<10}" for c in cols_norm)
        f.write(encabezado + "\n")
        f.write(f"  {'-'*100}\n")
        for _, row in df.sort_values("IVS", ascending=False).iterrows():
            vals = " ".join(f"{row[c]:>10.4f}" if c in row.index
                            else f"{'N/D':>10}" for c in cols_norm)
            f.write(f"  {row['ACR']:<5} {row['NOM_MUN']:<18} {vals}\n")

        subtitulo("4. RANKING FINAL")
        f.write(f"\n  {'#':<4} {'ACR':<5} {'Municipio':<18} {'IVS':>8} "
                f"{'Nivel':<12} {'DIM_VS':>8} {'DIM_EF':>8}")
        if "IML_MUNICIPAL" in df.columns:
            f.write(f" {'IML':>9}")
        f.write("\n")
        f.write(f"  {'-'*85}\n")
        for _, row in df.sort_values("IVS", ascending=False).iterrows():
            f.write(
                f"  {int(row['RANKING']):<4} {row['ACR']:<5} "
                f"{row['NOM_MUN']:<18} {row['IVS']:>8.4f} "
                f"{str(row['NIVEL_IVS']):<12} {row['DIM_VS']:>8.4f} "
                f"{row['DIM_EF']:>8.4f}"
            )
            if "IML_MUNICIPAL" in df.columns:
                f.write(f" {row['IML_MUNICIPAL']:>9.4f}")
            f.write("\n")

        subtitulo("5. DISTRIBUCIÓN POR NIVEL")
        conteo = df["NIVEL_IVS"].value_counts()
        for nivel in NIVELES_INDICE:
            n   = conteo.get(nivel, 0)
            pct = n / len(df) * 100
            f.write(f"  {nivel:<12} {'█'*n:<15} {n} mun. ({pct:.1f}%)\n")

        subtitulo("6. CORRELACIONES ENTRE VARIABLES NORMALIZADAS")
        if len(cols_norm) > 1:
            corr_mat = df[cols_norm].rename(
                columns={c: ETIQUETAS_VARS.get(c, c) for c in cols_norm}
            ).corr().round(3)
            f.write("\n" + corr_mat.to_string() + "\n")

        if "IML_MUNICIPAL" in df.columns:
            subtitulo("7. VALIDACIÓN EXTERNA — IML vs IVS")
            corr_val = df["IML_MUNICIPAL"].corr(df["IVS"])
            corr_vs  = df["IML_MUNICIPAL"].corr(df["DIM_VS"])
            corr_ef  = df["IML_MUNICIPAL"].corr(df["DIM_EF"])
            interp   = ("Muy alta" if abs(corr_val) >= 0.8 else
                        "Alta"     if abs(corr_val) >= 0.6 else
                        "Moderada" if abs(corr_val) >= 0.4 else "Baja")
            f.write(f"  Pearson IML vs IVS:    r = {corr_val:.4f}\n")
            f.write(f"  Pearson IML vs DIM_VS: r = {corr_vs:.4f}\n")
            f.write(f"  Pearson IML vs DIM_EF: r = {corr_ef:.4f}\n")
            f.write(f"  Interpretación:        Correlación {interp}\n")
            f.write(f"  Nota: Con N=12 interpretar con cautela.\n")

        subtitulo("8. NOTAS METODOLÓGICAS")
        f.write(
            "  - Normalización min-max por variable, rango [0,1].\n"
            "  - DIM_VS = promedio simple NORM_VS1 a NORM_VS5.\n"
            "  - DIM_EF = promedio simple NORM_EF1 a NORM_EF3.\n"
            "  - IVS = DIM_VS × 0.6 + DIM_EF × 0.4.\n"
            "  - Clasificación: quintiles del IVS.\n"
            "  - Outliers conservados (N=12).\n"
            "  - Marco de referencia: Marco de Sendai 2015-2030.\n"
        )

        linea()
        f.write(f"  Fin del reporte — {ahora}\n")
        linea()

    print(f"  Reporte TXT guardado: {ruta.name}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SCRIPT 06 — Visualizaciones y reporte completo")
    print("=" * 60)

    for d in [DIR_FIGURAS, DIR_MAPAS, DIR_TABLAS]:
        d.mkdir(parents=True, exist_ok=True)

    df = cargar_indice(DATOS_INDICE)

    print("\n  [Figuras de publicación]")
    fig01_ranking_ivs(df)
    fig02_dimensiones_barras(df)
    fig03_heatmap_variables(df)
    fig04_mapa_cloropletico(df)

    print("\n  [Figuras exploratorias]")
    exp01_dispersion_vs_ef(df)
    exp02_boxplot_variables(df)
    exp03_correlacion_iml_ivs(df)
    exp04_radar_municipios(df)

    print("\n  [Reporte completo]")
    generar_reporte(df)

    print("\n✓ Script 06 completado exitosamente")
    print(f"  Figuras en:  {DIR_FIGURAS}")
    print(f"  Mapa en:     {DIR_MAPAS}")
    print(f"  Reporte en:  {DIR_TABLAS}\n")


if __name__ == "__main__":
    main()