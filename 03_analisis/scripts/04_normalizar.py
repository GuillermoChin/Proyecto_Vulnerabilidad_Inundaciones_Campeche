# =============================================================================
# 04_normalizar.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
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
# Después del script 03, las variables absolutas se convirtieron en PROP_*
# POBTOT es la excepción: se usará directamente como densidad relativa
VARS_NORMALIZACION = {
    "VS1": "PROP_P15YM_AN",
    "VS2": "PROP_VPH_AGUAFV",
    "VS3": "PROP_VPH_NODREN",
    "VS4": "PROP_VPH_PISODT",
    "VS5": "PROP_PSINDER",
    "EF1": "POBTOT",          # Se normaliza directamente (densidad relativa)
    "EF2": "PROP_VPH_C_ELEC",
    "EF3": "PROP_PLOCRUG",
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
    Aplica normalización min-max a cada variable del índice.
    Crea columnas nuevas con prefijo NORM_ para cada variable.
    Reporta estadísticas básicas de cada variable normalizada.
    """
    print("\n  Normalización min-max por variable:")
    print(f"  {'Variable':<10} {'Col. origen':<22} {'Min orig':>9} "
          f"{'Max orig':>9} {'Media norm':>10}")
    print("  " + "-" * 65)

    for clave, col_origen in VARS_NORMALIZACION.items():
        if col_origen not in df.columns:
            print(f"  ⚠ Columna '{col_origen}' no encontrada — se omite {clave}")
            continue

        col_norm = f"NORM_{clave}"
        df[col_norm] = normalizar_minmax(df[col_origen])

        # Reporte por variable
        print(
            f"  {clave:<10} {col_origen:<22} "
            f"{df[col_origen].min():>9.4f} "
            f"{df[col_origen].max():>9.4f} "
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