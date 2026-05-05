# =============================================================================
# 03_limpiar_datos.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Une las tablas limpias del ITER (script 01) y del IML (script 02)
#   mediante la clave municipal. Verifica consistencia, detecta valores
#   atípicos y exporta la tabla final integrada lista para el cálculo
#   del índice.
#
#   Entrada:  02_datos_procesados/iter_municipal_limpio.csv
#             02_datos_procesados/iml_campeche_municipal.csv
#   Salida:   02_datos_procesados/campeche_municipios_merged.csv
# =============================================================================

import sys
import pandas as pd
import numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[0]))
from config import (
    ITER_LIMPIO,
    IML_LIMPIO,
    DATOS_MERGED,
    NUM_MUNICIPIOS,
    VARIABLES_INDICE,
)


def cargar_procesados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carga los archivos ya procesados por los scripts 01 y 02.
    Verifica que existan antes de continuar.
    """
    for ruta in [ITER_LIMPIO, IML_LIMPIO]:
        if not ruta.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: {ruta}\n"
                f"Asegúrate de ejecutar los scripts 01 y 02 primero."
            )

    df_iter = pd.read_csv(ITER_LIMPIO, dtype={"MUN": str, "ENTIDAD": str})
    df_iml  = pd.read_csv(IML_LIMPIO,  dtype={"CVE_MUN": str})

    print(f"  ITER cargado:  {len(df_iter)} municipios")
    print(f"  IML cargado:   {len(df_iml)} municipios")
    return df_iter, df_iml


def estandarizar_claves(df_iter: pd.DataFrame,
                        df_iml: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Asegura que ambas tablas tengan una clave municipal de 3 dígitos
    con ceros a la izquierda (ej: '001', '011') para que el merge funcione.
    """
    df_iter["CVE_MUN"] = df_iter["MUN"].str.zfill(3)
    df_iml["CVE_MUN"]  = df_iml["MUN"].str.zfill(3)
    print("  Claves municipales estandarizadas ✓")
    return df_iter, df_iml


def merge_fuentes(df_iter: pd.DataFrame,
                  df_iml: pd.DataFrame) -> pd.DataFrame:
    """
    Une ambas tablas por clave municipal (inner join).
    Reporta municipios que no matcheen en alguna de las dos fuentes.
    """
    df = df_iter.merge(
        df_iml[["CVE_MUN", "IML_MUNICIPAL", "GM_MUNICIPAL"]],
        on="CVE_MUN",
        how="inner",
        validate="1:1",     # Garantiza que no haya duplicados por clave
    )

    if len(df) != NUM_MUNICIPIOS:
        print(f"  ⚠ Se esperaban {NUM_MUNICIPIOS} municipios, "
              f"se obtuvieron {len(df)} después del merge.")
        # Detectar cuáles no coincidieron
        solo_iter = set(df_iter["CVE_MUN"]) - set(df_iml["CVE_MUN"])
        solo_iml  = set(df_iml["CVE_MUN"])  - set(df_iter["CVE_MUN"])
        if solo_iter:
            print(f"    Claves solo en ITER (sin IML): {solo_iter}")
        if solo_iml:
            print(f"    Claves solo en IML (sin ITER): {solo_iml}")
    else:
        print(f"  Merge exitoso: {len(df)} municipios ✓")

    return df


def calcular_proporciones(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte los conteos absolutos del ITER en proporciones (0-1)
    dividiendo entre el total correspondiente (POBTOT o TVIVHAB).
    Esto es necesario para comparar municipios de diferente tamaño.

    Variables de población → dividir entre POBTOT
    Variables de vivienda  → dividir entre TVIVHAB
    """
    VARS_POBLACION = ["P15YM_AN", "PSINDER", "PLOCRUG"]
    VARS_VIVIENDA  = ["VPH_AGUAFV", "VPH_NODREN", "VPH_PISODT", "VPH_C_ELEC"]

    for col in VARS_POBLACION:
        if col in df.columns and "POBTOT" in df.columns:
            nueva_col = f"PROP_{col}"
            df[nueva_col] = df[col] / df["POBTOT"]
            df[nueva_col] = df[nueva_col].clip(0, 1)   # Acotar entre 0 y 1
            print(f"  Proporción calculada: {nueva_col}")

    for col in VARS_VIVIENDA:
        if col in df.columns and "TVIVHAB" in df.columns:
            nueva_col = f"PROP_{col}"
            df[nueva_col] = df[col] / df["TVIVHAB"]
            df[nueva_col] = df[nueva_col].clip(0, 1)
            print(f"  Proporción calculada: {nueva_col}")

    # POBTOT se convierte en densidad más adelante (requiere shapefile)
    # Por ahora se mantiene como valor absoluto

    return df


def detectar_outliers(df: pd.DataFrame) -> None:
    """
    Detecta valores potencialmente atípicos usando el rango intercuartílico
    (IQR). Con N=13 no se eliminan, solo se reportan para revisión manual.
    """
    print("\n  Detección de valores atípicos (IQR):")
    cols_prop = [c for c in df.columns if c.startswith("PROP_")]

    for col in cols_prop:
        Q1  = df[col].quantile(0.25)
        Q3  = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lim_inf = Q1 - 1.5 * IQR
        lim_sup = Q3 + 1.5 * IQR
        atipicos = df[(df[col] < lim_inf) | (df[col] > lim_sup)]["NOM_MUN"]
        if not atipicos.empty:
            print(f"    {col}: posibles atípicos → {list(atipicos)}")

    print("  (Con N=13 los atípicos se conservan — revisar en la discusión)")


def reporte_nulos(df: pd.DataFrame) -> None:
    """
    Imprime un reporte de valores nulos en la tabla integrada.
    """
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    if nulos.empty:
        print("  Sin valores nulos en la tabla integrada ✓")
    else:
        print(f"  ⚠ Valores nulos detectados:\n{nulos}")


def exportar(df: pd.DataFrame, ruta_salida) -> None:
    """
    Exporta la tabla integrada y limpia a CSV.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"\n  Exportado: {ruta_salida.name} ({len(df)} filas, "
          f"{len(df.columns)} columnas)")


def main():
    print("=" * 60)
    print("SCRIPT 03 — Limpieza, merge e integración de fuentes")
    print("=" * 60)

    # 1. Cargar archivos procesados
    df_iter, df_iml = cargar_procesados()

    # 2. Estandarizar claves municipales
    df_iter, df_iml = estandarizar_claves(df_iter, df_iml)

    # 3. Merge por clave municipal
    df = merge_fuentes(df_iter, df_iml)

    # 4. Calcular proporciones
    df = calcular_proporciones(df)

    # 5. Reporte de nulos
    reporte_nulos(df)

    # 6. Detección de outliers
    detectar_outliers(df)

    # 7. Vista previa
    cols_vista = ["NOM_MUN", "POBTOT", "IML_MUNICIPAL", "GM_MUNICIPAL"]
    print(f"\n  Vista previa:\n{df[cols_vista].to_string(index=False)}")

    # 8. Exportar
    exportar(df, DATOS_MERGED)

    print("\n✓ Script 03 completado exitosamente\n")


if __name__ == "__main__":
    main()