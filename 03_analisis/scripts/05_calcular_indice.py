# =============================================================================
# 05_calcular_indice.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Calcula las dos dimensiones del índice (VS y EF) como promedios simples
#   de sus variables normalizadas, luego calcula el índice compuesto final
#   aplicando los pesos definidos en config.py. Clasifica cada municipio
#   en uno de 5 niveles de vulnerabilidad y genera el ranking final.
#
#   Entrada:  02_datos_procesados/campeche_municipios_merged.csv
#   Salida:   02_datos_procesados/campeche_indice_final.csv
# =============================================================================

import sys
import pandas as pd
import numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[0]))
from config import (
    DATOS_MERGED,
    DATOS_INDICE,
    PESOS_DIMENSIONES,
    NIVELES_INDICE,
    DIR_TABLAS,
)


# ── Variables normalizadas por dimensión ──────────────────────────────────────
VARS_SS = ["NORM_SS1", "NORM_SS2", "NORM_SS3", "NORM_SS4", "NORM_SS5"]
VARS_EF = ["NORM_EF1", "NORM_EF2", "NORM_EF3"]
VARS_CA = ["NORM_CA1", "NORM_CA2", "NORM_CA3", "NORM_CA4"]
VARS_GV = ["NORM_GV1", "NORM_GV2", "NORM_GV3", "NORM_GV4"]


def cargar_normalizado(ruta) -> pd.DataFrame:
    """
    Carga la tabla con variables normalizadas generada por el script 04.
    Verifica que las columnas NORM_* existan.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"Archivo no encontrado: {ruta}\n"
            f"Ejecuta los scripts 01 al 04 primero."
        )

    df = pd.read_csv(ruta, dtype={"CVE_MUN": str, "MUN": str})

    cols_norm = [c for c in df.columns if c.startswith("NORM_")]
    if not cols_norm:
        raise ValueError(
            "No se encontraron columnas NORM_* en el archivo.\n"
            "Asegúrate de ejecutar el script 04 antes de este."
        )

    print(f"  Tabla cargada: {len(df)} municipios")
    print(f"  Columnas normalizadas disponibles: {cols_norm}")
    return df


def calcular_dimensiones(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula las 4 dimensiones como promedios simples de sus variables.
    SS, EF, CA, GV → cada una en [0,1].
    """
    dimensiones = {
        "DIM_SS": VARS_SS,
        "DIM_EF": VARS_EF,
        "DIM_CA": VARS_CA,
        "DIM_GV": VARS_GV,
    }

    print(f"\n  {'Municipio':<30} "
          f"{'DIM_SS':>8} {'DIM_EF':>8} {'DIM_CA':>8} {'DIM_GV':>8}")
    print("  " + "-" * 66)

    for dim_col, vars_dim in dimensiones.items():
        vars_disp   = [v for v in vars_dim if v in df.columns]
        faltantes   = set(vars_dim) - set(vars_disp)
        if faltantes:
            print(f"  ⚠ {dim_col}: variables no disponibles: {faltantes}")
        df[dim_col] = df[vars_disp].mean(axis=1)
        print(f"  {dim_col} calculada con {len(vars_disp)} variables ✓")

    print()
    for _, row in df[["NOM_MUN","DIM_SS","DIM_EF",
                       "DIM_CA","DIM_GV"]].iterrows():
        print(
            f"  {row['NOM_MUN']:<30} "
            f"{row['DIM_SS']:>8.4f} {row['DIM_EF']:>8.4f} "
            f"{row['DIM_CA']:>8.4f} {row['DIM_GV']:>8.4f}"
        )
    return df


def calcular_indice_compuesto(df: pd.DataFrame) -> pd.DataFrame:
    """
    IVS = DIM_SS×0.30 + DIM_EF×0.25 + DIM_CA×0.25 + DIM_GV×0.20
    Justificación de pesos:
      SS=0.30 — Cutter et al. (2003) Social Vulnerability Index
      EF=0.25 — IPCC AR5 (2014) exposure component
      CA=0.25 — IPCC AR5 (2014) adaptive capacity component
      GV=0.20 — Wisner et al. (2004) At Risk framework
    """
    p = PESOS_DIMENSIONES
    df["IVS"] = (
        df["DIM_SS"] * p["SS"] +
        df["DIM_EF"] * p["EF"] +
        df["DIM_CA"] * p["CA"] +
        df["DIM_GV"] * p["GV"]
    )
    df["IVS"] = df["IVS"].round(4)

    print(f"\n  Índice IVS calculado:")
    print(f"    IVS = SS×{p['SS']} + EF×{p['EF']} + "
          f"CA×{p['CA']} + GV×{p['GV']}")
    print(f"    Rango: [{df['IVS'].min():.4f} — {df['IVS'].max():.4f}]")
    print(f"    Media: {df['IVS'].mean():.4f} | "
          f"Desv: {df['IVS'].std():.4f}")
    return df


def clasificar_niveles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica cada municipio en uno de 5 niveles de vulnerabilidad
    usando quintiles del IVS (distribución igual entre los 5 niveles).

    Con N=13 los quintiles pueden no ser perfectamente iguales,
    pero es el método más reproducible y transparente para este N.

    Niveles (de mayor a menor vulnerabilidad):
        Muy Alto | Alto | Medio | Bajo | Muy Bajo
    """
    # Quintiles: cortes en 0%, 20%, 40%, 60%, 80%, 100%
    quintiles = df["IVS"].quantile([0.0, 0.2, 0.4, 0.6, 0.8, 1.0]).values

    # Eliminar duplicados en los cortes (puede pasar con N=13)
    cortes = sorted(set(quintiles))

    # Si hay menos de 6 cortes únicos ajustamos con linspace
    if len(cortes) < 6:
        cortes = list(np.linspace(df["IVS"].min(), df["IVS"].max(), 6))

    df["NIVEL_IVS"] = pd.cut(
        df["IVS"],
        bins=cortes,
        labels=NIVELES_INDICE,
        include_lowest=True,
        ordered=True,
    )

    print(f"\n  Distribución por nivel de vulnerabilidad:")
    print(df["NIVEL_IVS"].value_counts().sort_index().to_string())

    return df


def generar_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ordena los municipios de mayor a menor vulnerabilidad (IVS descendente)
    y agrega columna de posición en el ranking.
    """
    df = df.sort_values("IVS", ascending=False).reset_index(drop=True)
    df["RANKING"] = df.index + 1

    print(f"\n  Ranking final de vulnerabilidad:")
    print(f"\n  {'#':<4} {'Municipio':<30} {'IVS':>7} {'Nivel':<12} "
            f"{'DIM_SS':>8} {'DIM_EF':>8} {'DIM_CA':>8} {'DIM_GV':>8}")
    print("  " + "-" * 90)
    for _, fila in df.iterrows():
        print(
            f"  {int(fila['RANKING']):<4} {fila['NOM_MUN']:<30} "
            f"{fila['IVS']:>7.4f} {str(fila['NIVEL_IVS']):<12} "
            f"{fila['DIM_SS']:>8.4f} {fila['DIM_EF']:>8.4f}"
        )

    return df


def exportar_tabla_articulo(df: pd.DataFrame) -> None:
    """
    Exporta una tabla simplificada con solo las columnas relevantes
    para incluir en el artículo (04_outputs/tablas/).
    """
    cols_articulo = [
                    "RANKING", "NOM_MUN", "DIM_SS", "DIM_EF",
                    "DIM_CA", "DIM_GV", "IVS", "NIVEL_IVS"
                    ]
    cols_disponibles = [c for c in cols_articulo if c in df.columns]
    df_art = df[cols_disponibles].copy()

    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta_tabla = DIR_TABLAS / "tabla_ranking_ivs.csv"
    df_art.to_csv(ruta_tabla, index=False, encoding="utf-8")
    print(f"\n  Tabla para artículo exportada: {ruta_tabla.name}")


def exportar(df: pd.DataFrame, ruta_salida) -> None:
    """
    Exporta la tabla completa con índice y ranking.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"  Exportado: {ruta_salida.name} ({len(df)} filas, "
          f"{len(df.columns)} columnas)")


def main():
    print("=" * 60)
    print("SCRIPT 05 — Cálculo del índice compuesto y ranking")
    print("=" * 60)

    # 1. Cargar tabla normalizada
    df = cargar_normalizado(DATOS_MERGED)

    # 2. Calcular dimensiones
    df = calcular_dimensiones(df)

    # 3. Calcular índice compuesto
    df = calcular_indice_compuesto(df)

    # 4. Clasificar en niveles
    df = clasificar_niveles(df)

    # 5. Generar ranking
    df = generar_ranking(df)

    # 6. Exportar tabla para artículo
    exportar_tabla_articulo(df)

    # 7. Exportar tabla completa
    exportar(df, DATOS_INDICE)

    print("\n✓ Script 05 completado exitosamente\n")


if __name__ == "__main__":
    main()