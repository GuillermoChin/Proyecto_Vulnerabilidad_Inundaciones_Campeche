# =============================================================================
# 02_cargar_iml.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Carga el archivo IML_2020.xls del Índice de Marginación por Localidad
#   (CONAPO 2020), filtra las localidades del estado de Campeche y agrega
#   los valores a nivel municipal mediante promedio ponderado por población.
#   Exporta una tabla con un valor de marginación por municipio.
#
#   Entrada:  01_datos_crudos/IML_2020/IML_2020.xls
#   Salida:   02_datos_procesados/iml_campeche_municipal.csv
# =============================================================================

import sys
import pandas as pd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[0]))
from config import (
    IML_XLS,
    IML_LIMPIO,
    CLAVE_ENTIDAD,
)


# ── Nombres de columnas esperados en el IML_2020.xls ─────────────────────────
# CONAPO usa estos nombres — si cambian en futuras versiones ajustar aquí
COL_ENTIDAD   = "CVE_ENT"     # Clave de entidad (2 dígitos, string)
COL_MUNICIPIO = "CVE_MUN"     # Clave de municipio (3 dígitos, string)
COL_NOM_MUN   = "NOM_MUN"     # Nombre del municipio
COL_POBLACION = "POB_TOT"     # Población total de la localidad
COL_IML       = "IM_2020"     # Índice de marginación de la localidad
COL_GRADO     = "GM_2020"     # Grado de marginación (Muy alto/Alto/Medio/Bajo/Muy bajo)


def cargar_iml(ruta_xls) -> pd.DataFrame:
    """
    Carga el archivo XLS del IML CONAPO 2020.
    El archivo es nacional (~130,000 localidades) así que tarda unos segundos.
    """
    print(f"  Cargando IML desde: {ruta_xls.name}")
    print("  (Archivo nacional ~130,000 filas, puede tardar unos segundos...)")
    # Intentar detectar automáticamente la fila del encabezado real
    # CONAPO 2020 típicamente tiene entre 5 y 8 filas de metadata
    for skiprows in range(0, 10):
        df_test = pd.read_excel(
            ruta_xls,
            sheet_name=0,
            dtype=str,
            header=skiprows,
            nrows=3,
        )
        if any("CVE" in str(c).upper() or "ENT" in str(c).upper()
            for c in df_test.columns):
                print(f"  Encabezado real encontrado en fila {skiprows}")
                df = pd.read_excel(
                ruta_xls,
                sheet_name=0,
                dtype=str,
                header=skiprows,
            )
                break
        else:
        # Si no encontró automáticamente, prueba la hoja 1
            print("  ⚠ Probando hoja 1 del archivo...")
        df = pd.read_excel(ruta_xls, sheet_name=1, dtype=str)
    print(f"  Filas cargadas: {len(df):,} | Columnas: {len(df.columns)}")
    print(f"  Columnas disponibles: {list(df.columns)}")
    return df


def filtrar_campeche(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra únicamente las localidades del estado de Campeche (CVE_ENT == '04').
    Verifica que la columna de entidad exista con el nombre esperado.
    """
    if COL_ENTIDAD not in df.columns:
        # Intento alternativo: buscar columna que contenga 'ENT'
        candidatas = [c for c in df.columns if "ENT" in c.upper()]
        if candidatas:
            print(f"  ⚠ Columna '{COL_ENTIDAD}' no encontrada.")
            print(f"    Usando columna alternativa: '{candidatas[0]}'")
            col_ent = candidatas[0]
        else:
            raise KeyError(
                f"No se encontró columna de entidad. "
                f"Columnas disponibles: {list(df.columns)}"
            )
    else:
        col_ent = COL_ENTIDAD

    df_camp = df[df[col_ent] == CLAVE_ENTIDAD].copy()
    print(f"  Localidades en Campeche: {len(df_camp):,}")
    return df_camp


def convertir_numericas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte población e índice de marginación a numérico.
    """
    for col in [COL_POBLACION, COL_IML]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    nulos_iml = df[COL_IML].isnull().sum() if COL_IML in df.columns else 0
    if nulos_iml > 0:
        print(f"  ⚠ Localidades sin valor de IML: {nulos_iml} (se excluirán del promedio)")
    return df


def agregar_municipal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega el IML de localidades a nivel municipal mediante promedio
    ponderado por población total de cada localidad.

    Fórmula:
        IML_municipal = Σ(IML_localidad × POB_localidad) / Σ(POB_localidad)

    También calcula el grado de marginación predominante por municipio
    (el grado más frecuente entre sus localidades).
    """
    # Verificar columnas necesarias
    for col in [COL_MUNICIPIO, COL_NOM_MUN, COL_POBLACION, COL_IML]:
        if col not in df.columns:
            print(f"  ⚠ Columna esperada no encontrada: '{col}'")
            print(f"    Ajusta las constantes COL_* en este script.")

    # Eliminar filas sin IML o sin población para el cálculo ponderado
    df_valido = df.dropna(subset=[COL_IML, COL_POBLACION]).copy()

    # Promedio ponderado por municipio
    def promedio_ponderado(grupo):
        pob   = grupo[COL_POBLACION]
        iml   = grupo[COL_IML]
        total = pob.sum()
        if total == 0:
            return iml.mean()
        return (iml * pob).sum() / total

    iml_mun = (
        df_valido
        .groupby([COL_MUNICIPIO, COL_NOM_MUN])
        .apply(promedio_ponderado)
        .reset_index()
        .rename(columns={0: "IML_MUNICIPAL"})
    )

    # Grado predominante (moda por municipio)
    if COL_GRADO in df.columns:
        grado_mun = (
            df.groupby(COL_MUNICIPIO)[COL_GRADO]
            .agg(lambda x: x.mode()[0] if not x.mode().empty else None)
            .reset_index()
            .rename(columns={COL_GRADO: "GM_MUNICIPAL"})
        )
        iml_mun = iml_mun.merge(grado_mun, on=COL_MUNICIPIO, how="left")

    # Redondear IML a 4 decimales
    iml_mun["IML_MUNICIPAL"] = iml_mun["IML_MUNICIPAL"].round(4)

    print(f"  Municipios con IML agregado: {len(iml_mun)}")
    return iml_mun


def exportar(df: pd.DataFrame, ruta_salida) -> None:
    """
    Exporta el DataFrame agregado a CSV en 02_datos_procesados/.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"  Exportado: {ruta_salida.name} ({len(df)} filas)")


def main():
    print("=" * 60)
    print("SCRIPT 02 — Carga y agregación del IML CONAPO 2020")
    print("=" * 60)

    # 1. Cargar archivo nacional
    df_raw = cargar_iml(IML_XLS)

    # 2. Filtrar Campeche
    df_camp = filtrar_campeche(df_raw)

    # 3. Convertir numéricas
    df_num = convertir_numericas(df_camp)

    # 4. Agregar a nivel municipal
    df_mun = agregar_municipal(df_num)

    # 5. Vista previa
    print("\n  Vista previa (todos los municipios):")
    print(df_mun.to_string(index=False))

    # 6. Exportar
    exportar(df_mun, IML_LIMPIO)

    print("\n✓ Script 02 completado exitosamente\n")


if __name__ == "__main__":
    main()