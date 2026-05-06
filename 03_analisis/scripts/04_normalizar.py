# =============================================================================
# 04_normalizar.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Aplica normalización min-max a cada variable del índice para llevarlas
#   a una escala común [0, 1] donde 0 = menor vulnerabilidad y
#   1 = mayor vulnerabilidad. Exporta la tabla normalizada lista para
#   el cálculo de dimensiones e índice compuesto.
#
#   Entrada:  02_datos_procesados/campeche_municipios_merged.csv
#   Salida:   02_datos_procesados/campeche_municipios_merged.csv (actualizado)
#             (agrega columnas NORM_* al mismo archivo)
# =============================================================================

import sys
import pandas as pd
import numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[0]))
from config import (
    DATOS_MERGED,
    VARIABLES_INDICE,
)

# ── Mapeo de variables del índice a sus columnas de proporción ────────────────
# Después del script 03 las variables absolutas → PROP_*
# Las variables de CA se invierten: NORM = 1 - minmax(PROP)
VARS_NORMALIZACION = {
    # SS — Sensibilidad Social
    "SS1": {"prop": "PROP_P15YM_AN",   "inv": False},
    "SS2": {"prop": "PROP_VPH_AGUAFV", "inv": False},
    "SS3": {"prop": "PROP_VPH_NODREN", "inv": False},
    "SS4": {"prop": "PROP_VPH_PISODT", "inv": False},
    "SS5": {"prop": "PROP_PSINDER",    "inv": False},
    # EF — Exposición Física
    "EF1": {"prop": "POBTOT",          "inv": False},
    "EF2": {"prop": "PROP_VPH_C_ELEC", "inv": False},
    "EF3": {"prop": "PROP_VPH_SNBIEN", "inv": False},
    # CA — Capacidad Adaptativa (inversas)
    "CA1": {"prop": "PROP_GRAPROES",   "inv": True},
    "CA2": {"prop": "PROP_P18YM_PB",   "inv": True},
    "CA3": {"prop": "PROP_PDER_IMSS",  "inv": True},
    "CA4": {"prop": "PROP_POCUPADA",   "inv": True},
    # GV — Grupos Vulnerables
    "GV1": {"prop": "PROP_P60YMAS",    "inv": False},
    "GV2": {"prop": "PROP_POB0_14",    "inv": False},
    "GV3": {"prop": "PROP_P3YM_HLI",   "inv": False},
    "GV4": {"prop": "PROP_PCON_DISC",  "inv": False},
}


def cargar_merged(ruta) -> pd.DataFrame:
    """
    Carga la tabla integrada generada por el script 03.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"Archivo no encontrado: {ruta}\n"
            f"Ejecuta el script 03 primero."
        )
    df = pd.read_csv(ruta, dtype={"CVE_MUN": str, "MUN": str})
    print(f"  Tabla cargada: {len(df)} municipios, {len(df.columns)} columnas")
    return df


def normalizar_minmax(serie: pd.Series) -> pd.Series:
    """
    Aplica normalización min-max a una Serie de pandas.

    Fórmula:
        x_norm = (x - x_min) / (x_max - x_min)

    Resultado en [0, 1]:
        0 = municipio con MENOR valor (menor vulnerabilidad en esa variable)
        1 = municipio con MAYOR valor (mayor vulnerabilidad en esa variable)

    Si todos los valores son iguales (rango = 0) devuelve 0.5 para todos.
    Esto evita división por cero y es metodológicamente neutral.
    """
    x_min = serie.min()
    x_max = serie.max()
    rango  = x_max - x_min

    if rango == 0:
        return pd.Series(0.5, index=serie.index)

    return (serie - x_min) / rango


def aplicar_normalizacion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica normalización min-max a cada variable.
    Las variables inversas se normalizan como: NORM = 1 - minmax(PROP)
    Mayor NORM siempre = mayor vulnerabilidad.
    """
    print(f"\n  {'Variable':<8} {'Prop':<22} {'Inv':>5} "
          f"{'Min':>8} {'Max':>8} {'MediaNorm':>10}")
    print("  " + "-" * 68)

    for clave, meta in VARS_NORMALIZACION.items():
        col_origen = meta["prop"]
        inversa    = meta["inv"]

        if col_origen not in df.columns:
            print(f"  ⚠ {clave:<8} {col_origen:<22} — columna no encontrada")
            continue

        col_norm = f"NORM_{clave}"
        serie    = df[col_origen].copy()

        # Normalización min-max base
        norm = normalizar_minmax(serie)

        # Invertir si es variable de capacidad adaptativa
        if inversa:
            norm = 1 - norm

        df[col_norm] = norm

        print(
            f"  {clave:<8} {col_origen:<22} {'Sí' if inversa else 'No':>5} "
            f"{serie.min():>8.4f} {serie.max():>8.4f} "
            f"{df[col_norm].mean():>10.4f}"
        )

    return df


def verificar_normalizacion(df: pd.DataFrame) -> None:
    """
    Verifica que todas las columnas normalizadas estén en [0, 1].
    Reporta cualquier valor fuera de rango.
    """
    cols_norm = [c for c in df.columns if c.startswith("NORM_")]
    print(f"\n  Verificación de rango [0,1] en {len(cols_norm)} variables:")

    errores = 0
    for col in cols_norm:
        fuera = df[(df[col] < 0) | (df[col] > 1)]
        if not fuera.empty:
            print(f"  ⚠ {col}: valores fuera de rango en "
                  f"{list(fuera['NOM_MUN'])}")
            errores += 1

    if errores == 0:
        print("  Todas las variables normalizadas en [0,1] ✓")


def tabla_resumen(df: pd.DataFrame) -> None:
    """
    Imprime una tabla resumen con los valores normalizados
    por municipio — útil para revisión rápida del equipo.
    """
    cols_norm = [c for c in df.columns if c.startswith("NORM_")]
    cols_vista = ["NOM_MUN"] + cols_norm
    print(f"\n  Tabla de valores normalizados por municipio:")
    print(df[cols_vista].round(3).to_string(index=False))


def exportar(df: pd.DataFrame, ruta_salida) -> None:
    """
    Sobreescribe el archivo merged con las columnas NORM_* agregadas.
    """
    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    cols_norm = [c for c in df.columns if c.startswith("NORM_")]
    print(f"\n  Exportado: {ruta_salida.name} "
          f"(+{len(cols_norm)} columnas NORM_*)")


def main():
    print("=" * 60)
    print("SCRIPT 04 — Normalización min-max de variables del índice")
    print("=" * 60)

    # 1. Cargar tabla integrada
    df = cargar_merged(DATOS_MERGED)

    # 2. Aplicar normalización
    df = aplicar_normalizacion(df)

    # 3. Verificar rango
    verificar_normalizacion(df)

    # 4. Tabla resumen
    tabla_resumen(df)

    # 5. Exportar (actualiza el mismo archivo merged)
    exportar(df, DATOS_MERGED)

    print("\n✓ Script 04 completado exitosamente\n")


if __name__ == "__main__":
    main()