# =============================================================================
# 01_cargar_iter.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Carga el archivo ITER del Censo de Población y Vivienda 2020 (INEGI)
#   para el estado de Campeche. Filtra únicamente las filas de resumen
#   municipal (MUN != 000, LOC == 0000), selecciona las columnas relevantes
#   para el índice y exporta el resultado a 02_datos_procesados/.
#
#   Entrada:  01_datos_crudos/iter_04_cpv2020_csv/.../conjunto_de_datos_iter_04CSV20.csv
#   Salida:   02_datos_procesados/iter_municipal_limpio.csv
# =============================================================================

import sys
import pandas as pd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[0]))
from config import (
    ITER_CSV,
    ITER_LIMPIO,
    CLAVE_ENTIDAD,
    VARIABLES_INDICE,
)

# ── Columnas base que siempre necesitamos ─────────────────────────────────────
COLS_BASE = [
    "ENTIDAD",   # Clave de entidad federativa
    "MUN",       # Clave de municipio
    "LOC",       # Clave de localidad (0000 = total municipal)
    "NOM_MUN",   # Nombre del municipio
    "POBTOT",    # Población total
    "TVIVHAB",   # Total de viviendas habitadas
]

# Columnas de variables del índice (extraídas del diccionario en config.py)
COLS_INDICE = list(VARIABLES_INDICE.values())

# Todas las columnas que necesitamos leer
COLS_NECESARIAS = COLS_BASE + [c for c in COLS_INDICE if c not in COLS_BASE]


def cargar_iter(ruta_csv: str) -> pd.DataFrame:
    """
    Carga el CSV del ITER Censo 2020 y lo devuelve como DataFrame completo.
    Se especifica encoding latin-1 porque los archivos INEGI usan ese encoding.
    """
    print(f"  Cargando ITER desde: {ruta_csv.name}")
    df = pd.read_csv(
        ruta_csv,
        encoding="latin-1",
        encoding_errors="replace",
        dtype=str,          # Todo como string para evitar pérdida de ceros
        low_memory=False,
    )
    df.columns = [c.replace("ï»¿", "").strip() for c in df.columns]
    print(f"  Filas cargadas: {len(df):,} | Columnas: {len(df.columns)}")
    return df


def filtrar_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra únicamente las filas de resumen municipal:
      - MUN distinto de '000' (no es total estatal)
      - LOC igual a '0000'    (es total del municipio, no localidad específica)
    """
    mascara = (df["MUN"] != "000") & (df["LOC"].isin(["0000", "000"]))
    # Excluir la fila de total estatal (NOM_MUN vacío o igual al estado)
    mascara = mascara & (df["MUN"].str.strip() != "000")
    df_mun = df[mascara].copy()
    print(f"  Municipios encontrados: {len(df_mun)}")
    return df_mun


def seleccionar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selecciona únicamente las columnas necesarias para el índice.
    Verifica que todas existan antes de seleccionar.
    """
    faltantes = [c for c in COLS_NECESARIAS if c not in df.columns]
    if faltantes:
        print(f"  ⚠ Columnas no encontradas en el ITER: {faltantes}")
        print("    Verifica el diccionario de datos y ajusta config.py")
        # Filtramos solo las que sí existen para no detener el flujo
        cols_disponibles = [c for c in COLS_NECESARIAS if c in df.columns]
    else:
        cols_disponibles = COLS_NECESARIAS

    df_sel = df[cols_disponibles].copy()
    print(f"  Columnas seleccionadas: {len(df_sel.columns)}")
    return df_sel


def convertir_numericas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte las columnas de variables a numérico.
    Los valores '*' o 'N/D' del INEGI se convierten a NaN.
    """
    cols_num = [c for c in COLS_INDICE if c in df.columns]
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # También POBTOT y TVIVHAB son numéricas
    for col in ["POBTOT", "TVIVHAB"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    nulos = df[cols_num].isnull().sum()
    if nulos.any():
        print(f"  Valores nulos por columna:\n{nulos[nulos > 0]}")
    else:
        print("  Sin valores nulos en columnas numéricas ✓")

    return df


def exportar(df: pd.DataFrame, ruta_salida) -> None:
    """
    Exporta el DataFrame limpio a CSV en 02_datos_procesados/.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"  Exportado: {ruta_salida.name} ({len(df)} filas)")


def main():
    print("=" * 60)
    print("SCRIPT 01 — Carga y filtrado del ITER Censo 2020")
    print("=" * 60)

    # 1. Cargar
    df_raw = cargar_iter(ITER_CSV)

    # 2. Filtrar municipios
    df_mun = filtrar_municipios(df_raw)

    # 3. Seleccionar columnas
    df_sel = seleccionar_columnas(df_mun)

    # 4. Convertir a numérico
    df_num = convertir_numericas(df_sel)

    # 5. Vista previa
    print("\n  Vista previa (primeras 3 filas):")
    print(df_num[["NOM_MUN", "POBTOT"] + COLS_INDICE[:3]].to_string(index=False))

    # 6. Exportar
    exportar(df_num, ITER_LIMPIO)

    print("\n✓ Script 01 completado exitosamente\n")


if __name__ == "__main__":
    main()